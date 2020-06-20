# SCP-079-USER - Invite and help other bots
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
#
# This file is part of SCP-079-USER.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from time import sleep

from pyrogram import Client

from .. import glovar
from .channel import share_data
from .decorators import threaded
from .etc import code, general_link, lang, thread
from .file import data_to_file, save
from .group import leave_group, save_admins
from .telegram import get_admins, get_group_info, send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


@threaded()
def backup_files(client: Client) -> bool:
    # Backup data files to BACKUP
    result = False

    try:
        for file in glovar.file_list:
            # Check
            if not eval(f"glovar.{file}"):
                continue

            # Share
            share_data(
                client=client,
                receivers=["BACKUP"],
                action="backup",
                action_type="data",
                data=file,
                file=f"data/{file}"
            )
            sleep(5)

        result = True
    except Exception as e:
        logger.warning(f"Backup error: {e}", exc_info=True)

    return result


def interval_hour_01(client: Client) -> bool:
    # Execute every hour
    result = False

    try:
        # Ignore groups
        group_list = {gid for gid in list(glovar.configs)
                      if not any(glovar.configs[gid].get(s) for s in ["sb", "sr", "sd"])}
        file = data_to_file(group_list)
        share_data(
            client=client,
            receivers=["CAPTCHA"],
            action="update",
            action_type="ignore",
            file=file
        )

        result = True
    except Exception as e:
        logger.warning(f"Interval hour 01 error: {e}", exc_info=True)

    return result


def interval_min_10(client: Client) -> bool:
    # Execute every 10 minutes
    result = False

    glovar.locks["message"].acquire()

    try:
        # Clear recorded users
        for gid in list(glovar.recorded_ids):
            glovar.recorded_ids[gid] = set()

        # Send /long to LONG
        thread(send_report_message, (10, client, glovar.captcha_group_id, "/long"))

        result = True
    except Exception as e:
        logger.warning(f"Interval min 10 error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def reset_data(client: Client) -> bool:
    # Reset user data every month
    try:
        glovar.bad_ids["users"] = set()
        save("bad_ids")

        glovar.except_ids["temp"] = {}
        save("except_ids")

        glovar.user_ids = {}
        save("user_ids")

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('reset'))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Reset data error: {e}", exc_info=True)

    return False


def update_admins(client: Client) -> bool:
    # Update admin list every day
    result = False

    glovar.locks["admin"].acquire()

    try:
        # Basic data
        group_list = list(glovar.admin_ids)

        # Check groups
        for gid in group_list:
            group_name, group_link = get_group_info(client, gid)
            admin_members = get_admins(client, gid)

            # Bot is not in the chat, leave automatically without approve
            if admin_members is False or any(admin.user.is_self for admin in admin_members) is False:
                leave_group(client, gid)
                share_data(
                    client=client,
                    receivers=["MANAGE"],
                    action="leave",
                    action_type="info",
                    data={
                        "group_id": gid,
                        "group_name": group_name,
                        "group_link": group_link
                    }
                )
                project_text = general_link(glovar.project_name, glovar.project_link)
                debug_text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                              f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                              f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                              f"{lang('status')}{lang('colon')}{code(lang('leave_auto'))}\n"
                              f"{lang('reason')}{lang('colon')}{code(lang('reason_leave'))}\n")
                thread(send_message, (client, glovar.debug_channel_id, debug_text))
                continue

            # Check the admin list
            if not (admin_members and any([admin.user.is_self for admin in admin_members])):
                continue

            # Save the admin list
            save_admins(gid, admin_members)

            # Ignore the group
            if gid in glovar.lack_group_ids:
                continue

            # Check the permissions
            if glovar.user_id not in glovar.admin_ids[gid]:
                reason = "user"
            elif any(admin.user.is_self
                     and ((admin.can_delete_messages and admin.can_restrict_members)
                          or admin.status == "creator")
                     for admin in admin_members):
                glovar.lack_group_ids.discard(gid)
                save("lack_group_ids")
                continue
            else:
                reason = "permissions"
                glovar.lack_group_ids.add(gid)
                save("lack_group_ids")

            # Send the leave request
            share_data(
                client=client,
                receivers=["MANAGE"],
                action="leave",
                action_type="request",
                data={
                    "group_id": gid,
                    "group_name": group_name,
                    "group_link": group_link,
                    "reason": reason
                }
            )
            reason = lang(f"reason_{reason}")
            project_link = general_link(glovar.project_name, glovar.project_link)
            debug_text = (f"{lang('project')}{lang('colon')}{project_link}\n"
                          f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                          f"{lang('group_id')}{lang('colon')}{code(gid)}\n"
                          f"{lang('status')}{lang('colon')}{code(reason)}\n")
            thread(send_message, (client, glovar.debug_channel_id, debug_text))

        result = True
    except Exception as e:
        logger.warning(f"Update admin error: {e}", exc_info=True)
    finally:
        glovar.locks["admin"].release()

    return result


def update_status(client: Client, the_type: str) -> bool:
    # Update running status to BACKUP
    result = False

    try:
        result = share_data(
            client=client,
            receivers=["BACKUP"],
            action="backup",
            action_type="status",
            data={
                "type": the_type,
                "backup": glovar.backup
            }
        )
    except Exception as e:
        logger.warning(f"Update status error: {e}", exc_info=True)

    return result

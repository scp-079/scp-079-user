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
import pickle
from collections import Counter
from copy import deepcopy
from json import loads
from typing import Any

from pyrogram import Client, Message
from pyrogram.api.types import ChannelAdminLogEventsFilter, ChannelAdminLogEventActionParticipantJoin

from .. import glovar
from .channel import get_debug_text, share_data
from .decorators import threaded
from .etc import code, crypt_str, general_link, get_int, get_text, lang, mention_id, thread
from .file import crypt_file, data_to_file, delete_file, get_new_path, get_downloaded_path, save
from .group import delete_messages_globally, delete_messages_from_users, get_config_text, leave_group
from .ids import init_group_id, init_user_id
from .telegram import delete_all_messages, get_admin_log, get_chat_member, promote_chat_member, send_message
from .telegram import send_report_message
from .timers import update_admins
from .user import ban_user_globally, kick_users, unban_user_globally

# Enable logging
logger = logging.getLogger(__name__)


def receive_add_bad(sender: str, data: dict) -> bool:
    # Receive bad users or channels that other bots shared
    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Receive bad channel
        if sender == "MANAGE" and the_type == "channel":
            glovar.bad_ids["channels"].add(the_id)

        # Receive bad user
        if the_type == "user":
            glovar.bad_ids["users"].add(the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add bad error: {e}", exc_info=True)

    return False


def receive_add_except(data: dict) -> bool:
    # Receive a object and add it to except list
    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Receive except channel
        if the_type == "channel":
            glovar.except_ids["channels"].add(the_id)

        save("except_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add except error: {e}", exc_info=True)

    return False


def receive_clear_data(client: Client, data_type: str, data: dict) -> bool:
    # Receive clear data command
    glovar.locks["message"].acquire()
    try:
        # Basic data
        aid = data["admin_id"]
        the_type = data["type"]

        # Clear bad data
        if data_type == "bad":
            if the_type == "channels":
                glovar.bad_ids["channels"] = set()
            elif the_type == "users":
                glovar.bad_ids["users"] = set()

            save("bad_ids")

        # Clear except data
        if data_type == "except":
            if the_type == "channels":
                glovar.except_ids["channels"] = set()

            save("except_ids")

        # Clear user data
        if data_type == "user":
            if the_type == "all":
                glovar.user_ids = {}

            save("user_ids")

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('clear'))}\n"
                f"{lang('more')}{lang('colon')}{code(f'{data_type} {the_type}')}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Receive clear data: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def receive_config_commit(data: dict) -> bool:
    # Receive config commit
    try:
        # Basic data
        gid = data["group_id"]
        config = data["config"]

        glovar.configs[gid] = config
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Receive config commit error: {e}", exc_info=True)

    return False


def receive_config_reply(client: Client, data: dict) -> bool:
    # Receive config reply
    try:
        # Basic data
        gid = data["group_id"]
        uid = data["user_id"]
        link = data["config_link"]

        text = (f"{lang('admin')}{lang('colon')}{code(uid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('config_change'))}\n"
                f"{lang('description')}{lang('colon')}{general_link(lang('config_link'), link)}\n")
        thread(send_report_message, (180, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Receive config reply error: {e}", exc_info=True)

    return False


def receive_config_show(client: Client, data: dict) -> bool:
    # Receive config show request
    try:
        # Basic Data
        aid = data["admin_id"]
        mid = data["message_id"]
        gid = data["group_id"]

        # Generate report message's text
        result = (f"{lang('admin')}{lang('colon')}{mention_id(aid)}\n"
                  f"{lang('action')}{lang('colon')}{code(lang('config_show'))}\n"
                  f"{lang('group_id')}{lang('colon')}{code(gid)}\n")

        if glovar.configs.get(gid, {}):
            result += get_config_text(glovar.configs[gid])
        else:
            result += (f"{lang('status')}{lang('colon')}{code(lang('status_failed'))}\n"
                       f"{lang('reason')}{lang('colon')}{code(lang('reason_none'))}\n")

        # Send the text data
        file = data_to_file(result)
        share_data(
            client=client,
            receivers=["MANAGE"],
            action="config",
            action_type="show",
            data={
                "admin_id": aid,
                "message_id": mid,
                "group_id": gid
            },
            file=file
        )

        return True
    except Exception as e:
        logger.warning(f"Receive config show error: {e}", exc_info=True)

    return False


def receive_declared_message(data: dict) -> bool:
    # Update declared message's id
    try:
        # Basic data
        gid = data["group_id"]
        mid = data["message_id"]

        if not glovar.admin_ids.get(gid):
            return True

        if init_group_id(gid):
            glovar.declared_message_ids[gid].add(mid)

        return True
    except Exception as e:
        logger.warning(f"Receive declared message error: {e}", exc_info=True)

    return False


def receive_file_data(client: Client, message: Message, decrypt: bool = True) -> Any:
    # Receive file's data from exchange channel
    data = None
    try:
        if not message.document:
            return None

        file_id = message.document.file_id
        file_ref = message.document.file_ref
        path = get_downloaded_path(client, file_id, file_ref)

        if not path:
            return None

        if decrypt:
            # Decrypt the file, save to the tmp directory
            path_decrypted = get_new_path()
            crypt_file("decrypt", path, path_decrypted)
            path_final = path_decrypted
        else:
            # Read the file directly
            path_decrypted = ""
            path_final = path

        with open(path_final, "rb") as f:
            data = pickle.load(f)

        for f in {path, path_decrypted}:
            thread(delete_file, (f,))
    except Exception as e:
        logger.warning(f"Receive file error: {e}", exc_info=True)

    return data


def receive_flood_delete(client: Client, message: Message, data: int) -> bool:
    # Receive flood delete
    result = False

    try:
        # Basic data
        gid = data

        # Get the user list
        user_list = receive_file_data(client, message)

        if user_list is None:
            return False

        # Clear messages
        delete_messages_from_users(client, gid, user_list)

        result = True
    except Exception as e:
        logger.warning(f"Receive flood delete error: {e}", exc_info=True)

    return result


def receive_flood_score(client: Client, message: Message) -> bool:
    # Receive flood users' score
    result = False

    glovar.locks["message"].acquire()

    try:
        users = receive_file_data(client, message)

        if users is None:
            return False

        user_list = [uid for uid in list(users) if init_user_id(uid)]

        for uid in user_list:
            glovar.user_ids[uid]["score"]["captcha"] = users[uid]

        save("user_ids")
    except Exception as e:
        logger.warning(f"Receive flood score error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return result


def receive_help_ban(client: Client, data: dict) -> bool:
    # Receive help ban request
    glovar.locks["message"].acquire()
    try:
        # Basic data
        group_id = data["group_id"]
        user_id = data["user_id"]
        action_type = data["type"]
        should_delete = data["delete"]

        # Init user data
        if not init_user_id(user_id):
            return True

        # Save data
        glovar.user_ids[user_id][action_type].add(group_id)
        save("user_ids")

        # Delete all messages from the user
        if glovar.configs[group_id].get("delete") and should_delete:
            thread(delete_all_messages, (client, group_id, user_id))

        # Ban globally
        thread(ban_user_globally, (client, group_id, user_id))

        return True
    except Exception as e:
        logger.warning(f"Receive help ban error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def receive_help_confirm(client: Client, data: dict) -> bool:
    # Receive help confirm
    result = False

    try:
        # Basic data
        gid = data["group_id"]
        begin = data["begin"]
        end = data["end"]
        limit = data["limit"]

        # Check the group
        if glovar.admin_ids.get(gid) is None:
            return False

        # Get the recent actions
        event_filter = ChannelAdminLogEventsFilter(join=True, invite=True)
        log_list = get_admin_log(
            client=client,
            cid=gid,
            event_filter=event_filter
        )

        # Check the log list
        if not log_list:
            return share_data(
                client=client,
                receivers=["CAPTCHA"],
                action="help",
                action_type="confirm",
                data={
                    "group_id": gid,
                    "status": "end"
                }
            )

        # Get the user list
        user_list = {event.user_id if isinstance(event.action, ChannelAdminLogEventActionParticipantJoin)
                     else event.participant.user_id
                     for log in log_list for event in log.events if begin <= event.date <= end}

        # Check the user list
        if len(user_list) >= limit:
            status = "ongoing"
        else:
            status = "end"

        # Share the report
        result = share_data(
            client=client,
            receivers=["CAPTCHA"],
            action="help",
            action_type="confirm",
            data={
                "group_id": gid,
                "status": status
            }
        )
    except Exception as e:
        logger.warning(f"Receive help confirm error: {e}", exc_info=True)

    return result


def receive_help_delete(client: Client, data: dict) -> bool:
    # Receive help delete request
    glovar.locks["message"].acquire()
    try:
        # Basic data
        group_id = data["group_id"]
        user_id = data["user_id"]
        action_type = data["type"]
        should_delete = data["delete"]

        # Delete all messages from the user
        if action_type == "global":
            thread(delete_messages_globally, (client, user_id, int(not should_delete) and group_id))
        elif action_type == "single":
            if glovar.configs[group_id].get("delete") and should_delete:
                thread(delete_all_messages, (client, group_id, user_id))

        return True
    except Exception as e:
        logger.warning(f"Receive help delete error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@threaded()
def receive_help_kick(client: Client, message: Message, data: dict) -> bool:
    # Receive help kick
    result = False

    try:
        # Basic data
        gid = data["group_id"]
        manual = data["manual"]

        # Get the user list
        user_list = receive_file_data(client, message)

        if user_list is None:
            return False

        # Kick the user
        kick_users(client, gid, user_list)
        manual and logger.warning(f"Banned {user_list} in {gid}")
        delete_messages_from_users(client, gid, user_list)

        result = True
    except Exception as e:
        logger.warning(f"Receive help kick error: {e}", exc_info=True)

    return result


def receive_help_log(client: Client, data: dict) -> bool:
    # Receive check log request
    result = False

    try:
        # Basic data
        gid = data["group_id"]
        begin = data["begin"]
        end = data["end"]
        manual = data["manual"]

        # Check the group
        if glovar.admin_ids.get(gid) is None:
            return False

        # Get the recent actions
        event_filter = ChannelAdminLogEventsFilter(join=True, invite=True)
        log_list = get_admin_log(
            client=client,
            cid=gid,
            event_filter=event_filter
        )

        if not log_list:
            return False

        # Get the user list
        user_list = {event.user_id if isinstance(event.action, ChannelAdminLogEventActionParticipantJoin)
                     else event.participant.user_id
                     for log in log_list for event in log.events if begin <= event.date <= end}

        # Share the users
        file = data_to_file(user_list)
        result = share_data(
            client=client,
            receivers=["CAPTCHA"],
            action="help",
            action_type="log",
            data={
                "group_id": gid,
                "manual": manual
            },
            file=file
        )
    except Exception as e:
        logger.warning(f"Receive help log error: {e}", exc_info=True)

    return result


@threaded()
def receive_invite_try(client: Client, data: dict) -> bool:
    # Receive invite try
    result = False

    try:
        # Basic data
        aid = data["admin_id"]
        mid = data["message_id"]
        gid = data["group_id"]
        bots = data["bots"]

        # Check the group status
        if glovar.admin_ids.get(gid) is None:
            return share_data(
                client=client,
                receivers=["MANAGE"],
                action="invite",
                action_type="result",
                data={
                    "admin_id": aid,
                    "message_id": mid,
                    "group_id": gid,
                    "bots": bots,
                    "status": False,
                    "reason": lang("USER 尚未加入该群组")
                }
            )

        # Check USER's permissions
        chat_member = get_chat_member(client, gid, glovar.user_id)

        if (not chat_member
                or not chat_member.can_delete_messages
                or not chat_member.can_restrict_members
                or not chat_member.can_invite_users
                or not chat_member.can_pin_messages
                or not chat_member.can_promote_members):
            return share_data(
                client=client,
                receivers=["MANAGE"],
                action="invite",
                action_type="result",
                data={
                    "admin_id": aid,
                    "message_id": mid,
                    "group_id": gid,
                    "bots": bots,
                    "status": False,
                    "reason": lang("USER 权限缺失")
                }
            )

        # Promote bots
        for bot in bots:
            if bot == "AIO":
                bot_list = [glovar.captcha_id, glovar.clean_id, glovar.lang_id, glovar.long_id, glovar.noflood_id,
                            glovar.noporn_id, glovar.nospam_id, glovar.tip_id, glovar.warn_id]
                bot_count = Counter(bot_list)
                bot_id = bot_count.most_common()[0][0]
            else:
                bot_id = eval(f"glovar.{bot.lower()}_id")

            if not bot_id:
                continue

            if bot == "AIO":
                promote_chat_member(
                    client=client,
                    cid=gid,
                    uid=bot_id,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_invite_users=True,
                    can_pin_messages=True
                )
                break
            elif bot in {"CLEAN", "LANG", "LONG", "NOFLOOD", "NOPORN", "NOSPAM", "WARN"}:
                promote_chat_member(
                    client=client,
                    cid=gid,
                    uid=bot_id,
                    can_delete_messages=True,
                    can_restrict_members=True
                )
            elif bot == "CAPTCHA":
                promote_chat_member(
                    client=client,
                    cid=gid,
                    uid=bot_id,
                    can_delete_messages=True,
                    can_restrict_members=True,
                    can_pin_messages=True
                )
            elif bot == "TIP":
                promote_chat_member(
                    client=client,
                    cid=gid,
                    uid=bot_id,
                    can_delete_messages=True,
                    can_invite_users=True,
                    can_pin_messages=True
                )

        # Share data
        share_data(
            client=client,
            receivers=["MANAGE"],
            action="invite",
            action_type="result",
            data={
                    "admin_id": aid,
                    "message_id": mid,
                    "group_id": gid,
                    "bots": bots,
                    "status": True
            }
        )

        result = True
    except Exception as e:
        logger.warning(f"Receive invite try error: {e}", exc_info=True)

    return result


def receive_leave_approve(client: Client, data: dict) -> bool:
    # Receive leave approve
    try:
        # Basic data
        admin_id = data["admin_id"]
        the_id = data["group_id"]
        force = data["force"]
        reason = data["reason"]

        if reason in {"permissions", "user"}:
            reason = lang(f"reason_{reason}")

        if not glovar.admin_ids.get(the_id) and not force:
            return True

        text = get_debug_text(client, the_id)
        text += (f"{lang('admin_project')}{lang('colon')}{mention_id(admin_id)}\n"
                 f"{lang('status')}{lang('colon')}{code(lang('leave_approve'))}\n")

        if reason:
            text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        info_text = f"{lang('action')}{lang('colon')}{code(lang('leave_group'))}\n"

        if reason:
            info_text += f"{lang('reason')}{lang('colon')}{code(reason)}\n"

        send_message(client, the_id, info_text)

        leave_group(client, the_id)
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive leave approve error: {e}", exc_info=True)

    return False


def receive_refresh(client: Client, data: int) -> bool:
    # Receive refresh
    try:
        # Basic data
        aid = data

        # Update admins
        update_admins(client)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('refresh'))}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive refresh error: {e}", exc_info=True)

    return False


def receive_remove_bad(client: Client, sender: str, data: dict) -> bool:
    # Receive removed bad objects
    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Remove bad channel
        if sender == "MANAGE" and the_type == "channel":
            glovar.bad_ids["channels"].discard(the_id)

        # Remove bad user
        if the_type == "user":
            glovar.bad_ids["users"].discard(the_id)
            unban_user_globally(client, the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove bad error: {e}", exc_info=True)

    return False


def receive_remove_except(data: dict) -> bool:
    # Receive a object and remove it from except list
    try:
        # Basic data
        the_id = data["id"]
        the_type = data["type"]

        # Remove except channel
        if the_type == "channel":
            glovar.except_ids["channels"].discard(the_id)

        save("except_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove except error: {e}", exc_info=True)

    return False


def receive_remove_score(data: int) -> bool:
    # Receive remove user's score
    glovar.locks["message"].acquire()
    try:
        # Basic data
        uid = data

        if not glovar.user_ids.get(uid):
            return True

        glovar.user_ids[uid] = deepcopy(glovar.default_user_status)
        save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove score error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def receive_remove_watch(data: int) -> bool:
    # Receive removed watching users
    try:
        # Basic data
        uid = data

        # Reset watch status
        glovar.watch_ids["ban"].pop(uid, 0)
        glovar.watch_ids["delete"].pop(uid, 0)
        save("watch_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove watch error: {e}", exc_info=True)

    return False


def receive_rollback(client: Client, message: Message, data: dict) -> bool:
    # Receive rollback data
    try:
        # Basic data
        aid = data["admin_id"]
        the_type = data["type"]
        the_data = receive_file_data(client, message)

        if not the_data:
            return True

        exec(f"glovar.{the_type} = the_data")
        save(the_type)

        # Send debug message
        text = (f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"
                f"{lang('admin_project')}{lang('colon')}{mention_id(aid)}\n"
                f"{lang('action')}{lang('colon')}{code(lang('rollback'))}\n"
                f"{lang('more')}{lang('colon')}{code(the_type)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Receive rollback error: {e}", exc_info=True)

    return False


def receive_status_ask(client: Client, data: dict) -> bool:
    # Receive version info request
    glovar.locks["message"].acquire()
    try:
        # Basic data
        aid = data["admin_id"]
        mid = data["message_id"]

        group_count = len(glovar.admin_ids)

        status = {
            lang("group_count"): f"{group_count}"
        }
        file = data_to_file(status)
        share_data(
            client=client,
            receivers=["MANAGE"],
            action="status",
            action_type="reply",
            data={
                "admin_id": aid,
                "message_id": mid
            },
            file=file
        )

        return True
    except Exception as e:
        logger.warning(f"Receive version ask error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)

        if not text:
            return {}

        data = loads(text)
    except Exception as e:
        logger.warning(f"Receive text data error: {e}")

    return data


def receive_user_score(project: str, data: dict) -> bool:
    # Receive and update user's score
    glovar.locks["message"].acquire()
    try:
        # Basic data
        project = project.lower()
        uid = data["id"]

        if not init_user_id(uid):
            return True

        score = data["score"]
        glovar.user_ids[uid]["score"][project] = score
        save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive user score error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


def receive_watch_user(data: dict) -> bool:
    # Receive watch users that other bots shared
    try:
        # Basic data
        the_type = data["type"]
        uid = data["id"]
        until = data["until"]

        # Decrypt the data
        until = crypt_str("decrypt", until, glovar.key)
        until = get_int(until)

        # Add to list
        if the_type == "ban":
            glovar.watch_ids["ban"][uid] = until
        elif the_type == "delete":
            glovar.watch_ids["delete"][uid] = until
        else:
            return False

        save("watch_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive watch user error: {e}", exc_info=True)

    return False

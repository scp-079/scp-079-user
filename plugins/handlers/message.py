# SCP-079-USER - Invite and help other bots
# Copyright (C) 2019 SCP-079 <https://scp-079.org>
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
import re

from PIL import Image
from pyrogram import Client, Filters, Message, WebPage

from .. import glovar
from ..functions.channel import get_debug_text, share_data
from ..functions.etc import code, general_link, get_channel_link, get_stripped_link, lang, mention_id, thread
from ..functions.file import data_to_file, delete_file, get_downloaded_path, save
from ..functions.filters import authorized_group, captcha_group, class_c, class_d, class_e, declared_message
from ..functions.filters import exchange_channel, from_user, hide_channel, is_class_d_user, is_declared_message
from ..functions.filters import is_not_allowed, new_group, test_group
from ..functions.group import delete_message, leave_group
from ..functions.ids import init_group_id
from ..functions.receive import receive_add_bad, receive_add_except, receive_clear_data, receive_config_commit
from ..functions.receive import receive_config_reply, receive_config_show, receive_declared_message, receive_help_ban
from ..functions.receive import receive_help_delete, receive_leave_approve, receive_refresh, receive_remove_bad
from ..functions.receive import receive_remove_except, receive_rollback, receive_status_ask, receive_text_data
from ..functions.telegram import get_admins, read_history, read_mention
from ..functions.telegram import resolve_username, send_message
from ..functions.tests import preview_test
from ..functions.timers import backup_files
from ..functions.user import terminate_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~Filters.new_chat_members
                   & ~captcha_group & ~test_group & authorized_group
                   & from_user & ~class_c & class_d & ~class_e
                   & ~declared_message)
def check(client: Client, message: Message) -> bool:
    # Check messages from groups
    glovar.locks["message"].acquire()
    try:
        # Not allowed message
        detection = is_not_allowed(message)
        if is_not_allowed(message):
            terminate_user(client, message, message.from_user, detection)

        return True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members
                   & ~captcha_group & ~test_group & ~new_group & authorized_group
                   & from_user & ~class_c & ~class_e
                   & ~declared_message)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    glovar.locks["message"].acquire()
    try:
        for new in message.new_chat_members:
            # Check if the user is Class D personnel
            if not is_class_d_user(new):
                continue

            detection = is_not_allowed(message)
            if detection:
                terminate_user(client, message, new, detection)

        return True
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & Filters.service
                   & captcha_group & ~test_group
                   & from_user)
def delete_service(client: Client, message: Message) -> bool:
    # Delete service messages sent by SCP-079
    try:
        # Basic data
        gid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id

        # Check if the message is sent by SCP-079
        if uid in glovar.bot_ids:
            delete_message(client, gid, mid)

        return True
    except Exception as e:
        logger.warning(f"Delete service error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & hide_channel, group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]

        if "EMERGENCY" not in receivers:
            return True

        if action != "backup":
            return True

        if action_type != "hide":
            return True

        if data is True:
            glovar.should_hide = data
        elif data is False and sender == "MANAGE":
            glovar.should_hide = data

        project_text = general_link(glovar.project_name, glovar.project_link)
        hide_text = (lambda x: lang("enabled") if x else "disabled")(glovar.should_hide)
        text = (f"{lang('project')}{lang('colon')}{project_text}\n"
                f"{lang('action')}{lang('colon')}{code(lang('transfer_channel'))}\n"
                f"{lang('emergency_channel')}{lang('colon')}{code(hide_text)}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group
                   & (Filters.new_chat_members | Filters.group_chat_created | Filters.supergroup_chat_created)
                   & ~captcha_group & ~test_group & new_group
                   & from_user)
def init_group(client: Client, message: Message) -> bool:
    # Initiate new groups
    try:
        gid = message.chat.id
        text = get_debug_text(client, message.chat)
        invited_by = message.from_user.id

        # Check permission
        if invited_by == glovar.user_id:
            # Remove the left status
            if gid in glovar.left_group_ids:
                glovar.left_group_ids.discard(gid)
                save("left_group_ids")

            # Update group's admin list
            if not init_group_id(gid):
                return True

            admin_members = get_admins(client, gid)
            if admin_members:
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                         if not admin.user.is_bot and not admin.user.is_deleted}
                save("admin_ids")
                text += f"{lang('status')}{lang('colon')}{code(lang('status_joined'))}\n"
            else:
                thread(leave_group, (client, gid))
                text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                         f"{lang('reason')}{lang('colon')}{code(lang('reason_admin'))}\n")
        else:
            if gid in glovar.left_group_ids:
                return leave_group(client, gid)

            leave_group(client, gid)
            text += (f"{lang('status')}{lang('colon')}{code(lang('status_left'))}\n"
                     f"{lang('reason')}{lang('colon')}{code(lang('reason_unauthorized'))}\n")
            if message.from_user.username:
                text += f"{lang('inviter')}{lang('colon')}{mention_id(invited_by)}\n"
            else:
                text += f"{lang('inviter')}{lang('colon')}{code(invited_by)}\n"

        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & ~Filters.private & Filters.mentioned, group=1)
def mark_mention(client: Client, message: Message) -> bool:
    # Mark mention as read
    try:
        if not message.chat:
            return True

        cid = message.chat.id
        thread(read_mention, (client, cid))

        return True
    except Exception as e:
        logger.warning(f"Mark mention error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & ~Filters.private, group=2)
def mark_message(client: Client, message: Message) -> bool:
    # Mark messages from groups and channels as read
    try:
        if not message.chat:
            return True

        cid = message.chat.id
        thread(read_history, (client, cid))

        return True
    except Exception as e:
        logger.warning(f"Mark message error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & exchange_channel)
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    glovar.locks["receive"].acquire()
    try:
        data = receive_text_data(message)

        if not data:
            return True

        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]
        
        # This will look awkward,
        # seems like it can be simplified,
        # but this is to ensure that the permissions are clear,
        # so it is intentionally written like this
        if glovar.sender in receivers:

            if sender == "CAPTCHA":
                if action == "help":
                    if action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "CLEAN":
                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

                elif action == "help":
                    if action_type == "ban":
                        receive_help_ban(client, data)
                    elif action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "CONFIG":

                if action == "config":
                    if action_type == "commit":
                        receive_config_commit(data)
                    elif action_type == "reply":
                        receive_config_reply(client, data)

            elif sender == "LANG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

                elif action == "help":
                    if action_type == "ban":
                        receive_help_ban(client, data)
                    elif action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "LONG":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

                elif action == "help":
                    if action_type == "ban":
                        receive_help_ban(client, data)
                    elif action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "MANAGE":

                if action == "add":
                    if action == "add":
                        if action_type == "bad":
                            receive_add_bad(sender, data)
                        elif action_type == "except":
                            receive_add_except(data)

                elif action == "backup":
                    if action_type == "now":
                        thread(backup_files, (client,))
                    elif action_type == "rollback":
                        receive_rollback(client, message, data)

                elif action == "clear":
                    receive_clear_data(client, action_type, data)

                elif action == "config":
                    if action_type == "show":
                        receive_config_show(client, data)

                elif action == "leave":
                    if action_type == "approve":
                        receive_leave_approve(client, data)

                elif action == "remove":
                    if action_type == "bad":
                        receive_remove_bad(client, sender, data)
                    elif action_type == "except":
                        receive_remove_except(data)

                elif action == "status":
                    if action_type == "ask":
                        receive_status_ask(client, data)

                elif action == "update":
                    if action_type == "refresh":
                        receive_refresh(client, data)

            elif sender == "NOFLOOD":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

                elif action == "help":
                    if action_type == "ban":
                        receive_help_ban(client, data)
                    elif action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "NOPORN":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

                elif action == "help":
                    if action_type == "ban":
                        receive_help_ban(client, data)
                    elif action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "NOSPAM":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

                elif action == "help":
                    if action_type == "ban":
                        receive_help_ban(client, data)
                    elif action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "RECHECK":

                if action == "add":
                    if action_type == "bad":
                        receive_add_bad(sender, data)

                elif action == "help":
                    if action_type == "ban":
                        receive_help_ban(client, data)
                    elif action_type == "delete":
                        receive_help_delete(client, data)

                elif action == "update":
                    if action_type == "declare":
                        receive_declared_message(data)

            elif sender == "WARN":

                if action == "help":
                    if action_type == "delete":
                        receive_help_delete(client, data)

        return True
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)
    finally:
        glovar.locks["receive"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & ~Filters.service
                   & ~captcha_group & ~test_group & authorized_group
                   & from_user & ~class_c & ~class_d & ~class_e
                   & ~declared_message)
def share_preview(client: Client, message: Message) -> bool:
    # Share the message's preview with other bots
    glovar.locks["preview"].acquire()
    try:
        if not message.web_page:
            return True

        web_page: WebPage = message.web_page
        preview = {
            "url": None,
            "image": None,
            "text": None,
            "media": None
        }

        url = web_page.url
        if url in glovar.shared_url:
            return True

        # Bypass
        bypass = get_stripped_link(get_channel_link(message))
        if f"{bypass}/" in f"{url}/":
            return True

        link_username = re.match(r"t\.me/(.+?)/", f"{web_page.display_url}/")
        if link_username:
            link_username = link_username.group(1)
            _, pid = resolve_username(client, link_username)
            if pid in glovar.except_ids["channels"] or glovar.admin_ids.get(pid, {}):
                return True

        gid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id

        # Store image
        if web_page.photo and web_page.photo.file_size <= glovar.image_size:
            file_id = web_page.photo.file_id
            file_ref = web_page.photo.file_ref
            image_path = get_downloaded_path(client, file_id, file_ref)
            if is_declared_message(None, message):
                return True
            elif image_path:
                preview["image"] = Image.open(image_path)
                delete_file(image_path)

        # Store text
        text = ""

        text += message.text + "\n\n"

        text += web_page.display_url + "\n\n"

        if web_page.site_name:
            text += web_page.site_name + "\n\n"

        if web_page.title:
            text += web_page.title + "\n\n"

        if web_page.description:
            text += web_page.description + "\n\n"

        preview["text"] = text

        # Store url
        preview["url"] = url

        # Store media
        if (web_page.audio
                or web_page.document
                or web_page.animation
                or web_page.video):
            preview["media"] = True

        # Save and share
        file = data_to_file(preview)
        share_data(
            client=client,
            receivers=glovar.receivers["preview"],
            action="update",
            action_type="preview",
            data={
                "group_id": gid,
                "user_id": uid,
                "message_id": mid
            },
            file=file
        )
        glovar.shared_url.add(url)

        return True
    except Exception as e:
        logger.warning(f"Share preview error: {e}", exc_info=True)
    finally:
        glovar.locks["preview"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & ~Filters.bot & ~Filters.service
                   & ~Filters.command(glovar.all_commands, glovar.prefix)
                   & test_group
                   & from_user)
def test(client: Client, message: Message) -> bool:
    # Show test results in TEST group
    glovar.locks["test"].acquire()
    try:
        preview_test(client, message)

        return True
    except Exception as e:
        logger.warning(f"Test error: {e}", exc_info=True)
    finally:
        glovar.locks["test"].release()

    return False

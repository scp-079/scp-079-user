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
from copy import deepcopy

from PIL import Image
from pyrogram import Client, Filters, Message, WebPage

from .. import glovar
from ..functions.channel import forward_evidence, get_debug_text, send_debug, share_data
from ..functions.etc import code, general_link, get_channel_link, get_now, get_stripped_link, thread
from ..functions.file import data_to_file, delete_file, get_downloaded_path, save
from ..functions.filters import class_c, class_d, class_e, declared_message, exchange_channel, from_user, hide_channel
from ..functions.filters import is_declared_message, is_delete, new_group, test_group
from ..functions.group import archive_chat, leave_group
from ..functions.ids import init_group_id, init_user_id
from ..functions.receive import receive_add_bad, receive_add_except, receive_config_commit, receive_config_reply
from ..functions.receive import receive_declared_message, receive_help_ban, receive_help_delete, receive_leave_approve
from ..functions.receive import receive_refresh, receive_remove_bad, receive_remove_except
from ..functions.receive import receive_status_ask, receive_text_data
from ..functions.telegram import delete_all_messages, get_admins, read_history, read_mention
from ..functions.telegram import resolve_username, send_message
from ..functions.tests import preview_test
from ..functions.user import ban_user, terminate_user

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user & ~Filters.service
                   & ~class_c & class_d & ~class_e & ~declared_message)
def check(client: Client, message: Message) -> bool:
    # Check messages from groups
    glovar.locks["message"].acquire()
    try:
        # Check declare status
        if is_declared_message(None, message):
            return True

        # All groups' admins
        uid = message.from_user.id
        admin_ids = deepcopy(glovar.admin_ids)
        for gid in admin_ids:
            if uid in admin_ids[gid]:
                return True

        # Need deletion
        if is_delete(message):
            terminate_user(client, message)

        return True
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user & Filters.new_chat_members & ~new_group
                   & ~class_c & ~class_e & ~declared_message)
def check_join(client: Client, message: Message) -> bool:
    # Check new joined user
    glovar.locks["message"].acquire()
    try:
        # Check declare status
        if is_declared_message(None, message):
            return True

        # All groups' admins
        uid = message.from_user.id
        admin_ids = deepcopy(glovar.admin_ids)
        for gid in admin_ids:
            if uid in admin_ids[gid]:
                return True

        gid = message.chat.id
        mid = message.message_id

        if glovar.configs[gid]["subscribe"]:
            for n in message.new_chat_members:
                uid = n.id
                if init_user_id(uid):
                    if uid in glovar.bad_ids["users"]:
                        # now = get_now()
                        # banned_time = glovar.banned_ids[uid].get(gid, 0)
                        # if banned_time and now - banned_time > 10:
                        #     glovar.except_ids["temp"][uid].add(gid)
                        #     save("except_ids")
                        #     # If three groups forgive the user, then unban the user automatically
                        #     if len(glovar.except_ids["temp"][uid]) == 3:
                        #         unban_user_globally(client, uid)
                        #         share_forgiven_user(client, uid)
                        #         send_debug(client, message.chat, "自动解禁", uid, mid, message)
                        #     else:
                        #         unban_user(client, gid, uid)
                        #         send_debug(client, message.chat, "单独解禁", uid, mid, message)
                        # else:
                        glovar.banned_ids[uid][gid] = get_now()
                        save("banned_ids")
                        result = forward_evidence(client, message, "自动封禁", "订阅列表")
                        if result:
                            ban_user(client, gid, message.from_user.username or uid)
                            thread(delete_all_messages, (client, gid, uid))
                            send_debug(client, message.chat, "自动封禁", uid, mid, result)

        return True
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)
    finally:
        glovar.locks["message"].release()

    return False


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix), group=-1)
def exchange_emergency(client: Client, message: Message) -> bool:
    # Sent emergency channel transfer request
    try:
        # Read basic information
        data = receive_text_data(message)
        if data:
            sender = data["from"]
            receivers = data["to"]
            action = data["action"]
            action_type = data["type"]
            data = data["data"]
            if "EMERGENCY" in receivers:
                if action == "backup":
                    if action_type == "hide":
                        if data is True:
                            glovar.should_hide = data
                        elif data is False and sender == "MANAGE":
                            glovar.should_hide = data

                        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                                f"执行操作：{code('频道转移')}\n"
                                f"应急频道：{code((lambda x: '启用' if x else '禁用')(glovar.should_hide))}\n")
                        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user
                   & (Filters.new_chat_members | Filters.group_chat_created | Filters.supergroup_chat_created)
                   & new_group)
def init_group(client: Client, message: Message) -> bool:
    # Initiate new groups
    try:
        gid = message.chat.id
        text = get_debug_text(client, message.chat)
        # Check permission
        if init_group_id(gid):
            admin_members = get_admins(client, gid)
            if admin_members:
                glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                         if not admin.user.is_bot and not admin.user.is_deleted}
                save("admin_ids")
                archive_chat(client, gid)
                text += f"状态：{code('已加入群组')}\n"
            else:
                thread(leave_group, (client, gid))
                text += (f"状态：{code('已退出群组')}\n"
                         f"原因：{code('获取管理员列表失败')}\n")

        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)

    return False


@Client.on_message(~Filters.private & Filters.incoming & Filters.mentioned, group=1)
def mark_mention(client: Client, message: Message) -> bool:
    # Mark mention as read
    try:
        if message.chat:
            cid = message.chat.id
            thread(read_mention, (client, cid))

        return True
    except Exception as e:
        logger.warning(f"Mark mention error: {e}", exc_info=True)

    return False


@Client.on_message(~Filters.private & Filters.incoming, group=2)
def mark_message(client: Client, message: Message) -> bool:
    # Mark messages from groups and channels as read
    try:
        if message.chat:
            cid = message.chat.id
            thread(read_history, (client, cid))

        return True
    except Exception as e:
        logger.warning(f"Mark message error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client: Client, message: Message) -> bool:
    # Process the data in exchange channel
    if glovar.locks["receive"].acquire():
        try:
            data = receive_text_data(message)
            if data:
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
                                receive_help_delete(client, sender, data)

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
                                receive_help_delete(client, sender, data)

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
                                receive_help_delete(client, sender, data)

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
                                receive_help_delete(client, sender, data)

                        elif action == "update":
                            if action_type == "declare":
                                receive_declared_message(data)

                    elif sender == "MANAGE":

                        if action == "add":
                            if action == "add":
                                if action_type == "bad":
                                    receive_add_bad(sender, data)
                                elif action_type == "except":
                                    receive_add_except(client, data)

                        elif action == "leave":
                            if action_type == "approve":
                                receive_leave_approve(client, data)

                        elif action == "remove":
                            if action_type == "bad":
                                receive_remove_bad(client, sender, data)
                            elif action_type == "except":
                                receive_remove_except(client, data)

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
                                receive_help_delete(client, sender, data)

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
                                receive_help_delete(client, sender, data)

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
                                receive_help_delete(client, sender, data)

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
                                receive_help_delete(client, sender, data)

                        elif action == "update":
                            if action_type == "declare":
                                receive_declared_message(data)

                    elif sender == "WARN":

                        if action == "help":
                            if action_type == "delete":
                                receive_help_delete(client, sender, data)

            return True
        except Exception as e:
            logger.warning(f"Process data error: {e}", exc_info=True)
        finally:
            glovar.locks["receive"].release()

    return False


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user & ~Filters.service
                   & ~class_d & ~class_e & ~declared_message)
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


@Client.on_message(Filters.incoming & Filters.group & test_group & from_user & ~Filters.service & ~Filters.bot
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def test(client: Client, message: Message) -> bool:
    # Show test results in TEST group
    if glovar.locks["test"].acquire():
        try:
            preview_test(client, message)

            return True
        except Exception as e:
            logger.warning(f"Test error: {e}", exc_info=True)
        finally:
            glovar.locks["test"].release()

    return False

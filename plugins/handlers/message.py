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
from pickle import dump

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import forward_evidence, get_debug_text, receive_data, send_debug, share_data
from ..functions.etc import code, general_link, thread, user_mention
from ..functions.file import get_new_path, save
from ..functions.filters import class_c, class_d, class_e, declared_message, exchange_channel, hide_channel
from ..functions.filters import new_group, test_group
from ..functions.group import delete_message, delete_messages_globally, leave_group
from ..functions.ids import init_group_id, init_user_id
from ..functions.telegram import delete_all_messages, get_admins, get_preview, mark_as_read
from ..functions.telegram import send_message, send_report_message, unban_chat_member
from ..functions.tests import preview_test
from ..functions.user import ban_user, ban_user_globally

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & ~Filters.new_chat_members
                   & ~class_c & class_d & ~declared_message)
def check(client: Client, message: Message):
    try:
        gid = message.chat.id
        if glovar.configs[gid]["subscribe"]:
            uid = message.from_user.id
            mid = message.message_id
            if message.forward_from or message.forward_from_chat:
                if uid not in glovar.recorded_ids[gid]:
                    glovar.recorded_ids[gid].add(uid)
                    result = forward_evidence(client, message, "自动删除", "订阅列表")
                    if result:
                        send_debug(client, message.chat, "自动删除", uid, mid, result)

            delete_message(client, gid, mid)
    except Exception as e:
        logger.warning(f"Check error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & Filters.new_chat_members
                   & ~class_c & ~class_e & ~declared_message)
def check_join(client: Client, message: Message):
    try:
        gid = message.chat.id
        mid = message.message_id
        if glovar.configs[gid]["subscribe"]:
            for n in message.new_chat_members:
                uid = n.id
                if init_user_id(uid):
                    if uid in glovar.bad_ids["users"]:
                        if gid in glovar.banned_ids[uid]:
                            glovar.except_ids["tmp"][uid].add(gid)
                            save("except_ids")
                        else:
                            glovar.banned_ids[uid].add(gid)
                            save("banned_ids")
                            result = forward_evidence(client, message, "自动封禁", "订阅列表")
                            if result:
                                ban_user(client, gid, uid)
                                send_debug(client, message.chat, "自动封禁", uid, mid, result)
    except Exception as e:
        logger.warning(f"Check join error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & hide_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def exchange_emergency(_, message: Message):
    try:
        # Read basic information
        data = receive_data(message)
        sender = data["from"]
        receivers = data["to"]
        action = data["action"]
        action_type = data["type"]
        data = data["data"]
        if "EMERGENCY" in receivers:
            if sender == "EMERGENCY":
                if action == "backup":
                    if action_type == "hide":
                        glovar.should_hide = data
    except Exception as e:
        logger.warning(f"Exchange emergency error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & Filters.new_chat_members & new_group)
def init_group(client: Client, message: Message):
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
                text += f"状态：{code('已加入群组')}\n"
            else:
                thread(leave_group, (client, gid))
                text += (f"状态：{code('已退出群组')}\n"
                         f"原因：{code('获取管理员列表失败')}\n")

        thread(send_message, (client, glovar.debug_channel_id, text))
    except Exception as e:
        logger.warning(f"Init group error: {e}", exc_info=True)


@Client.on_message(~Filters.private & Filters.incoming & Filters.mentioned, group=1)
def mark_mention(client: Client, message: Message):
    try:
        cid = message.chat.id
        thread(mark_as_read, (client, cid, "mention"))
    except Exception as e:
        logger.warning(f"Mark mention error: {e}", exc_info=True)


@Client.on_message(~Filters.private & Filters.incoming, group=2)
def mark_message(client, message):
    try:
        cid = message.chat.id
        thread(mark_as_read, (client, cid, "message"))
    except Exception as e:
        logger.warning(f"Mark message error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.channel & exchange_channel
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def process_data(client: Client, message: Message):
    try:
        data = receive_data(message)
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
                if sender == "CLEAN":
                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")

                    elif action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "ban":
                            if init_user_id(user_id):
                                glovar.banned_ids[user_id].add(group_id)
                                thread(ban_user_globally, (client, user_id))
                        elif action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            if glovar.configs.get(group_id):
                                if init_group_id(group_id):
                                    glovar.declared_message_ids[group_id].add(message_id)

                elif sender == "CONFIG":

                    if action == "config":
                        if action_type == "commit":
                            gid = data["group_id"]
                            config = data["config"]
                            glovar.configs[gid] = config
                            save("configs")
                        elif action_type == "reply":
                            gid = data["group_id"]
                            uid = data["user_id"]
                            link = data["config_link"]
                            text = (f"管理员：{user_mention(uid)}\n"
                                    f"操作：{code('更改设置')}\n"
                                    f"设置链接：{general_link('点击此处', link)}")
                            thread(send_report_message, (180, client, gid, text))

                elif sender == "LANG":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")

                    elif action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "ban":
                            if init_user_id(user_id):
                                glovar.banned_ids[user_id].add(group_id)
                                thread(ban_user_globally, (client, user_id))
                        elif action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            if glovar.configs.get(group_id):
                                if init_group_id(group_id):
                                    glovar.declared_message_ids[group_id].add(message_id)

                elif sender == "LONG":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")

                    elif action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "ban":
                            if init_user_id(user_id):
                                glovar.banned_ids[user_id].add(group_id)
                                thread(ban_user_globally, (client, user_id))
                        elif action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            if glovar.configs.get(group_id):
                                if init_group_id(group_id):
                                    glovar.declared_message_ids[group_id].add(message_id)

                elif sender == "MANAGE":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "channel":
                                glovar.bad_ids["channels"].add(the_id)
                                save("bad_ids")
                        elif action_type == "except":
                            if the_type == "channels":
                                glovar.except_ids["channels"].add(the_id)
                            elif the_type == "user":
                                glovar.except_ids["users"].add(the_id)

                            save("except_ids")

                    elif action == "leave":
                        if action_type == "approve":
                            the_id = data["group_id"]
                            reason = data["reason"]
                            if action_type == "group":
                                text = get_debug_text(client, the_id)
                                text += (f"状态：{code('已退出该群组')}\n"
                                         f"原因：{code(reason)}")
                                leave_group(client, the_id)
                                thread(send_message, (client, glovar.debug_channel_id, text))

                    elif action == "remove":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "channel":
                                glovar.bad_ids["channels"].discard(the_id)
                            elif the_type == "user":
                                glovar.bad_ids["users"].discard(the_id)
                                save("bad_ids")
                                for gid in glovar.banned_ids[the_id]:
                                    thread(unban_chat_member, (client, gid, the_id))

                                glovar.banned_ids[the_id] = set()
                                save("banned_ids")
                                if glovar.except_ids["tmp"].get(the_id):
                                    glovar.except_ids["tmp"].pop(the_id, set())
                                    save("except_ids")

                            save("bad_ids")
                        elif action_type == "except":
                            if the_type == "channel":
                                glovar.except_ids["channels"].discard(the_id)
                            elif the_type == "user":
                                glovar.except_ids["users"].discard(the_id)
                                glovar.except_ids["tmp"].pop(the_id, set())

                            save("except_ids")

                elif sender == "NOFLOOD":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")

                    elif action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "ban":
                            if init_user_id(user_id):
                                glovar.banned_ids[user_id].add(group_id)
                                thread(ban_user_globally, (client, user_id))
                        elif action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            if glovar.configs.get(group_id):
                                if init_group_id(group_id):
                                    glovar.declared_message_ids[group_id].add(message_id)

                elif sender == "NOPORN":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")

                    elif action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "ban":
                            if init_user_id(user_id):
                                glovar.banned_ids[user_id].add(group_id)
                                thread(ban_user_globally, (client, user_id))
                        elif action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            if glovar.configs.get(group_id):
                                if init_group_id(group_id):
                                    glovar.declared_message_ids[group_id].add(message_id)

                elif sender == "NOSPAM":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")

                    elif action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "ban":
                            if init_user_id(user_id):
                                glovar.banned_ids[user_id].add(group_id)
                                thread(ban_user_globally, (client, user_id))
                        elif action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            if glovar.configs.get(group_id):
                                if init_group_id(group_id):
                                    glovar.declared_message_ids[group_id].add(message_id)

                elif sender == "RECHECK":

                    if action == "add":
                        the_id = data["id"]
                        the_type = data["type"]
                        if action_type == "bad":
                            if the_type == "user":
                                glovar.bad_ids["users"].add(the_id)
                                save("bad_ids")

                    elif action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "ban":
                            if init_user_id(user_id):
                                glovar.banned_ids[user_id].add(group_id)
                                thread(ban_user_globally, (client, user_id))
                        elif action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))

                    elif action == "update":
                        if action_type == "declare":
                            group_id = data["group_id"]
                            message_id = data["message_id"]
                            if glovar.configs.get(group_id):
                                if init_group_id(group_id):
                                    glovar.declared_message_ids[group_id].add(message_id)

                elif sender == "WARN":

                    if action == "help":
                        group_id = data["group_id"]
                        user_id = data["user_id"]
                        if action_type == "delete":
                            help_type = data["type"]
                            if help_type == "global":
                                thread(delete_messages_globally, (client, user_id))
                            elif help_type == "single":
                                thread(delete_all_messages, (client, group_id, user_id))
    except Exception as e:
        logger.warning(f"Process data error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & ~Filters.service
                   & ~class_c & ~class_d & ~class_e & ~declared_message)
def share_preview(client: Client, message: Message):
    try:
        preview, _ = get_preview(client, message)
        if preview["text"] or preview["file_id"]:
            gid = message.chat.id
            uid = message.from_user.id
            mid = message.message_id
            file_path = get_new_path()
            with open(file_path, "wb") as f:
                dump(preview, f)

            share_data(
                client=client,
                receivers=glovar.receivers_preview,
                action="update",
                action_type="preview",
                data={
                    "group_id": gid,
                    "user_id": uid,
                    "message_id": mid
                },
                file=file_path,
                encrypt=False
            )
    except Exception as e:
        logger.warning(f"Share preview error: {e}", exc_info=True)


@Client.on_message(Filters.incoming & Filters.group & test_group & ~Filters.service & ~Filters.bot
                   & ~Filters.command(glovar.all_commands, glovar.prefix))
def test(client: Client, message: Message):
    try:
        preview_test(client, message)
    except Exception as e:
        logger.warning(f"Test error: {e}", exc_info=True)

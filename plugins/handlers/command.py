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

from pyrogram import Client, Filters, Message

from .. import glovar
from ..functions.channel import get_debug_text, share_data
from ..functions.etc import bold, code, delay, code_block, get_command_context, get_command_type, get_int, get_now
from ..functions.etc import thread, mention_id
from ..functions.file import save
from ..functions.filters import from_user, is_class_c, test_group
from ..functions.group import delete_message
from ..functions.telegram import get_group_info, resolve_username, send_message, send_report_message

# Enable logging
logger = logging.getLogger(__name__)


@Client.on_message(Filters.incoming & Filters.group & ~test_group & from_user
                   & Filters.command(["config"], glovar.prefix))
def config(client: Client, message: Message) -> bool:
    # Request CONFIG session
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            # Check command format
            command_type = get_command_type(message)
            if command_type and re.search(f"^{glovar.sender}$", command_type, re.I):
                now = get_now()
                # Check the config lock
                if now - glovar.configs[gid]["lock"] > 310:
                    # Set lock
                    glovar.configs[gid]["lock"] = now
                    save("configs")
                    # Ask CONFIG generate a config session
                    group_name, group_link = get_group_info(client, message.chat)
                    share_data(
                        client=client,
                        receivers=["CONFIG"],
                        action="config",
                        action_type="ask",
                        data={
                            "project_name": glovar.project_name,
                            "project_link": glovar.project_link,
                            "group_id": gid,
                            "group_name": group_name,
                            "group_link": group_link,
                            "user_id": message.from_user.id,
                            "config": glovar.configs[gid],
                            "default": glovar.default_config
                        }
                    )
                    # Send a report message to debug channel
                    text = get_debug_text(client, message.chat)
                    text += (f"群管理：{code(message.from_user.id)}\n"
                             f"操作：{code('创建设置会话')}\n")
                    thread(send_message, (client, glovar.debug_channel_id, text))

            delay(3, delete_message, [client, gid, mid])
        else:
            thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Config error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.group & ~test_group & from_user
                   & Filters.command(["config_user"], glovar.prefix))
def config_directly(client: Client, message: Message) -> bool:
    # Config the bot directly
    try:
        gid = message.chat.id
        mid = message.message_id
        # Check permission
        if is_class_c(None, message):
            aid = message.from_user.id
            success = True
            reason = "已更新"
            new_config = deepcopy(glovar.configs[gid])
            text = f"管理员：{code(aid)}\n"
            # Check command format
            command_type, command_context = get_command_context(message)
            if command_type:
                if command_type == "show":
                    text += (f"操作：{code('查看设置')}\n"
                             f"设置：{code((lambda x: '默认' if x else '自定义')(new_config.get('default')))}\n"
                             f"协助删除：{code((lambda x: '启用' if x else '禁用')(new_config.get('delete')))}\n"
                             f"订阅名单：{code((lambda x: '启用' if x else '禁用')(new_config.get('subscribe')))}\n")
                    thread(send_report_message, (15, client, gid, text))
                    thread(delete_message, (client, gid, mid))
                    return True

                now = get_now()
                # Check the config lock
                if now - new_config["lock"] > 310:
                    if command_type == "default":
                        if not new_config.get("default"):
                            new_config = deepcopy(glovar.default_config)
                    else:
                        if command_context:
                            if command_type in {"delete", "subscribe"}:
                                if command_context == "off":
                                    new_config[command_type] = False
                                elif command_context == "on":
                                    new_config[command_type] = True
                                else:
                                    success = False
                                    reason = "命令参数有误"
                            else:
                                success = False
                                reason = "命令类别有误"
                        else:
                            success = False
                            reason = "命令参数缺失"

                        if success:
                            new_config["default"] = False
                else:
                    success = False
                    reason = "设置当前被锁定"
            else:
                success = False
                reason = "格式有误"

            if success and new_config != glovar.configs[gid]:
                glovar.configs[gid] = new_config
                save("configs")

            text += (f"操作：{code('更改设置')}\n"
                     f"状态：{code(reason)}\n")
            thread(send_report_message, ((lambda x: 10 if x else 5)(success), client, gid, text))

        thread(delete_message, (client, gid, mid))

        return True
    except Exception as e:
        logger.warning(f"Config directly error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & test_group & from_user
                   & Filters.command(["mention"], glovar.prefix))
def mention(client: Client, message: Message) -> bool:
    # Mention a user
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = f"管理员：{mention_id(aid)}\n\n"
        uid = 0
        id_text = get_command_type(message)
        the_type = ""
        if id_text:
            uid = get_int(id_text)
            if not uid:
                the_type, the_id = resolve_username(client, id_text)
                if the_type == "user":
                    uid = the_id
        elif message.reply_to_message:
            r_message = message.reply_to_message
            if r_message.forward_from:
                uid = r_message.forward_from.id

        if uid:
            if the_type:
                text += f"查询用户：{code(uid)}\n"
            else:
                text += f"查询用户：{mention_id(uid)}\n"
        else:
            text += f"错误：{code('用户参数有误')}\n"

        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Mention error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & test_group & from_user
                   & Filters.command(["print"], glovar.prefix))
def print_message(client: Client, message: Message) -> bool:
    # Print a message
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        if message.reply_to_message:
            result = str(message.reply_to_message).replace("pyrogram.", "")
            result = re.sub('"phone_number": ".*?"', '"phone_number": "███████████"', result)
            result_list = [result[i:i + 3000] for i in range(0, len(result), 3000)]
            for result in result_list:
                text = (f"管理员：{mention_id(aid)}\n\n"
                        f"消息结构：" + "-" * 24 + "\n\n"
                        f"{code_block(result.rstrip())}\n")
                send_message(client, cid, text, mid)

        return True
    except Exception as e:
        logger.warning(f"Print message error: {e}", exc_info=True)

    return False


@Client.on_message(Filters.incoming & Filters.group & test_group & from_user
                   & Filters.command(["version"], glovar.prefix))
def version(client: Client, message: Message) -> bool:
    # Check the program's version
    try:
        cid = message.chat.id
        aid = message.from_user.id
        mid = message.message_id
        text = (f"管理员：{mention_id(aid)}\n\n"
                f"版本：{bold(glovar.version)}\n")
        thread(send_message, (client, cid, text, mid))

        return True
    except Exception as e:
        logger.warning(f"Version error: {e}", exc_info=True)

    return False

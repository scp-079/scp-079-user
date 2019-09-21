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
import pickle
from json import loads
from typing import Any

from pyrogram import Client, Message

from .. import glovar
from .channel import get_debug_text, share_data
from .etc import code, general_link, get_text, thread, user_mention
from .file import crypt_file, data_to_file, delete_file, get_new_path, get_downloaded_path, save
from .group import delete_messages_globally, leave_group
from .ids import init_group_id, init_user_id
from .telegram import delete_all_messages, send_message, send_report_message
from .timers import update_admins
from .user import ban_user_globally, unban_user_globally

# Enable logging
logger = logging.getLogger(__name__)


def receive_add_except(_: Client, data: dict) -> bool:
    # Receive a object and add it to except list
    try:
        the_id = data["id"]
        the_type = data["type"]
        # Receive except channels
        if the_type == "channel":
            glovar.except_ids["channels"].add(the_id)
            save("except_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add except error: {e}", exc_info=True)

    return False


def receive_add_bad(sender: str, data: dict) -> bool:
    # Receive bad users or channels that other bots shared
    try:
        the_id = data["id"]
        the_type = data["type"]
        if the_type == "user":
            glovar.bad_ids["users"].add(the_id)
            save("bad_ids")
        elif sender == "MANAGE" and the_type == "channel":
            glovar.bad_ids["channels"].add(the_id)
            save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive add bad error: {e}", exc_info=True)

    return False


def receive_config_commit(data: dict) -> bool:
    # Receive config commit
    try:
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
        gid = data["group_id"]
        uid = data["user_id"]
        link = data["config_link"]
        text = (f"管理员：{code(uid)}\n"
                f"操作：{code('更改设置')}\n"
                f"说明：{general_link('请点击此处进行设置', link)}\n")
        thread(send_report_message, (180, client, gid, text))

        return True
    except Exception as e:
        logger.warning(f"Receive config reply error: {e}", exc_info=True)

    return False


def receive_declared_message(data: dict) -> bool:
    # Update declared message's id
    try:
        gid = data["group_id"]
        mid = data["message_id"]
        if glovar.admin_ids.get(gid):
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
        if message.document:
            file_id = message.document.file_id
            path = get_downloaded_path(client, file_id)
            if path:
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


def receive_help_ban(client: Client, data: dict) -> bool:
    # Receive help ban requests
    if glovar.locks["message"].acquire():
        try:
            group_id = data["group_id"]
            user_id = data["user_id"]
            if user_id not in glovar.helped_ids:
                if init_user_id(user_id):
                    glovar.helped_ids.add(user_id)
                    if glovar.configs[group_id]["delete"]:
                        thread(delete_all_messages, (client, group_id, user_id))

                    thread(ban_user_globally, (client, group_id, user_id))
                    glovar.banned_ids[user_id].add(group_id)
                    save("banned_ids")

            return True
        except Exception as e:
            logger.warning(f"Receive help ban error: {e}", exc_info=True)
        finally:
            glovar.locks["message"].release()

    return False


def receive_help_delete(client: Client, sender: str, data: dict) -> bool:
    # Receive help delete requests
    try:
        group_id = data["group_id"]
        user_id = data["user_id"]
        help_type = data["type"]
        if group_id and group_id not in glovar.admin_ids:
            return True

        if help_type == "global":
            thread(delete_messages_globally, (client, user_id))
        elif help_type == "single" and (glovar.configs[group_id]["delete"] or sender in {"CLEAN", "WARN"}):
            thread(delete_all_messages, (client, group_id, user_id))

        return True
    except Exception as e:
        logger.warning(f"Receive help delete error: {e}", exc_info=True)

    return False


def receive_leave_approve(client: Client, data: dict) -> bool:
    # Receive leave approve
    try:
        admin_id = data["admin_id"]
        the_id = data["group_id"]
        reason = data["reason"]
        if reason == "permissions":
            reason = "权限缺失"
        elif reason == "user":
            reason = "缺失 USER"

        if glovar.admin_ids.get(the_id, {}):
            text = get_debug_text(client, the_id)
            text += (f"项目管理员：{user_mention(admin_id)}\n"
                     f"状态：{code('已批准退出该群组')}\n")
            if reason:
                text += f"原因：{code(reason)}\n"

            leave_group(client, the_id)
            thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive leave approve error: {e}", exc_info=True)

    return False


def receive_refresh(client: Client, data: int) -> bool:
    # Receive refresh
    try:
        aid = data
        update_admins(client)
        text = (f"项目编号：{general_link(glovar.project_name, glovar.project_link)}\n"
                f"项目管理员：{user_mention(aid)}\n"
                f"执行操作：{code('刷新群管列表')}\n")
        thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Receive refresh error: {e}", exc_info=True)

    return False


def receive_remove_bad(client: Client, sender: str, data: dict) -> bool:
    # Receive removed bad objects
    try:
        the_id = data["id"]
        the_type = data["type"]
        if sender == "MANAGE" and the_type == "channel":
            glovar.bad_ids["channels"].discard(the_id)
        elif the_type == "user":
            glovar.bad_ids["users"].discard(the_id)
            unban_user_globally(client, the_id)

        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove bad error: {e}", exc_info=True)

    return False


def receive_remove_except(_: Client, data: dict) -> bool:
    # Receive a object and remove it from except list
    try:
        the_id = data["id"]
        the_type = data["type"]
        # Receive except channels
        if the_type == "channel":
            glovar.except_ids["channels"].discard(the_id)
            save("except_ids")

        return True
    except Exception as e:
        logger.warning(f"Receive remove except error: {e}", exc_info=True)

    return False


def receive_status_ask(client: Client, data: dict) -> bool:
    # Receive version info request
    try:
        aid = data["admin_id"]
        mid = data["message_id"]
        group_count = len(glovar.admin_ids)
        status = {
            "群组数量": f"{group_count} 个"
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

    return False


def receive_text_data(message: Message) -> dict:
    # Receive text's data from exchange channel
    data = {}
    try:
        text = get_text(message)
        if text:
            data = loads(text)
    except Exception as e:
        logger.warning(f"Receive data error: {e}")

    return data

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
from typing import Union

from pyrogram import Client, Message

from .. import glovar
from .channel import forward_evidence, send_debug
from .etc import thread
from .file import save
from .group import delete_message
from .ids import init_group_id
from .telegram import get_common_chats, kick_chat_member, resolve_username, unban_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def add_bad_user(uid: int) -> bool:
    # Add a bad user, share it
    try:
        glovar.bad_ids["users"].add(uid)
        save("bad_ids")

        return True
    except Exception as e:
        logger.warning(f"Add bad user error: {e}", exc_info=True)

    return False


def ban_user(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Ban a user
    try:
        thread(kick_chat_member, (client, gid, uid))
        if isinstance(uid, int):
            glovar.banned_ids[uid].add(gid)
        else:
            peer_type, peer_id = resolve_username(client, uid)
            if peer_type == "user":
                glovar.banned_ids[peer_id].add(gid)

        save("banned_ids")

        return True
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)

    return False


def ban_user_globally(client: Client, uid: int) -> bool:
    # Ban a user globally
    try:
        chats = get_common_chats(client, uid)
        if chats:
            for chat in chats:
                gid = chat.id
                if init_group_id(gid):
                    if glovar.configs[gid]["subscribe"]:
                        thread(ban_user, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Ban user globally error: {e}", exc_info=True)

    return False


def terminate_user(client: Client, message: Message) -> bool:
    # Delete user's message
    try:
        gid = message.chat.id
        uid = message.from_user.id
        mid = message.message_id
        if gid not in glovar.banned_ids.get(uid, set()):
            result = forward_evidence(client, message, "自动封禁", "订阅列表")
            if result:
                ban_user(client, gid, uid)
                send_debug(client, message.chat, "自动封禁", uid, mid, result)
        elif uid not in glovar.recorded_ids[gid]:
            glovar.recorded_ids[gid].add(uid)
            result = forward_evidence(client, message, "自动删除", "订阅列表")
            if result:
                send_debug(client, message.chat, "自动删除", uid, mid, result)

        delete_message(client, gid, mid)

        return True
    except Exception as e:
        logger.warning(f"Terminate user error: {e}", exc_info=True)

    return False


def unban_user(client: Client, gid: int, uid: int) -> bool:
    # Unban a user
    try:
        thread(unban_chat_member, (client, gid, uid))
        glovar.banned_ids[uid].discard(gid)
        save("banned_ids")

        return True
    except Exception as e:
        logger.warning(f"Unban user error: {e}", exc_info=True)

    return False


def unban_user_globally(client: Client, uid: int) -> bool:
    # Unban a user globally
    try:
        glovar.bad_ids["users"].discard(uid)
        save("bad_ids")

        for gid in glovar.banned_ids[uid]:
            unban_user(client, gid, uid)

        if glovar.except_ids["temp"].get(uid, set()):
            glovar.except_ids["temp"].pop(uid, set())
            save("except_ids")
    except Exception as e:
        logger.warning(f"Unban user globally error: {e}", exc_info=True)

    return False

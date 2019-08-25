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

from pyrogram import Client
from pyrogram.api.types import InputPeerUser, InputPeerChannel

from .. import glovar
from .etc import get_int, thread
from .file import save
from .ids import init_group_id
from .telegram import get_common_chats, kick_chat_member, resolve_peer, unban_chat_member

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


def ban_user(client: Client, gid: int, uid: int) -> bool:
    # Ban a user
    try:
        thread(kick_chat_member, (client, gid, uid))
        glovar.banned_ids[uid].add(gid)
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
                gid = int(f"-100{chat.id}")
                if init_group_id(gid):
                    if glovar.configs[gid]["subscribe"]:
                        thread(ban_user, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Ban user globally error: {e}", exc_info=True)

    return False


def resolve_username(client: Client, username: str) -> (str, int):
    # Resolve peer by username
    peer_type = ""
    peer_id = 0
    try:
        if username:
            result = resolve_peer(client, username)
            if result:
                if isinstance(result, InputPeerChannel):
                    peer_type = "channel"
                    peer_id = result.channel_id
                    peer_id = get_int(f"-100{peer_id}")
                elif isinstance(result, InputPeerUser):
                    peer_type = "user"
                    peer_id = result.user_id
    except Exception as e:
        logger.warning(f"Resolve username error: {e}", exc_info=True)

    return peer_type, peer_id


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

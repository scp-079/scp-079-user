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

from .. import glovar
from .etc import thread
from .file import save
from .telegram import get_common_chats, kick_chat_member

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
                thread(ban_user, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Ban user globally error: {e}", exc_info=True)

    return False

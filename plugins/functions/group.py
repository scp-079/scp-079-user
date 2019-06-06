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
from .ids import init_group_id
from .telegram import delete_messages, delete_all_messages, get_common_chats, leave_chat

# Enable logging
logger = logging.getLogger(__name__)


def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    try:
        mids = [mid]
        thread(delete_messages, (client, gid, mids))
        return True
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return False


def delete_messages_globally(client: Client, uid: int) -> bool:
    # Delete all messages from a user globally
    try:
        chats = get_common_chats(client, uid)
        if chats:
            for chat in chats:
                gid = int(f"-100{chat.id}")
                if init_group_id(gid):
                    if glovar.configs[gid]["subscribe"]:
                        thread(delete_all_messages, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Delete messages globally error: {e}", exc_info=True)

    return False


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    try:
        thread(leave_chat, (client, gid))

        glovar.admin_ids.pop(gid, None)
        save("admin_ids")

        glovar.configs.pop(gid, None)
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

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
from typing import Optional

from pyrogram import Chat, ChatMember, Client, Message

from .. import glovar
from .etc import code, lang, t2t, thread
from .file import save
from .ids import init_group_id
from .telegram import delete_messages, delete_all_messages, get_chat, get_chat_member, get_common_chats
from .telegram import get_messages, leave_chat

# Enable logging
logger = logging.getLogger(__name__)


def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    try:
        if not gid or not mid:
            return True

        mids = [mid]
        thread(delete_messages, (client, gid, mids))

        return True
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return False


def delete_messages_globally(client: Client, uid: int, no_id: int = 0) -> bool:
    # Delete all messages from a user globally
    try:
        chats = get_common_chats(client, uid)

        if not chats:
            return True

        for chat in chats:
            gid = chat.id

            if gid == no_id:
                continue

            if not init_group_id(gid):
                continue

            if (glovar.configs[gid].get("delete")
                    and (glovar.configs[gid].get("gb")
                         or glovar.configs[gid].get("gr")
                         or glovar.configs[gid].get("gd"))):
                thread(delete_all_messages, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Delete messages globally error: {e}", exc_info=True)

    return False


def get_config_text(config: dict) -> str:
    # Get config text
    result = ""
    try:
        # Basic
        default_text = (lambda x: lang("default") if x else lang("custom"))(config.get("default"))
        delete_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get("delete"))
        result += (f"{lang('config')}{lang('colon')}{code(default_text)}\n"
                   f"{lang('delete')}{lang('colon')}{code(delete_text)}\n")

        # Others
        for the_type in ["gb", "gr", "gd", "sb", "sr", "sd"]:
            the_text = (lambda x: lang("enabled") if x else lang("disabled"))(config.get(the_type))
            result += f"{lang(the_type)}{lang('colon')}{code(the_text)}\n"
    except Exception as e:
        logger.warning(f"Get config text error: {e}", exc_info=True)

    return result


def get_description(client: Client, gid: int) -> str:
    # Get group's description
    result = ""
    try:
        group = get_group(client, gid)
        if group and group.description:
            result = t2t(group.description, False, False)
    except Exception as e:
        logger.warning(f"Get description error: {e}", exc_info=True)

    return result


def get_group(client: Client, gid: int, cache: bool = True) -> Optional[Chat]:
    # Get the group
    result = None
    try:
        the_cache = glovar.chats.get(gid)

        if the_cache:
            result = the_cache
        else:
            result = get_chat(client, gid)

        if cache and result:
            glovar.chats[gid] = result
    except Exception as e:
        logger.warning(f"Get group error: {e}", exc_info=True)

    return result


def get_member(client: Client, gid: int, uid: int, cache: bool = True) -> Optional[ChatMember]:
    # Get a member in the group
    result = None
    try:
        if not init_group_id(gid):
            return None

        the_cache = glovar.members[gid].get(uid)

        if the_cache:
            result = the_cache
        else:
            result = get_chat_member(client, gid, uid)

        if cache and result:
            glovar.members[gid][uid] = result
    except Exception as e:
        logger.warning(f"Get member error: {e}", exc_info=True)

    return result


def get_message(client: Client, gid: int, mid: int) -> Optional[Message]:
    # Get a single message
    result = None
    try:
        mids = [mid]
        result = get_messages(client, gid, mids)
        if result:
            result = result[0]
    except Exception as e:
        logger.warning(f"Get message error: {e}", exc_info=True)

    return result


def get_pinned(client: Client, gid: int) -> Optional[Message]:
    # Get group's pinned message
    result = None
    try:
        group = get_group(client, gid)
        if group and group.pinned_message:
            result = group.pinned_message
    except Exception as e:
        logger.warning(f"Get pinned error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    try:
        glovar.left_group_ids.add(gid)
        save("left_group_ids")
        thread(leave_chat, (client, gid, True))

        glovar.admin_ids.pop(gid, set())
        save("admin_ids")

        glovar.configs.pop(gid, {})
        save("configs")

        return True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return False

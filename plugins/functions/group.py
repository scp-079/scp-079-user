# SCP-079-USER - Invite and help other bots
# Copyright (C) 2019-2020 SCP-079 <https://scp-079.org>
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
from typing import List, Optional

from pyrogram import Chat, ChatMember, Client, Message

from .. import glovar
from .decorators import threaded
from .etc import code, lang, t2t, thread
from .file import save
from .ids import init_group_id
from .telegram import delete_messages, delete_all_messages, get_chat, get_chat_member, get_common_chats, leave_chat

# Enable logging
logger = logging.getLogger(__name__)


@threaded()
def delete_message(client: Client, gid: int, mid: int) -> bool:
    # Delete a single message
    result = False

    try:
        if not gid or not mid:
            return True

        mids = [mid]
        result = delete_messages(client, gid, mids)
    except Exception as e:
        logger.warning(f"Delete message error: {e}", exc_info=True)

    return result


@threaded()
def delete_messages_globally(client: Client, uid: int, no_id: int = 0) -> bool:
    # Delete all messages from a user globally
    result = False

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

            should_delete = any(glovar.configs[gid].get(g) for g in ["gb", "gr", "gd"])

            if not glovar.configs[gid].get("delete", True) or not should_delete:
                continue

            thread(delete_all_messages, (client, gid, uid))

        result = True
    except Exception as e:
        logger.warning(f"Delete messages globally error: {e}", exc_info=True)

    return result


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


def get_description(client: Client, gid: int, cache: bool = True) -> str:
    # Get group's description
    result = ""
    try:
        group = get_group(client, gid, cache)

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

        if cache and the_cache:
            return the_cache

        result = get_chat(client, gid)

        if not result:
            return result

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

        if cache and the_cache:
            return the_cache

        result = get_chat_member(client, gid, uid)

        if not result:
            return result

        glovar.members[gid][uid] = result
    except Exception as e:
        logger.warning(f"Get member error: {e}", exc_info=True)

    return result


def get_pinned(client: Client, gid: int, cache: bool = True) -> Optional[Message]:
    # Get group's pinned message
    result = None

    try:
        group = get_group(client, gid, cache)

        if not group or not group.pinned_message:
            return None

        result = group.pinned_message
    except Exception as e:
        logger.warning(f"Get pinned error: {e}", exc_info=True)

    return result


def leave_group(client: Client, gid: int) -> bool:
    # Leave a group, clear it's data
    result = False

    try:
        glovar.left_group_ids.add(gid)
        save("left_group_ids")
        thread(leave_chat, (client, gid, True))

        glovar.lack_group_ids.discard(gid)
        save("lack_group_ids")

        glovar.admin_ids.pop(gid, set())
        save("admin_ids")

        glovar.trust_ids.pop(gid, set())
        save("trust_ids")

        glovar.configs.pop(gid, {})
        save("configs")

        glovar.declared_message_ids.pop(gid, set())
        glovar.members.pop(gid, {})
        glovar.recorded_ids.pop(gid, set())

        result = True
    except Exception as e:
        logger.warning(f"Leave group error: {e}", exc_info=True)

    return result


def save_admins(gid: int, admin_members: List[ChatMember]) -> bool:
    # Save the group's admin list
    result = False

    try:
        # Admin list
        glovar.admin_ids[gid] = {admin.user.id for admin in admin_members
                                 if (((not admin.user.is_bot and not admin.user.is_deleted)
                                      and admin.can_delete_messages
                                      and admin.can_restrict_members)
                                     or admin.status == "creator"
                                     or admin.user.id in glovar.bot_ids)}
        save("admin_ids")

        # Trust list
        glovar.trust_ids[gid] = {admin.user.id for admin in admin_members
                                 if ((not admin.user.is_bot and not admin.user.is_deleted)
                                     or admin.user.id in glovar.bot_ids)}
        save("trust_ids")

        result = True
    except Exception as e:
        logger.warning(f"Save admins error: {e}", exc_info=True)

    return result

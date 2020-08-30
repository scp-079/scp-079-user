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
from time import sleep
from typing import Iterable, Union

from pyrogram import ChatPermissions, Client, Message, User

from .. import glovar
from .channel import forward_evidence, send_debug, share_bad_user
from .decorators import threaded
from .etc import code, general_link, get_now, lang, thread
from .file import save
from .filters import is_class_d_user, is_declared_message
from .group import delete_message
from .ids import init_group_id, init_user_id
from .telegram import delete_all_messages, get_common_chats, get_group_info, kick_chat_member
from .telegram import restrict_chat_member, send_message, unban_chat_member

# Enable logging
logger = logging.getLogger(__name__)


def add_bad_user(client: Client, uid: int) -> bool:
    # Add a bad user, share it
    try:
        if uid in glovar.bad_ids["users"]:
            return True

        glovar.bad_ids["users"].add(uid)
        save("bad_ids")
        share_bad_user(client, uid)

        return True
    except Exception as e:
        logger.warning(f"Add bad user error: {e}", exc_info=True)

    return False


@threaded()
def ban_user(client: Client, gid: int, uid: Union[int, str], lock: bool = False) -> bool:
    # Ban a user
    result = False

    lock and glovar.locks["ban"].acquire()

    try:
        result = kick_chat_member(client, gid, uid)
    except Exception as e:
        logger.warning(f"Ban user error: {e}", exc_info=True)
    finally:
        lock and glovar.locks["ban"].release()

    return result


def ban_user_globally(client: Client, gid: int, uid: int) -> bool:
    # Ban a user globally
    try:
        # Debug text prefix
        text = f"{lang('project')}{lang('colon')}{general_link(glovar.project_name, glovar.project_link)}\n"

        # Get common chats
        chats = get_common_chats(client, uid)

        if not chats:
            return True

        for chat in chats:
            group_id = chat.id

            if group_id == gid:
                continue

            if not init_group_id(group_id):
                continue

            if (not glovar.configs[group_id].get("gb")
                    and not glovar.configs[group_id].get("gr")
                    and not glovar.configs[group_id].get("gd")):
                continue

            group_name, group_link = get_group_info(client, chat)
            text += (f"{lang('group_name')}{lang('colon')}{general_link(group_name, group_link)}\n"
                     f"{lang('group_id')}{lang('colon')}{code(group_id)}\n")

            # Global ban
            if glovar.configs[group_id].get("gb"):
                glovar.user_ids[uid]["ban"].add(group_id)
                ban_user(client, group_id, uid, True)
                glovar.configs[group_id].get("delete") and thread(delete_all_messages, (client, group_id, uid))
                text += f"{lang('action')}{lang('colon')}{code(lang('gb'))}\n"

            # Global restrict
            elif glovar.configs[group_id].get("gr"):
                if group_id in glovar.user_ids[uid]["restrict"]:
                    continue

                glovar.user_ids[uid]["restrict"].add(group_id)
                restrict_user(client, group_id, uid)
                glovar.configs[group_id].get("delete") and thread(delete_all_messages, (client, group_id, uid))
                text += f"{lang('action')}{lang('colon')}{code(lang('gr'))}\n"

            # Global delete
            elif glovar.configs[group_id].get("gd"):
                glovar.configs[group_id].get("delete") and thread(delete_all_messages, (client, group_id, uid))
                text += f"{lang('action')}{lang('colon')}{code(lang('gd'))}\n"

        if len(text.split("\n")) > 2:
            text += (f"{lang('user_id')}{lang('colon')}{code(uid)}\n"
                     f"{lang('rule')}{lang('colon')}{code(lang('rule_custom'))}\n")
            thread(send_message, (client, glovar.debug_channel_id, text))

        return True
    except Exception as e:
        logger.warning(f"Ban user globally error: {e}", exc_info=True)

    return False


@threaded()
def kick_user(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Kick a user
    result = False

    try:
        kick_chat_member(client, gid, uid)
        sleep(3)
        unban_chat_member(client, gid, uid)
        result = True
    except Exception as e:
        logger.warning(f"Kick user error: {e}", exc_info=True)

    return result


@threaded()
def kick_users(client: Client, gid: int, uids: Iterable[int]) -> bool:
    # Kick users
    result = False

    try:
        if not uids:
            return False

        for uid in uids:
            now = get_now()
            kick_chat_member(client, gid, uid, now + 600)

        result = True
    except Exception as e:
        logger.warning(f"Kick users error: {e}", exc_info=True)

    return result


@threaded()
def restrict_user(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Restrict a user
    result = False

    try:
        if uid in glovar.bad_ids["users"]:
            return True

        result = restrict_chat_member(client, gid, uid, ChatPermissions())
    except Exception as e:
        logger.warning(f"Restrict user error: {e}", exc_info=True)

    return result


def terminate_user(client: Client, message: Message, user: User, the_type: str) -> bool:
    # Delete user's message
    try:
        # Check if it is necessary
        if is_declared_message(None, message):
            return True

        gid = message.chat.id
        uid = user.id
        mid = message.message_id

        if not is_class_d_user(user):
            bad = True
        else:
            bad = False

        # Init user status
        if not init_user_id(uid):
            return True

        # Subscribe ban
        if the_type == "sb":
            if gid not in glovar.user_ids[uid]["ban"]:
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_ban"),
                    rule=lang(the_type)
                )

                if result:
                    bad and add_bad_user(client, uid)
                    glovar.user_ids[uid]["ban"].add(gid)
                    save("user_ids")
                    ban_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("auto_ban"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            else:
                delete_message(client, gid, mid)

        # Subscribe restrict
        elif the_type == "sr":
            if gid not in glovar.user_ids[uid]["restrict"]:
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_ban"),
                    rule=lang(the_type)
                )

                if result:
                    bad and add_bad_user(client, uid)
                    glovar.user_ids[uid]["restrict"].add(gid)
                    save("user_ids")
                    restrict_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("auto_ban"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            else:
                delete_message(client, gid, mid)

        # Subscribe delete
        elif the_type == "sd":
            if uid not in glovar.recorded_ids[gid]:
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_delete"),
                    rule=lang(the_type)
                )

                if result:
                    bad and add_bad_user(client, uid)
                    glovar.recorded_ids[gid].add(uid)
                    delete_message(client, gid, mid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("auto_delete"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            else:
                delete_message(client, gid, mid)

        # Scam
        elif the_type == "scam":
            if gid not in glovar.user_ids[uid]["ban"]:
                result = forward_evidence(
                    client=client,
                    message=message,
                    user=user,
                    level=lang("auto_ban"),
                    rule=lang(the_type)
                )

                if result:
                    bad and add_bad_user(client, uid)
                    glovar.user_ids[uid]["ban"].add(gid)
                    save("user_ids")
                    ban_user(client, gid, uid)
                    delete_message(client, gid, mid)
                    send_debug(
                        client=client,
                        chat=message.chat,
                        action=lang("auto_ban"),
                        uid=uid,
                        mid=mid,
                        em=result
                    )
            else:
                delete_message(client, gid, mid)

        return True
    except Exception as e:
        logger.warning(f"Terminate user error: {e}", exc_info=True)

    return False


def unban_user(client: Client, gid: int, uid: int) -> bool:
    # Unban a user
    try:
        thread(unban_chat_member, (client, gid, uid))

        return True
    except Exception as e:
        logger.warning(f"Unban user error: {e}", exc_info=True)

    return False


def unban_user_globally(client: Client, uid: int) -> bool:
    # Unban a user globally
    try:
        if not init_user_id(uid):
            return True

        for gid in list(glovar.user_ids[uid]["ban"]):
            glovar.user_ids[uid]["ban"].discard(gid)
            unban_user(client, gid, uid)

        for gid in list(glovar.user_ids[uid]["restrict"]):
            glovar.user_ids[uid]["restrict"].discard(gid)
            unrestrict_user(client, gid, uid)

        save("user_ids")

        return True
    except Exception as e:
        logger.warning(f"Unban user globally error: {e}", exc_info=True)

    return False


def unrestrict_user(client: Client, gid: int, uid: Union[int, str]) -> bool:
    # Unrestrict a user
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_stickers=True,
            can_send_animations=True,
            can_send_games=True,
            can_use_inline_bots=True,
            can_add_web_page_previews=True,
            can_send_polls=True,
            can_change_info=True,
            can_invite_users=True,
            can_pin_messages=True
        )
        thread(restrict_chat_member, (client, gid, uid, permissions))

        return True
    except Exception as e:
        logger.warning(f"Unrestrict user error: {e}", exc_info=True)

    return False

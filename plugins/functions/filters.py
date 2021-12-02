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
import re
from typing import Union

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, User

from .. import glovar
from .group import get_member
from .ids import init_group_id
from .telegram import resolve_username

# Enable logging
logger = logging.getLogger(__name__)


def is_aio(_, __) -> bool:
    # Check if the program is under all-in-one mode
    result = False

    try:
        result = glovar.aio
    except Exception as e:
        logger.warning(f"Is aio error: {e}", exc_info=True)

    return result


def is_authorized_group(_, update: Union[CallbackQuery, Message]) -> bool:
    # Check if the message is send from the authorized group
    try:
        if isinstance(update, CallbackQuery):
            message = update.message
        else:
            message = update

        if not message.chat:
            return False

        cid = message.chat.id

        if init_group_id(cid):
            return True
    except Exception as e:
        logger.warning(f"Is authorized group error: {e}", exc_info=True)

    return False


def is_captcha_group(_, update: Union[CallbackQuery, Message]) -> bool:
    # Check if the message is sent from the captcha group
    try:
        if isinstance(update, CallbackQuery):
            message = update.message
        else:
            message = update

        if not message.chat:
            return False

        cid = message.chat.id

        if cid == glovar.captcha_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is captcha group error: {e}", exc_info=True)

    return False


def is_class_c(_, message: Message) -> bool:
    # Check if the message is Class C personnel
    try:
        if not message.from_user:
            return False

        # Basic data
        uid = message.from_user.id
        gid = message.chat.id

        # Check permission
        if uid in glovar.admin_ids[gid] or uid in glovar.bot_ids or message.from_user.is_self:
            return True
    except Exception as e:
        logger.warning(f"Is class c error: {e}", exc_info=True)

    return False


def is_class_d(_, message: Message) -> bool:
    # Check if the message is Class D object
    try:
        if message.from_user:
            if is_class_d_user(message.from_user):
                return True

        if message.forward_from:
            fid = message.forward_from.id

            if fid in glovar.bad_ids["users"]:
                return True

        if message.forward_from_chat:
            cid = message.forward_from_chat.id

            if cid in glovar.bad_ids["channels"]:
                return True
    except Exception as e:
        logger.warning(f"Is class d error: {e}", exc_info=True)


def is_class_e(_, message: Message, test: bool = False) -> bool:
    # Check if the message is Class E object
    try:
        if message.from_user and not test:
            # The group's temp exception
            gid = message.chat.id
            uid = message.from_user.id

            if gid in glovar.except_ids["temp"].get(uid, set()):
                return True
    except Exception as e:
        logger.warning(f"Is class e error: {e}", exc_info=True)

    return False


def is_declared_message(_, message: Message) -> bool:
    # Check if the message is declared by other bots
    try:
        if not message.chat:
            return False

        gid = message.chat.id
        mid = message.message_id

        return is_declared_message_id(gid, mid)
    except Exception as e:
        logger.warning(f"Is declared message error: {e}", exc_info=True)

    return False


def is_exchange_channel(_, message: Message) -> bool:
    # Check if the message is sent from the exchange channel
    try:
        if not message.chat:
            return False

        cid = message.chat.id

        if glovar.should_hide:
            return cid == glovar.hide_channel_id
        else:
            return cid == glovar.exchange_channel_id
    except Exception as e:
        logger.warning(f"Is exchange channel error: {e}", exc_info=True)

    return False


def is_from_user(_, message: Message) -> bool:
    # Check if the message is sent from a user
    try:
        if message.from_user and message.from_user.id != 777000:
            return True
    except Exception as e:
        logger.warning(f"Is from user error: {e}", exc_info=True)

    return False


def is_hide_channel(_, message: Message) -> bool:
    # Check if the message is sent from the hide channel
    try:
        if not message.chat:
            return False

        cid = message.chat.id

        if cid == glovar.hide_channel_id:
            return True
    except Exception as e:
        logger.warning(f"Is hide channel error: {e}", exc_info=True)

    return False


def is_new_group(_, message: Message) -> bool:
    # Check if the bot joined a new group
    try:
        new_users = message.new_chat_members

        if new_users:
            return any(user.is_self for user in new_users)
        elif message.group_chat_created or message.supergroup_chat_created:
            return True
    except Exception as e:
        logger.warning(f"Is new group error: {e}", exc_info=True)

    return False


def is_test_group(_, update: Union[CallbackQuery, Message]) -> bool:
    # Check if the message is sent from the test group
    try:
        if isinstance(update, CallbackQuery):
            message = update.message
        else:
            message = update

        if not message.chat:
            return False

        cid = message.chat.id

        if cid == glovar.test_group_id:
            return True
    except Exception as e:
        logger.warning(f"Is test group error: {e}", exc_info=True)

    return False


aio = filters.create(
    func=is_aio,
    name="AIO"
)

authorized_group = filters.create(
    func=is_authorized_group,
    name="Authorized Group"
)

captcha_group = filters.create(
    func=is_captcha_group,
    name="CAPTCHA Group"
)

class_c = filters.create(
    func=is_class_c,
    name="Class C"
)

class_d = filters.create(
    func=is_class_d,
    name="Class D"
)

class_e = filters.create(
    func=is_class_e,
    name="Class E"
)

declared_message = filters.create(
    func=is_declared_message,
    name="Declared message"
)

exchange_channel = filters.create(
    func=is_exchange_channel,
    name="Exchange Channel"
)

from_user = filters.create(
    func=is_from_user,
    name="From User"
)

hide_channel = filters.create(
    func=is_hide_channel,
    name="Hide Channel"
)

new_group = filters.create(
    func=is_new_group,
    name="New Group"
)

test_group = filters.create(
    func=is_test_group,
    name="Test Group"
)


def is_class_d_user(user: Union[int, User]) -> bool:
    # Check if the user is a Class D personnel
    try:
        if isinstance(user, int):
            uid = user
        else:
            uid = user.id

        if uid in glovar.bad_ids["users"]:
            return True
    except Exception as e:
        logger.warning(f"Is class d user error: {e}", exc_info=True)

    return False


def is_class_e_user(user: Union[int, User]) -> bool:
    # Check if the user is a Class E personnel
    try:
        if isinstance(user, int):
            uid = user
        else:
            uid = user.id

        if uid in glovar.bot_ids:
            return True

        group_list = list(glovar.trust_ids)

        for gid in group_list:
            if uid in glovar.trust_ids.get(gid, set()):
                return True
    except Exception as e:
        logger.warning(f"Is class e user error: {e}", exc_info=True)

    return False


def is_declared_message_id(gid: int, mid: int) -> bool:
    # Check if the message's ID is declared by other bots
    try:
        if mid in glovar.declared_message_ids.get(gid, set()):
            return True
    except Exception as e:
        logger.warning(f"Is declared message id error: {e}", exc_info=True)

    return False


def is_friend_username(client: Client, gid: int, username: str, friend: bool, friend_user: bool = False) -> bool:
    # Check if it is a friend username
    try:
        username = username.strip()

        if not username:
            return False

        if username[0] != "@":
            username = "@" + username

        if not re.search(r"\B@([a-z][0-9a-z_]{4,31})", username, re.I | re.M | re.S):
            return False

        peer_type, peer_id = resolve_username(client, username)

        if peer_type == "channel":
            if friend or glovar.configs[gid].get("friend"):
                if peer_id in glovar.except_ids["channels"] or glovar.admin_ids.get(peer_id, {}):
                    return True

        if peer_type == "user":
            if friend and friend_user:
                return True

            if friend or glovar.configs[gid].get("friend"):
                if is_class_e_user(peer_id):
                    return True

            member = get_member(client, gid, peer_id)

            if member and member.status in {"creator", "administrator", "member"}:
                return True
    except Exception as e:
        logger.warning(f"Is friend username: {e}", exc_info=True)

    return False


def is_high_score_user(user: User) -> float:
    # Check if the message is sent by a high score user
    try:
        if is_class_e_user(user):
            return 0.0

        uid = user.id
        user_status = glovar.user_ids.get(uid, {})

        if not user_status:
            return 0.0

        score = sum(user_status["score"].values())

        if score >= 3.0:
            return score
    except Exception as e:
        logger.warning(f"Is high score user error: {e}", exc_info=True)

    return 0.0


def is_not_allowed(message: Message) -> str:
    # Check if the message is not allowed in the group
    try:
        # Basic data
        gid = message.chat.id

        # Subscribe ban
        if glovar.configs[gid].get("sb"):
            return "sb"

        # Subscribe restrict
        if glovar.configs[gid].get("sr"):
            return "sr"

        # Subscribe delete
        if glovar.configs[gid].get("sd"):
            return "sd"
    except Exception as e:
        logger.warning(f"Is not allowed error: {e}", exc_info=True)

    return ""


def is_watch_user(user: User, the_type: str, now: int) -> bool:
    # Check if the message is sent by a watch user
    try:
        if is_class_e_user(user):
            return False

        uid = user.id
        until = glovar.watch_ids[the_type].get(uid, 0)

        if now < until:
            return True
    except Exception as e:
        logger.warning(f"Is watch user error: {e}", exc_info=True)

    return False

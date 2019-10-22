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
from typing import Generator, Iterable, List, Optional, Union

from pyrogram import Chat, ChatMember, ChatPreview, Client, InlineKeyboardMarkup, Message
from pyrogram.api.functions.channels import DeleteUserHistory
from pyrogram.api.functions.messages import ReadMentions
from pyrogram.api.types import InputPeerUser, InputPeerChannel
from pyrogram.errors import ChannelInvalid, ChannelPrivate, FloodWait, PeerIdInvalid
from pyrogram.errors import UsernameInvalid, UsernameNotOccupied

from .. import glovar
from .etc import delay, get_int, wait_flood

# Enable logging
logger = logging.getLogger(__name__)


def archive_chats(client: Client, cids: List[Union[int, str]]) -> Optional[bool]:
    # Archive chats
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.archive_chats(chat_ids=cids)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Archive chats error: {e}", exc_info=True)

    return result


def delete_messages(client: Client, cid: int, mids: Iterable[int]) -> Optional[bool]:
    # Delete some messages
    result = None
    try:
        mids = list(mids)
        mids_list = [mids[i:i + 100] for i in range(0, len(mids), 100)]
        for mids in mids_list:
            try:
                flood_wait = True
                while flood_wait:
                    flood_wait = False
                    try:
                        result = client.delete_messages(chat_id=cid, message_ids=mids)
                    except FloodWait as e:
                        flood_wait = True
                        wait_flood(e)
            except Exception as e:
                logger.warning(f"Delete message in {cid} for loop error: {e}", exc_info=True)
    except Exception as e:
        logger.warning(f"Delete messages in {cid} error: {e}", exc_info=True)

    return result


def delete_all_messages(client: Client, gid: int, uid: int) -> bool:
    # Delete a user's all messages in a group
    try:
        group_id = resolve_peer(client, gid)
        user_id = resolve_peer(client, uid)
        if group_id and user_id:
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    client.send(DeleteUserHistory(channel=group_id, user_id=user_id))
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)

        return True
    except Exception as e:
        logger.warning('Delete user all message error: %s', e)

    return False


def download_media(client: Client, file_id: str, file_ref: str, file_path: str):
    # Download a media file
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.download_media(message=file_id, file_ref=file_ref, file_name=file_path)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Download media {file_id} to {file_path} error: {e}", exc_info=True)

    return result


def get_admins(client: Client, cid: int) -> Optional[Union[bool, List[ChatMember]]]:
    # Get a group's admins
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.get_chat_members(chat_id=cid, filter="administrators")
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Get admins in {cid} error: {e}", exc_info=True)

    return result


def get_common_chats(client: Client, uid: int) -> Optional[List[Chat]]:
    # Get the common chats with a user
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.get_common_chats(user_id=uid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Get common chats error: {e}", exc_info=True)

    return result


def get_chat(client: Client, cid: Union[int, str]) -> Optional[Union[Chat, ChatPreview]]:
    # Get a chat
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.get_chat(chat_id=cid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Get chat error: {e}", exc_info=True)

    return result


def get_group_info(client: Client, chat: Union[int, Chat]) -> (str, str):
    # Get a group's name and link
    group_name = "Unknown Group"
    group_link = glovar.default_group_link
    try:
        if isinstance(chat, int):
            result = None
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    result = client.get_chat(chat_id=chat)
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)
                except Exception as e:
                    logger.info(f"Get chat {chat} error: {e}", exc_info=True)

            chat = result

        if chat.title:
            group_name = chat.title

        if chat.username:
            group_link = "https://t.me/" + chat.username
    except Exception as e:
        logger.info(f"Get group info error: {e}", exc_info=True)

    return group_name, group_link


def get_members(client: Client, cid: int, query: str = "all") -> Optional[Generator[ChatMember, None, None]]:
    # Get a members generator of a chat
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.iter_chat_members(chat_id=cid, filter=query)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Get members in {cid} error: {e}", exc_info=True)

    return result


def kick_chat_member(client: Client, cid: int, uid: Union[int, str]) -> Optional[Union[bool, Message]]:
    # Kick a chat member in a group
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.kick_chat_member(chat_id=cid, user_id=uid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Kick chat member {uid} in {cid} error: {e}", exc_info=True)

    return result


def leave_chat(client: Client, cid: int) -> bool:
    # Leave a channel
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                client.leave_chat(chat_id=cid, delete=True)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)

        return True
    except Exception as e:
        logger.warning(f"Leave chat {cid} error: {e}", exc_info=True)

    return False


def read_history(client: Client, cid: int) -> bool:
    # Mark messages in a chat as read
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                client.read_history(chat_id=cid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)

        return True
    except Exception as e:
        logger.warning(f"Read history error: {e}", exc_info=True)

    return False


def read_mention(client: Client, cid: int) -> bool:
    # Mark a mention as read
    try:
        peer = resolve_peer(client, cid)
        if peer:
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    client.send(ReadMentions(peer=peer))
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)

            return True
    except Exception as e:
        logger.warning(f"Read mention error: {e}", exc_info=True)

    return False


def resolve_peer(client: Client, pid: Union[int, str]) -> Optional[Union[bool, InputPeerChannel, InputPeerUser]]:
    # Get an input peer by id
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.resolve_peer(pid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except (PeerIdInvalid, UsernameInvalid, UsernameNotOccupied):
                return False
    except Exception as e:
        logger.warning(f"Resolve peer error: {e}", exc_info=True)

    return result


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


def send_document(client: Client, cid: int, document: str, file_ref: str = None, text: str = None, mid: int = None,
                  markup: InlineKeyboardMarkup = None) -> Optional[Union[bool, Message]]:
    # Send a document to a chat
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.send_document(
                    chat_id=cid,
                    document=document,
                    file_ref=file_ref,
                    caption=text,
                    parse_mode="html",
                    reply_to_message_id=mid,
                    reply_markup=markup
                )
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
            except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                return False
    except Exception as e:
        logger.warning(f"Send document to {cid} error: {e}", exec_info=True)

    return result


def send_message(client: Client, cid: int, text: str, mid: int = None,
                 markup: InlineKeyboardMarkup = None) -> Optional[Union[bool, Message]]:
    # Send a message to a chat
    result = None
    try:
        if text.strip():
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    result = client.send_message(
                        chat_id=cid,
                        text=text,
                        parse_mode="html",
                        disable_web_page_preview=True,
                        reply_to_message_id=mid,
                        reply_markup=markup
                    )
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)
                except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                    return False
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result


def send_photo(client: Client, cid: int, photo: str, file_ref: str = None, text: str = None, mid: int = None,
               markup: InlineKeyboardMarkup = None) -> Optional[Union[bool, Message]]:
    # Send a photo to a chat
    result = None
    try:
        if photo.strip():
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    result = client.send_photo(
                        chat_id=cid,
                        photo=photo,
                        file_ref=file_ref,
                        caption=text,
                        parse_mode="html",
                        reply_to_message_id=mid,
                        reply_markup=markup
                    )
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)
                except (PeerIdInvalid, ChannelInvalid, ChannelPrivate):
                    return False
    except Exception as e:
        logger.warning(f"Send photo to {cid} error: {e}", exc_info=True)

    return result


def send_report_message(secs: int, client: Client, cid: int, text: str, mid: int = None,
                        markup: InlineKeyboardMarkup = None) -> Optional[Message]:
    # Send a message that will be auto deleted to a chat
    result = None
    try:
        if text.strip():
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    result = client.send_message(
                        chat_id=cid,
                        text=text,
                        parse_mode="html",
                        disable_web_page_preview=True,
                        reply_to_message_id=mid,
                        reply_markup=markup
                    )
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)

            mid = result.message_id
            mids = [mid]
            delay(secs, delete_messages, [client, cid, mids])
    except Exception as e:
        logger.warning(f"Send message to {cid} error: {e}", exc_info=True)

    return result


def unban_chat_member(client: Client, cid: int, uid: Union[int, str]) -> Optional[bool]:
    # Unban a user in a group
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.unban_chat_member(chat_id=cid, user_id=uid)
            except FloodWait as e:
                flood_wait = True
                wait_flood(e)
    except Exception as e:
        logger.warning(f"Unban chat member {uid} in {cid} error: {e}", exc_info=True)

    return result

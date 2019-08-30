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
from struct import pack
from typing import Iterable, List, Optional, Union

from pyrogram import Chat, ChatMember, Client, InlineKeyboardMarkup, Message
from pyrogram.api.functions.channels import DeleteUserHistory
from pyrogram.api.functions.messages import GetCommonChats, GetWebPagePreview, ReadMentions
from pyrogram.api.types import InputPeerUser, InputPeerChannel, MessageMediaPhoto, MessageMediaWebPage, Photo, WebPage
from pyrogram.client.ext.utils import encode
from pyrogram.errors import ChannelInvalid, ChannelPrivate, FloodWait, PeerIdInvalid, UsernameInvalid

from .. import glovar
from .etc import delay, get_text, wait_flood

# Enable logging
logger = logging.getLogger(__name__)


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
                logger.warning(f"Delete message in for loop error: {e}", exc_info=True)
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


def download_media(client: Client, file_id: str, file_path: str):
    # Download a media file
    result = None
    try:
        flood_wait = True
        while flood_wait:
            flood_wait = False
            try:
                result = client.download_media(message=file_id, file_name=file_path)
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
    # Get the common groups with a user
    result = None
    try:
        user_id = resolve_peer(client, uid)
        if user_id:
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    chats = client.send(GetCommonChats(
                        user_id=user_id,
                        max_id=0,
                        limit=len(glovar.configs))
                    )
                    result = chats.chats
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)
    except Exception as e:
        logger.warning(f"Get common chats error: {e}", exc_info=True)

    return result


def get_chat(client: Client, cid: Union[int, str]) -> Optional[Chat]:
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


def get_preview(client: Client, message: Message) -> dict:
    # Get message's preview
    preview = {
        "url": None,
        "text": None,
        "image": None
    }
    try:
        if should_preview(message):
            result = None
            message_text = get_text(message)
            flood_wait = True
            while flood_wait:
                flood_wait = False
                try:
                    result = client.send(GetWebPagePreview(message=message_text))
                except FloodWait as e:
                    flood_wait = True
                    wait_flood(e)

            if result:
                photo = None
                if isinstance(result, MessageMediaWebPage):
                    web_page = result.webpage
                    if isinstance(web_page, WebPage):
                        text = ""
                        if web_page.url:
                            preview["url"] = web_page.url

                        if web_page.display_url:
                            text += web_page.display_url + "\n\n"

                        if web_page.site_name:
                            text += web_page.site_name + "\n\n"

                        if web_page.title:
                            text += web_page.title + "\n\n"

                        if web_page.description:
                            text += web_page.description + "\n\n"

                        preview["text"] = text.strip()
                        if web_page.photo:
                            if isinstance(web_page.photo, Photo):
                                photo = web_page.photo
                elif isinstance(result, MessageMediaPhoto):
                    media = result.photo
                    if isinstance(media, Photo):
                        photo = media

                # See: github.com/pyrogram/pyrogram/blob/develop/pyrogram/client/types/messages_and_media/photo.py#L81
                if photo:
                    big = photo.sizes[-1]
                    if big.size <= glovar.image_size:
                        file_id = encode(
                            pack(
                                "<iiqqc",
                                2, photo.dc_id,
                                photo.id, photo.access_hash,
                                big.type.encode()
                            )
                        )
                        preview["image"] = file_id
    except Exception as e:
        logger.warning(f"Get preview error: {e}", exc_info=True)

    return preview


def kick_chat_member(client: Client, cid: int, uid: int) -> Optional[Union[bool, Message]]:
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
            except UsernameInvalid:
                return False
    except Exception as e:
        logger.warning(f"Resolve peer error: {e}", exc_info=True)

    return result


def send_document(client: Client, cid: int, file: str, text: str = None, mid: int = None,
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
                    document=file,
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


def send_photo(client: Client, cid: int, photo: str, caption: str = None, mid: int = None,
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
                        caption=caption,
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


def should_preview(message: Message) -> bool:
    # Check if the message should be previewed
    if message.entities or message.caption_entities:
        if message.entities:
            entities = message.entities
        else:
            entities = message.caption_entities

        for en in entities:
            if en.type in ["url", "text_link"]:
                return True

    return False


def unban_chat_member(client: Client, cid: int, uid: int) -> Optional[bool]:
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
        logger.warning(f"Unban chat member {uid} in {cid} error: {e}")

    return result

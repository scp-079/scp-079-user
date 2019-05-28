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

from pyrogram import Client, Message

from .etc import code_block, thread, user_mention
from .telegram import get_preview, send_message, send_photo

# Enable logging
logger = logging.getLogger(__name__)


def preview_test(client: Client, message: Message) -> bool:
    # Test preview
    try:
        preview, url = get_preview(client, message)
        if preview["file_id"] or preview["text"]:
            cid = message.chat.id
            aid = message.from_user.id
            mid = message.message_id
            text = f"管理员：{user_mention(aid)}\n\n"
            if url:
                text += "触发链接：" + "-" * 24 + "\n\n" + code_block(url) + "\n"

            if preview["text"]:
                text += "预览文字：" + "-" * 24 + "\n\n" + code_block(preview["text"]) + "\n"

            if preview["file_id"]:
                thread(send_photo, (client, cid, preview["file_id"], text, mid))
            else:
                thread(send_message, (client, cid, text, mid))

    except Exception as e:
        logger.warning(f"Preview test error: {e}", exc_info=True)

    return False

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

from pyrogram import Client, Message, WebPage

from .etc import code, code_block, get_text, thread, user_mention
from .telegram import send_message, send_photo

# Enable logging
logger = logging.getLogger(__name__)


def preview_test(client: Client, message: Message) -> bool:
    # Test preview
    try:
        if message.web_page:
            web_page: WebPage = message.web_page
            url = web_page.url
            cid = message.chat.id
            aid = message.from_user.id
            mid = message.message_id
            text = f"管理员：{user_mention(aid)}\n\n"
            text += "触发链接：" + "-" * 24 + "\n\n" + code(url) + "\n\n"
            text += "原始消息：" + "-" * 24 + "\n\n" + code_block(get_text(message)) + "\n\n"
            text += "预览内容：" + "-" * 24 + "\n\n"
            text += code(web_page.display_url) + "\n\n"

            if web_page.site_name:
                text += code(web_page.site_name) + "\n\n"

            if web_page.title:
                text += code(web_page.title) + "\n\n"

            if web_page.description:
                text += code(web_page.description) + "\n\n"

            if web_page.photo:
                file_id = web_page.photo.file_id
                thread(send_photo, (client, cid, file_id, text, mid))
            else:
                thread(send_message, (client, cid, text, mid))

    except Exception as e:
        logger.warning(f"Preview test error: {e}", exc_info=True)

    return False

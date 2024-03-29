# SCP-079-USER - Invite and help other bots
# Copyright (C) 2019-2023 SCP-079 <https://scp-079.org>
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
from os import remove
from os.path import exists
from pickle import dump
from shutil import copyfile
from typing import Any

from pyAesCrypt import decryptFile, encryptFile
from pyrogram import Client

from .. import glovar
from .decorators import threaded
from .etc import random_str
from .telegram import download_media

# Enable logging
logger = logging.getLogger(__name__)


def crypt_file(operation: str, file_in: str, file_out: str) -> bool:
    # Encrypt or decrypt a file
    try:
        if not file_in or not file_out:
            return True

        buffer_ = 64 * 1024

        if operation == "decrypt":
            decryptFile(file_in, file_out, glovar.password, buffer_)
        else:
            encryptFile(file_in, file_out, glovar.password, buffer_)

        return True
    except Exception as e:
        logger.warning(f"Crypt file error: {e}", exc_info=True)

    return False


def data_to_file(data: Any) -> str:
    # Save data to a file in tmp directory
    try:
        file_path = get_new_path()

        with open(file_path, "wb") as f:
            dump(data, f)

        return file_path
    except Exception as e:
        logger.warning(f"Data to file error: {e}", exc_info=True)

    return ""


def delete_file(path: str) -> bool:
    # Delete a file
    try:
        if path and exists(path):
            remove(path)

        return True
    except Exception as e:
        logger.warning(f"Delete file error: {e}", exc_info=True)

    return False


def get_downloaded_path(client: Client, file_id: str) -> str:
    # Download file, get it's path on local machine
    final_path = ""
    try:
        if not file_id:
            return ""

        file_path = get_new_path()
        final_path = download_media(client, file_id, file_path)
    except Exception as e:
        logger.warning(f"Get downloaded path error: {e}", exc_info=True)

    return final_path


def get_new_path(extension: str = "", prefix: str = "") -> str:
    # Get a new path in tmp directory
    result = ""
    try:
        file_path = random_str(8)

        while exists(f"tmp/{prefix}{file_path}{extension}"):
            file_path = random_str(8)

        result = f"tmp/{prefix}{file_path}{extension}"
    except Exception as e:
        logger.warning(f"Get new path error: {e}", exc_info=True)

    return result


@threaded(daemon=False)
def save(file: str) -> bool:
    # Save a global variable to a file
    result = False

    try:
        if not glovar:
            return False

        with open(f"data/.{file}", "wb") as f:
            dump(eval(f"glovar.{file}"), f)

        result = copyfile(f"data/.{file}", f"data/{file}") or True
    except Exception as e:
        logger.warning(f"Save error: {e}", exc_info=True)

    return result

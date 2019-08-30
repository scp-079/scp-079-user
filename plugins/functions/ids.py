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
from copy import deepcopy

from .. import glovar
from .file import save

# Enable logging
logger = logging.getLogger(__name__)


def init_group_id(gid: int) -> bool:
    # Init group data
    try:
        if glovar.admin_ids.get(gid) is None:
            glovar.admin_ids[gid] = set()
            save("admin_ids")

        if glovar.configs.get(gid) is None:
            glovar.configs[gid] = deepcopy(glovar.default_config)
            save("configs")

        if glovar.declared_message_ids.get(gid) is None:
            glovar.declared_message_ids[gid] = set()

        if glovar.recorded_ids.get(gid) is None:
            glovar.recorded_ids[gid] = set()

        return True
    except Exception as e:
        logger.warning(f"Init group id {gid} error: {e}", exc_info=True)

    return False


def init_user_id(uid: int) -> bool:
    # Init user data
    try:
        if glovar.banned_ids.get(uid) is None:
            glovar.banned_ids[uid] = set()
            save("banned_ids")

        if glovar.except_ids["temp"].get(uid) is None:
            glovar.except_ids["temp"][uid] = set()
            save("except_ids")

        return True
    except Exception as e:
        logger.warning(f"Init user id {uid} error: {e}", exc_info=True)

    return False

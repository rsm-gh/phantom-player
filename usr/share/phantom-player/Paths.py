#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of either:
#
#   - the GNU Lesser General Public License as published by
#     the Free Software Foundation, version 2.1 only, or
#
#   - the GNU General Public License as published by
#     the Free Software Foundation, version 3 only.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the applicable licenses for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# version 2.1 and the GNU General Public License version 3
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-2.1-only OR GPL-3.0-only

import os
import sys
import getpass

import system_utils

__SRC_DIR = os.path.dirname(os.path.abspath(__file__))
__IMG_DIR = system_utils.join_path(__SRC_DIR, "view/img")

# Icons
_ICON_LOGO_SMALL = system_utils.join_path(__IMG_DIR, "phantom-player-32.png")
_ICON_LOGO_BIG = system_utils.join_path(__IMG_DIR, "phantom-player-250.png")

# Files
if 'linux' in sys.platform:

    if getpass.getuser() == "root":
        _HOME_DIR = "/root"
    else:
        _HOME_DIR = system_utils.join_path("/home", getpass.getuser())

    _APP_DIR = system_utils.join_path(_HOME_DIR, ".local/share/phantom-player")
    _SERIES_DIR = _APP_DIR
    _NEW_PLAYLIST_IMG_PATH = system_utils.join_path(_SERIES_DIR, ".png")
    _CONF_FILE = system_utils.join_path(_HOME_DIR, ".config/phantom-player.ini")

elif sys.platform == 'win32':
    _HOME_DIR = system_utils.join_path(r"C:\Users", getpass.getuser())
    _APP_DIR = system_utils.join_path(_HOME_DIR, r"AppData\Local\PhantomPlayer")
    _SERIES_DIR = system_utils.join_path(_APP_DIR, "Playlists")
    _NEW_PLAYLIST_IMG_PATH = system_utils.join_path(_SERIES_DIR, ".png")
    _CONF_FILE = system_utils.join_path(_APP_DIR, "phantom-player.ini")

else:
    raise ValueError('Unsupported platform', sys.platform)


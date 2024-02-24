#!/usr/bin/python3
#

#  Copyright (C) 2014-2015, 2024 Rafael Senties Martinelli.
#
#  This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License 3 as published by
#   the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import getpass

__SRC_DIR = os.path.dirname(os.path.abspath(__file__))
__IMG_DIR = os.path.join(__SRC_DIR, "view/img")

# Icons
_ICON_LOGO_SMALL = os.path.join(__IMG_DIR, "movie-icon-small.png")
_ICON_LOGO_MEDIUM = os.path.join(__IMG_DIR, "movie-icon-medium.png")
_ICON_LOGO_BIG = os.path.join(__IMG_DIR, "movie-icon-big.png")

# Files
if getpass.getuser() == "root":
    _HOME_DIR = "/root"
else:
    _HOME_DIR = "/home/" + getpass.getuser()

_SERIES_DIR = os.path.join(_HOME_DIR, ".local/share/phantom-player")
_CONF_FILE = os.path.join(_HOME_DIR,  ".config/phantom-player.ini")

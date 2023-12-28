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

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SRC_DIR, "view/img")

# Icons
ICON_LOGO_SMALL = os.path.join(IMG_DIR, "movie-icon-small.png")
ICON_LOGO_MEDIUM = os.path.join(IMG_DIR, "movie-icon-medium.png")
ICON_LOGO_BIG = os.path.join(IMG_DIR, "movie-icon-big.png")

ICON_ERROR = os.path.join(IMG_DIR, "error.png")
ICON_ERROR_BIG = os.path.join(IMG_DIR, "error-big.png")
ICON_CHECK = os.path.join(IMG_DIR, "check.png")
ICON_ADD = os.path.join(IMG_DIR, "add.png")

# Files
if getpass.getuser() == "root":
    HOME_PATH = "/root"
else:
    HOME_PATH = "/home/" + getpass.getuser()

FOLDER_LIST_PATH = os.path.join(HOME_PATH, ".local/share/vlist-player")
CONFIGURATION_FILE = os.path.join(HOME_PATH,  ".config/vlist-player.ini")
GLADE_FILE = os.path.join(SRC_DIR, "view/vlist-player.glade")
SERIES_PATH = FOLDER_LIST_PATH + '''/{0}.csv'''

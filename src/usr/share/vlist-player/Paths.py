#!/usr/bin/python3
#

#  Copyright (C) 2014-2015  Rafael Senties Martinelli 
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
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA.

import getpass

# Icons

ICON_LOGO_SMALL="./images/movie-icon-small.png"
ICON_LOGO_MEDIUM="./images/movie-icon-medium.png"
ICON_LOGO_BIG="./images/movie-icon-big.png"

ICON_ERROR="./images/error.png"
ICON_ERROR_BIG="./images/error-big.png"
ICON_CHECK="./images/check.png"
ICON_ADD="./images/add.png"


# Files
if getpass.getuser()=="root":
	HOME_PATH="/root"
	FOLDER_LIST_PATH=HOME_PATH+".local/share/vlist-player"
	CONFIGURATION_FILE=HOME_PATH+"/.config/vlist-player.ini"
else:
	HOME_PATH="/home/"+getpass.getuser()
	FOLDER_LIST_PATH=HOME_PATH+"/.local/share/vlist-player"
	CONFIGURATION_FILE=HOME_PATH+"/.config/vlist-player.ini"


GLADE_FILE="./vlist-player.glade"
SERIE_PATH=FOLDER_LIST_PATH+'''/{0}.csv'''





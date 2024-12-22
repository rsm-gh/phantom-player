#!/bin/bash

#
# GPL License
#
#  Copyright (C) 2015, 2024 Rafael Senties Martinelli.
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
#  You should have received a copy of the GNU General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.


if [ "$EUID" -ne 0 ]
  then echo "Please run as root."
  exit
fi

function remove_file(){

    if [ -f "$1" ]; then
        rm -f "$1"
        echo "removed.f: $1"
    fi
}

function remove_dir(){

    if [ -d "$1" ]; then
        rm -rf "$1"
        echo "removed.d: $1"
    fi
}

remove_dir "/usr/share/phantom-player"
remove_dir "/usr/share/doc/phantom-player"
remove_file "/usr/share/applications/com.senties-martinelli.PhantomPlayer.desktop"
remove_file "/usr/bin/phantom-player"

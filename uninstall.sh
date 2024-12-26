#!/bin/bash

#
# Public domain.
#
#
# uninstall.sh by Rafael Senties Martinelli.
#
# To the extent possible under law, the person who associated CC0 with
# uninstall.sh has waived all copyright and related or neighboring rights
# to uninstall.sh.
#
# You should have received a copy of the CC0 legalcode along with this
# work.  If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.


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

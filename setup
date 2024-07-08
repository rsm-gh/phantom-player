#!/bin/bash

#
# GPL License
#
#  Copyright (C) 2015, 2024 Rafael Senties Martinelli.
#
#  This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License 3 as published by
#   the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.

if [ "$EUID" -ne 0 ]
  then echo "Please run as root."
  exit
fi

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "$DIR" || exit

#
# Set the scripts permissions
#
chmod a+x ./remove

#
# Remove previous versions
#
echo -e "Removing previous versions..."
./remove

#
# Install the new files
#
echo -e "\nInstalling the software files..."

function install_files(){

    echo "installing: $1"

    if [ -d "$DIR$1/__pycache__" ]; then
      rm -rf "$DIR$1/__pycache__"
    fi

    install -d "$1" |& grep -v "omitting directory"
    install -D "$DIR$1/"* "$1" |& grep -v "omitting directory"

}

install_files "/usr/bin"
install_files "/usr/share/applications"
install_files "/usr/share/doc/phantom-player"
install_files "/usr/share/phantom-player"
install_files "/usr/share/phantom-player/controller"
install_files "/usr/share/phantom-player/model"
install_files "/usr/share/phantom-player/view"
install_files "/usr/share/phantom-player/view/img"
install_files "/usr/share/phantom-player/view/cellrenderers"

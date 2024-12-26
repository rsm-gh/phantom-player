#!/bin/bash

#
# Public domain.
#
#
# install.sh by Rafael Senties Martinelli.
#
# To the extent possible under law, the person who associated CC0 with
# install.sh has waived all copyright and related or neighboring rights
# to install.sh.
#
# You should have received a copy of the CC0 legalcode along with this
# work.  If not, see <https://creativecommons.org/publicdomain/zero/1.0/>.

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

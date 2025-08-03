#!/bin/bash

#
# This file is part of Phantom Player.
#
#  Copyright (C) 2025 Rafael Senties Martinelli.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root."
  exit 1
fi

DIR=$(cd "$(dirname "$0")" && pwd)

echo "Removing previous versions..."
chmod a+x "$DIR/uninstall_bsd.sh"
/bin/sh "$DIR/uninstall_bsd.sh"

#
# Install the new files
#
echo "Installing the software files..."

install_files() {

	echo "installing: $1"

	if [ -d "$DIR$1/__pycache__" ]; then
	rm -rf "$DIR$1/__pycache__"
	fi

	mkdir -p "$1"

	cp -Rp "$DIR$1/"* "$1/" 2>&1 | grep -v "omitting directory"
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

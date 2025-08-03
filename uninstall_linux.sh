#!/bin/bash

#
# This file is part of Phantom Player.
#
#  Copyright (C) 2015, 2024 Rafael Senties Martinelli.
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

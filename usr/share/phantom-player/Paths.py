#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
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

import os
import sys
import getpass

__SRC_DIR = os.path.dirname(os.path.abspath(__file__))
__IMG_DIR = os.path.join(__SRC_DIR, "view/img")

# Icons
_ICON_LOGO_SMALL = os.path.join(__IMG_DIR, "movie-icon-small.png")
_ICON_LOGO_MEDIUM = os.path.join(__IMG_DIR, "movie-icon-medium.png")
_ICON_LOGO_BIG = os.path.join(__IMG_DIR, "movie-icon-big.png")
_ICON_LOADING_PLAYLIST = os.path.join(__IMG_DIR, "loading-playlist.png")

# Files
if 'linux' in sys.platform:

    if getpass.getuser() == "root":
        _HOME_DIR = "/root"
    else:
        _HOME_DIR = os.path.join("/home", getpass.getuser())

    _APP_DIR = os.path.join(_HOME_DIR, ".local/share/phantom-player")
    _SERIES_DIR = _APP_DIR
    _NEW_PLAYLIST_IMG_PATH = os.path.join(_SERIES_DIR, ".png")
    _CONF_FILE = os.path.join(_HOME_DIR, ".config/phantom-player.ini")

elif sys.platform == 'win32':
    _HOME_DIR = os.path.join(r"C:\Users", getpass.getuser())
    _APP_DIR = os.path.join(_HOME_DIR, r"AppData\Local\PhantomPlayer")
    _SERIES_DIR = os.path.join(_APP_DIR, "Series")
    _NEW_PLAYLIST_IMG_PATH = os.path.join(_SERIES_DIR, ".png")
    _CONF_FILE = os.path.join(_APP_DIR, "phantom-player.ini")

else:
    raise ValueError('Unsupported platform', sys.platform)


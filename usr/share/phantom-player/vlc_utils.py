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
import vlc
import sys
import time

from console_printer import print_info, print_debug
print_info(f"python-vlc version: {vlc.__version__}, generator: {vlc.__generator_version__}, build date:{vlc.build_date}")

import faulthandler
faulthandler.enable()

# Create a single vlc.Instance() to be shared by (possible) multiple players.
__VLC_INSTANCE: None | vlc.Instance = None

def get_instance() -> vlc.Instance:
    global __VLC_INSTANCE

    if __VLC_INSTANCE is None:
        if 'linux' in sys.platform:
            # Inform libvlc that Xlib is not initialized for threads
            __VLC_INSTANCE = vlc.Instance("--no-xlib")
        else:
            __VLC_INSTANCE = vlc.Instance()

        print_debug(f"VLC instance: {__VLC_INSTANCE}")

    return __VLC_INSTANCE

def get_video_duration(path: str) -> int:
    """Get the duration of a video in seconds."""
    if not os.path.exists(path):
        return 0

    media = parse_file(path)
    while media.get_parsed_status() == 0:
        time.sleep(.1)

    duration = media.get_duration()

    media.release()

    if duration <= 1:
        return 0

    return int(duration / 1000)

def parse_file(path: str, timeout: int=3000) -> vlc.Media:
    media = get_instance().media_new_path(path)
    media.parse_with_options(vlc.MediaParseFlag.local, timeout)
    return media

def release_instance() -> None:
    global __VLC_INSTANCE

    print_debug(f"VLC Instance: {__VLC_INSTANCE}")

    if __VLC_INSTANCE is not None:
        __VLC_INSTANCE = __VLC_INSTANCE.release()
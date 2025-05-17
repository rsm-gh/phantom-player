#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of either:
#
#   - the GNU Lesser General Public License as published by
#     the Free Software Foundation, version 2.1 only, or
#
#   - the GNU General Public License as published by
#     the Free Software Foundation, version 3 only.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the applicable licenses for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# version 2.1 and the GNU General Public License version 3
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-2.1-only OR GPL-3.0-only

import os
import vlc
import sys
import time

from console_printer import print_debug

if sys.stderr is not None:
    # If built in windows, there will be no console and the library
    # will fail because there is no stderr
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
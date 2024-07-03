#!/usr/bin/python3

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli.
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
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import vlc
import time

_VLC_SCAN = vlc.Instance()
_VLC_PARSE_TIMEOUT = 5000


def video_duration(path):

    if not os.path.exists(path):
        return 0

    media = _VLC_SCAN.media_new(path)
    media.parse_with_options(vlc.MediaParseFlag.local, _VLC_PARSE_TIMEOUT)
    while media.get_parsed_status() == 0:
        time.sleep(.1)

    duration = media.get_duration()

    if duration <= 0:
        return 0

    return int(media.get_duration() / 1000)

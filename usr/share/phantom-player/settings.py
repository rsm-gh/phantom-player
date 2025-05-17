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

_IMAGE_FORMATS = ("jpeg", "jpg", "png", "webp", "svg")
_VIDEO_HASH_SIZE = 64
_SAVE_PLAYLISTS_SECONDS = 10 # Number of seconds that need to pass for saving a playlist

class IconSize:
    class Small:
        _width = 90
        _height = 120

    class Medium:
        _width = 150
        _height = 200

    class Big:
        _width = 250
        _height = 333


class ThemeButtons:
    """
        Name of the GTK theme buttons to be used in the player.
    """
    _play = "media-playback-start"
    _pause = "media-playback-pause"
    _next = "go-last"
    _previous = "go-first"
    _volume = ["audio-volume-muted", "audio-volume-high", "audio-volume-medium"]
    _fullscreen = "view-fullscreen"
    _un_fullscreen = "view-restore"
    _random = "media-playlist-shuffle"
    _keep_playing = "media-playlist-repeat"
    _settings = "media-tape"
    _menu = "open-menu"


class FontColors:
    _default = "#000000"
    _success = "#009933"
    _warning = "#ff9900"
    _error = "#ff0000"

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

_IMAGE_FORMATS = ("jpeg", "jpg", "png", "webp", "svg")
_VIDEO_HASH_SIZE = 64


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

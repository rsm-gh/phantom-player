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

_LONG_TIME_PLEASE_WAIT = "This may take long time, please wait.."


class Texts:
    class MediaPlayer:
        class Tooltip:
            _start = "Go to Start"
            _end = "Go to End"
            _play = "Play"
            _pause = "Pause"
            _tracks = "Audio & Subtitles"
            _fullscreen = "Fullscreen"
            _unfullscreen = "Un-Fullscreen"
            _keep_playing = "Keep Playing"
            _random = "Random Mode"

    class GUI:
        _title = "Phantom Player"

    class DialogPlaylist:

        _confirm_delete = 'Are you sure that you want to delete "{0}"?\n\nThe files will not be deleted from your hard drive.'
        _confirm_reset = 'Are you sure that you want to restart "{0}"?.'
        _is_missing = 'The playlist can not be reproduced because the videos are missing.'
        _already_exist = 'The playlist "{}" already exists.\n\nPlease rename the other playlist before adding this one.'
        _name_exist = 'The playlist "{}" already exists.\n\nPlease choose a different name.'
        _all_videos_played = 'All the videos have been played, restart the playlist to watch it again.'

    class WindowSettings:
        _new_title = "New Playlist"
        # it is important to specify "the name" in case that the user switched the settings tab.
        _playlist_name_empty = "The playlist name can not be empty."

        _add_path_error = 'It is not possible to add a path (or recursive path) that contains the following character "{}"'
        _add_path_title = "Discovering Videos"
        _add_path_videos = _LONG_TIME_PLEASE_WAIT
        _add_path_videos_done = "Scan done, the following videos went added:"

        _add_recursive_title = "Discovering recursive videos"
        _adding_recursive_videos = _LONG_TIME_PLEASE_WAIT
        _adding_recursive_videos_done = "Recursive scan done, the following videos will be added:"

        _remove_path_title = "Removing sources path"
        _remove_recursive_title = "Removing recursive videos"
        _remove_videos = "The following videos went removed:"

        _playlist_path_cant_recursive = "To make this path recursive, you need first remove the other ones that will be included by this one."
        _playlist_path_cant_add = "The path is already in the added (or recursively included)."

    class DialogVideos:
        _trash_videos = "{} video(s) will be moved to the trash.\n\n Do you want to continue?"
        _missing = 'The file is missing.'
        _cant_open_dir = 'Uh! It was not possible to open:\n\n"{0}"'

    class StatusBar:
        _load_playlist_cached = "Loading videos of {}..."
        _load_playlists_ended = "All the playlists are loaded."
        _load_playlist_discover = "Discovering {}, playlist {} of {}..."

    class DialogRenameSingle:
        _title = "Rename"
        _hdrive_off = "Rename the file only in Phantom-Player."
        _hdrive_on = "Rename the file in the hard-drive"

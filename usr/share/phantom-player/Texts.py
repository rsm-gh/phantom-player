#!/usr/bin/python3
#

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli
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

_LONG_TIME_PLEASE_WAIT = "This may take long time, please wait.."


class Texts:
    class MediaPlayer:
        class Tooltip:
            _start = "Restart"
            _end = "End"
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
        _is_missing = 'The playlist can not be reproduced because the videos are missing!\n\nUse the search button to find them.'
        _already_exist = 'The playlist "{}" already exists.\n\nPlease rename the other playlist before adding this one.'
        _name_exist = 'The playlist "{}" already exists.\n\nPlease choose a different name.'
        _all_videos_played = 'All the videos have been played, restart the playlist to watch it again.'

    class WindowSettings:
        _new_title = "New Playlist"
        _playlist_name_empty = "The name can not be empty."

        _add_path_error = 'It is not possible to add a path (or recursive path) that contains the following character "{}"'
        _add_path_title = "Discovering Videos"
        _add_path_videos = _LONG_TIME_PLEASE_WAIT
        _add_path_videos_done = "Inspection done, the following videos will be added:"

        _add_recursive_title = "Discovering recursive videos"
        _adding_recursive_videos = _LONG_TIME_PLEASE_WAIT
        _adding_recursive_videos_done = "Recursive inspection done, the following videos will be added:"

        _remove_recursive_title = "Removing recursive videos"
        _remove_videos = "The following videos will be removed:"

        _playlist_path_cant_recursive = "To make this path recursive, you need first remove the other ones that will be included by this one."
        _playlist_path_cant_add = "The path is already in the added (or recursively included)."

    class MenuItemVideos:
        _open_dir = "Open Directory"
        _ignore = "Ignore"
        _dont_ignore = "Don't Ignore"
        _progress_reset = "Restart Progress"
        _progress_fill = "Fill Progress"
        _remove = "Remove from listing"

    class DialogVideos:
        _delete = '''Are you sure that you want to delete the selected videos?\n\nThey wont be removed from your hard drive.'''
        _missing = 'The video can not be reproduced because the file is missing. Use the search button to find it.'
        _found_x = '{0} videos have been found.'
        _other_found = '{0} other videos have been found.'

    class StatusBar:
        _load_playlist_headers = "Loading playlists headers..."
        _load_playlist_cached = "Loading videos of '{}'..."
        _load_playlists_ended = "All the playlists are loaded."

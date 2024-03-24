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
        title = "Phantom Player"

    class MenuItemPlaylist:
        search = "Search"
        open_dir = "Open Directory"
        settings = "Settings"

    class DialogPlaylist:
        confirm_delete = 'Are you sure that you want to delete "{0}"?\n\nThe files will not be deleted from your hard drive.'
        confirm_reset = 'Are you sure that you want to restart "{0}"?.'
        is_missing = 'The playlist can not be reproduced because the videos are missing!\n\nUse the search button to find them.'
        already_exist = 'The playlist "{}" already exists.\n\nPlease rename the other playlist before adding this one.'
        name_exist = 'The playlist "{}" already exists.\n\nPlease choose a different name.'
        all_videos_played = 'All the videos have been played, restart the playlist to watch it again.'

    class WindowSettings:
        new_title = "New Playlist"
        edit_title = "Settings"
        playlist_name_empty = "The playlist name can not be empty."
        importing_videos = "Importing videos... This may take long time, the software will generate a hash for each video."

    class MenuItemVideos:
        open_dir = "Open Directory"
        ignore = "Ignore"
        dont_ignore = "Don't Ignore"
        search = "Search"
        reproduce = "Play"
        progress_reset = "Restart Progress"
        progress_fill = "Fill Progress"

    class DialogVideos:
        delete = '''Are you sure that you want to delete the selected videos?\n\nThey wont be removed from your hard drive.'''
        missing = 'The video can not be reproduced because the file is missing. Use the search button to find it.'
        found_x = '{0} videos have been found.'
        other_found = '{0} other videos have been found.'

    class StatusBar:

        _load_playlist_headers = "Loading playlists headers..."
        _load_playlist_cached = "Loading cached videos of '{}'..."
        _load_playlists_ended = "All the playlists are loaded."
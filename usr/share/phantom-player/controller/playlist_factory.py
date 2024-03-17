#!/usr/bin/python3
import os.path

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
from model.Playlist import Playlist
from model.PlaylistPath import PlaylistPath
from model.Video import VideoPosition
from controller.utils import str_to_boolean

def load_from_file(file_path):

    print("Loading playlist file '{}'".format(file_path))

    with open(file_path, mode='rt', encoding='utf-8') as f:
        playlist_header = f.readline().split('|')
        playlist_path = f.readline().split('|')

    #
    # Read the header
    #

    try:
        random = str_to_boolean(playlist_header[0])
    except Exception:
        print("\tError getting 'random'")
        random = False

    try:
        keep_playing = str_to_boolean(playlist_header[1])
    except Exception:
        print("\tError getting 'keep_playing'")
        keep_playing = False

    try:
        start_at = float(playlist_header[2])
    except Exception:
        print("\tError getting 'start_at'")
        start_at = VideoPosition._start

    try:
        audio_track = int(playlist_header[3])
    except Exception:
        print("\tError getting 'audio_track'")
        audio_track = 0

    try:
        subtitles_track = int(playlist_header[4])
    except Exception:
        print("\tError getting 'subtitles_track'")
        subtitles_track = 0

    try:
        icon_extension = playlist_header[5].strip()
    except Exception:
        print("\tError getting 'icon_extension'")
        icon_extension = ""

    #
    # Read the path
    #

    try:
        data_path = playlist_path[0].strip()
    except Exception:
        print("\tError getting 'data_path'")
        data_path = ""

    try:
        recursive = str_to_boolean(playlist_path[1])
    except Exception:
        print("\tError getting 'recursive'")
        recursive = False

    try:
        r_startup = str_to_boolean(playlist_path[2])
    except Exception:
        print("\tError getting 'r_startup'")
        r_startup = False

    playlist_paths = []
    if data_path != "":
        playlist_paths.append(PlaylistPath(data_path, recursive, r_startup))

    #
    # Create the playlist (without loading the videos)
    #
    new_playlist = Playlist(name=os.path.basename(file_path),
                            icon_extension=icon_extension,
                            is_random=random,
                            keep_playing=keep_playing,
                            start_at=start_at,
                            audio_track=audio_track,
                            subtitles_track=subtitles_track)


    for playlist_path in playlist_paths:
        new_playlist.add_playlist_path(playlist_path)

    return new_playlist

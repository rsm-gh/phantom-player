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
import csv

from model.Playlist import Playlist
from model.PlaylistPath import PlaylistPath
from model.Video import VideoPosition
from Paths import _SERIES_DIR
from controller.utils import str_to_boolean, read_lines


def load_from_file(file_path, pid):

    print("Loading headers & paths of ", file_path)
    lines = read_lines(file_path)

    #
    # Read the header
    #
    random = False
    keep_playing = False
    start_at = VideoPosition._start
    audio_track = 0
    current_video_hash = ""

    try:
        header = lines[0].split("|")
    except Exception:
        print("\tError getting the header.")
    else:

        try:
            random = str_to_boolean(header[0])
        except Exception:
            print("\tError getting 'random'")

        try:
            keep_playing = str_to_boolean(header[1])
        except Exception:
            print("\tError getting 'keep_playing'")

        try:
            start_at = float(header[2])
        except Exception:
            print("\tError getting 'start_at'")

        try:
            audio_track = int(header[3])
        except Exception:
            print("\tError getting 'audio_track'")

        try:
            subtitles_track = int(header[4])
        except Exception:
            print("\tError getting 'subtitles_track'")
            subtitles_track = 0

        try:
            # Deprecated icon extension
            _ = header[5].strip()
        except Exception:
            pass

        try:
            current_video_hash = header[6].strip()
        except Exception:
            print("\tError getting 'current_video_hash'")
        else:
            if len(current_video_hash) < 10: # in case the CSV parser saves "false" as value
                current_video_hash = ""

    #
    # Create the playlist (without loading the videos)
    #
    new_playlist = Playlist(pid=pid,
                            name=os.path.basename(file_path),
                            is_random=random,
                            keep_playing=keep_playing,
                            start_at=start_at,
                            audio_track=audio_track,
                            subtitles_track=subtitles_track,
                            current_video_hash=current_video_hash)

    #
    # Read the path
    #
    for i, line in enumerate(lines):

        if i == 0:
            continue

        possible_path = line.split("|")

        if len(possible_path) != 3:
            break

        else:
            recursive = False
            r_startup = False

            try:
                data_path = possible_path[0].strip()
            except Exception:
                print("\tError getting 'data_path'")
                continue
            else:
                if "/" not in data_path and "\\" not in data_path:
                    print("\t\tunvalid the path=", data_path)
                    continue

            try:
                recursive = str_to_boolean(possible_path[1])
            except Exception:
                print("\tError getting 'recursive'")

            try:
                r_startup = str_to_boolean(possible_path[2])
            except Exception:
                print("\tError getting 'r_startup'")


            playlist_path = PlaylistPath(path=data_path,
                                         recursive=recursive,
                                         startup_discover=r_startup)
            added = new_playlist.add_playlist_path(playlist_path)
            if not added:
                print('\tError rejected path='+data_path)


    return new_playlist


def save(playlist):

    if not os.path.exists(_SERIES_DIR):
        os.mkdir(_SERIES_DIR)

    with open(playlist.get_save_path(), mode='wt', encoding='utf-8') as f:
        csv_list = csv.writer(f, delimiter='|')

        csv_list.writerow([playlist.get_random(),
                           playlist.get_keep_playing(),
                           playlist.get_start_at(),
                           playlist.get_audio_track(),
                           playlist.get_subtitles_track(),
                           "None",
                           playlist.get_current_video_hash()])

        for playlist_path in playlist.get_playlist_paths():
            csv_list.writerow([playlist_path.get_path(),
                               playlist_path.get_recursive(),
                               playlist_path.get_startup_discover()])

        for video in playlist.get_videos():
            csv_list.writerow([video.get_path(),
                               video.get_name(),
                               video.get_position(),
                               video.get_ignore(),
                               video.get_hash()])
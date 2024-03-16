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
import magic

from model.Video import Video, VideoPosition
from controller.utils import str_to_boolean

_MAGIC_MIMETYPE = magic.open(magic.MAGIC_MIME)
_MAGIC_MIMETYPE.load()

def load(playlist, is_startup):

    print("Loading videos of '{}':".format(playlist.get_name()))

    if not os.path.exists(playlist.get_save_path()):
        print("\tCached videos... SKIP, the configuration file does not exist.")
    else:
        print("\tCached videos...")

        with open(playlist.get_save_path(), mode='rt', encoding='utf-8') as f:
            rows = list(f.readlines())

        for i, row in enumerate(rows):
            # 0: is the series header
            # 1: is the series path
            # 2: start of the videos
            if i <= 1:
                continue

            #
            # Read the data
            #
            columns = row.split('|')


            # The ID is no longer read.
            try:
                video_id = int(columns[0])
            except Exception:
                start = 0
            else:
                start = 1

            try:
                path = columns[start].strip()
            except Exception:
                print("\t\terror getting the path", columns)
                path = None

            try:
                name = columns[start+1].strip()
            except Exception:
                print("\t\terror getting the name", columns)
                name = ""

            try:
                position = float(columns[start+2])
            except Exception:
                position = VideoPosition._start
                print("\t\terror getting the position", columns)

            try:
                ignore = str_to_boolean(columns[start+3])
            except Exception:
                ignore = False
                print("\t\terror getting the ignore state", columns)

            #
            # Check for valid lines
            #
            if path is None:
                print("\t\tExit line because empty path.", columns)
                continue

            elif os.path.exists(path) and not __file_is_video(path,True):
                print("\t\tExit line because not video.", columns)
                continue

            duplicated = False
            for video in playlist.get_videos():
                if video.get_path() == path:
                    duplicated = True
                    break

            if duplicated:
                print("\t\tExit line because duplicated path.", columns)
                continue

            video = Video(path, name)
            video.set_position(position)
            video.set_ignore(ignore)
            playlist.add_video(video)


    #
    #    Get the videos from the folder. This will find new videos.
    #
    if not is_startup or (is_startup and playlist.get_r_startup()):
        if not os.path.exists(playlist.get_data_path()):
            print("\tDiscovering new videos... SKIP, the data path does not exist.")
        else:
            print("\tDiscovering new videos...")
            playlist_paths = [video.get_path() for video in playlist.get_videos()]
            for video_path in __generate_videos_list_from_directory(playlist.get_data_path(), playlist.get_recursive()):
                if video_path not in playlist_paths:
                    new_video = Video(video_path)
                    new_video.set_is_new(True)
                    playlist.add_video(new_video)
    else:
        print("\tDiscovering new videos... SKIP requested.")

def __file_is_video(path, forgive_broken_links=False):
    if os.path.islink(path):
        if forgive_broken_links and not os.path.exists(os.path.realpath(path)):
            return True

        mimetype = _MAGIC_MIMETYPE.file(os.path.realpath(path))
    else:
        mimetype = _MAGIC_MIMETYPE.file(path)

    if 'video/' in mimetype:
        return True

    return False


def __generate_videos_list_from_directory(dir_path, recursive):
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return []

    if recursive:
        paths = [os.path.join(dp, filename) for dp, dn, filenames in os.walk(dir_path) for filename in filenames]
    else:
        paths = [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]

    return [path for path in sorted(paths) if __file_is_video(path)]

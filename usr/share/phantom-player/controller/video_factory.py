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
import hashlib

from model.Video import Video, VideoPosition
from controller.utils import str_to_boolean, read_lines

_MAGIC_MIMETYPE = magic.open(magic.MAGIC_MIME)
_MAGIC_MIMETYPE.load()


def __hash_of_file(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


def load(playlist, is_startup, add_func=None):
    print("Loading videos of '{}':".format(playlist.get_name()))
    load_cached(playlist, add_func=add_func)

    # discover new videos
    auto_discover = False
    for playlist_path in playlist.get_playlist_paths():
        if playlist_path.get_startup_discover():
            auto_discover = True
            break

    if not is_startup or (is_startup and auto_discover):
        discover(playlist, add_func=add_func)


def load_cached(playlist, add_func=None):
    if not os.path.exists(playlist.get_save_path()):
        print("\tCached videos... SKIP, the configuration file does not exist.")
        return

    print("\tCached videos...")

    current_data = {}

    for i, row in enumerate(read_lines(playlist.get_save_path())):

        if i < 1:  # the first line is always the header
            continue

        #
        # Read the data
        #
        columns = row.split('|')

        if len(columns) <= 3:  # is not a video item
            continue

        name = ""
        position = VideoPosition._start
        ignore = False
        hash_file = ""

        try:
            path = columns[0].strip()
        except Exception:
            print("\t\terror getting the path", columns)
            continue
        else:
            if "/" not in path and "\\" not in path:
                print("\t\tinvalid the path=", path)
                continue

        try:
            name = columns[1].strip()
        except Exception:
            print("\t\terror getting the name", columns)

        try:
            position = float(columns[2])
        except Exception:
            print("\t\terror getting the position", columns)

        try:
            ignore = str_to_boolean(columns[3])
        except Exception:
            print("\t\terror getting the ignore state", columns)

        #
        # Check for valid lines
        #
        if path is None:
            print("\t\tSkipping line because empty path.", columns)
            continue

        if os.path.exists(path) and not __file_is_video(path, True):
            print("\t\tSkipping line because not video.", columns)
            continue

        if path in current_data.values():
            print("\t\tSkipping line because duplicated path.", path)
            continue

        #
        # This must be calculated after all the previous tests,
        # to avoid doing unuseful calculations.
        try:
            hash_file = columns[4].strip()
        except Exception:
            print("\t\terror getting the hash", columns)
        else:
            # Check if it is a hash, because when the hash is empty, the value is exported as False.
            # Why? Because if the CSV module?
            if len(hash_file) < 10:
                hash_file = ""

        if hash_file == "" and os.path.exists(path):
            print("\t\trecalculating video hash...", path)
            hash_file = __hash_of_file(path)

        if hash_file in current_data.keys():
            print("\t\tSkipping line because hash exists...", hash_file)
            print("\t\t\tImported path:", current_data[hash_file])
            print("\t\t\tSkipped path:", path)
            continue

        video = Video(path, name)
        video.set_position(position)
        video.set_ignore(ignore)
        video.set_hash(hash_file)
        playlist.add_video(video)
        if hash_file != "":  # The hash can be empty if the path does not exist
            current_data[hash_file] = path

        if add_func is not None:
            add_func(playlist, video)


def discover(playlist, playlist_paths=None, add_func=None):
    print("\tDiscovering new videos...")

    current_data = {video.get_hash(): video.get_path() for video in playlist.get_videos()}

    if playlist_paths is None:
        playlist_paths = playlist.get_playlist_paths()

    for playlist_path in playlist_paths:

        if os.path.exists(playlist_path.get_path()):
            print("\t\tLoading...", playlist_path.get_path())
        else:
            print("\t\tSkipping...", playlist_path.get_path())
            continue

        for video_path in __generate_videos_list_from_directory(playlist_path.get_path(),
                                                                playlist_path.get_recursive()):

            if video_path in current_data.values():
                continue  # No message on already added videos

            video_hash = __hash_of_file(video_path)
            if video_hash in current_data.keys():

                imported_path = current_data[video_hash]

                if not os.path.exists(imported_path):
                    # The video was renamed, use the new path instead
                    video = playlist.get_video_by_hash(video_hash)
                    video.set_path(video_path)
                    video.set_is_new(True)
                    current_data[video_hash] = video_path

                    print("\t\t\tUpdating path of video:")
                    print("\t\t\t\tOld path:", imported_path)
                    print("\t\t\t\tNew path:", video_path)
                    continue
                else:
                    print("\t\t\tSkipping video because hash exists...", video_hash)
                    print("\t\t\t\tImported path:", imported_path)
                    print("\t\t\t\tSkipped path:", video_path)
                    continue

            new_video = Video(video_path)
            new_video.set_is_new(True)
            new_video.set_hash(video_hash)
            playlist.add_video(new_video)
            current_data[video_hash] = video_path
            print("\t\t\tAdding...", video_path)
            if add_func is not None:
                add_func(playlist, new_video)


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

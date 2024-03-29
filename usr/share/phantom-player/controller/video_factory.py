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
from controller.utils import str_to_boolean

_MAGIC_MIMETYPE = magic.open(magic.MAGIC_MIME)
_MAGIC_MIMETYPE.load()

def __hash_of_file(file_path):

    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


def load(playlist, is_startup):

    print("Loading videos of '{}':".format(playlist.get_name()))
    load_cached(playlist)

    # discover new videos
    auto_discover = False
    for playlist_path in playlist.get_playlist_paths():
        if playlist_path.get_startup_discover():
            auto_discover = True
            break

    if not is_startup or (is_startup and auto_discover):
        discover(playlist)
    else:
        print("\tDiscovering new videos... SKIP requested.")

def load_cached(playlist):

    if not os.path.exists(playlist.get_save_path()):
        print("\tCached videos... SKIP, the configuration file does not exist.")
        return


    print("\tCached videos...")

    with open(playlist.get_save_path(), mode='rt', encoding='utf-8') as f:
        rows = list(f.readlines())

    existent_video_hashes = []
    existent_video_paths = []

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


        # The ID is no longer read. This is for compatibility
        # for the old files.
        try:
            int(columns[0])
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
            print("\t\terror getting the position", columns)
            position = VideoPosition._start

        try:
            ignore = str_to_boolean(columns[start+3])
        except Exception:
            print("\t\terror getting the ignore state", columns)
            ignore = False

        #
        # Check for valid lines
        #
        if path is None:
            print("\t\tExit line because empty path.", columns)
            continue

        if os.path.exists(path) and not __file_is_video(path,True):
            print("\t\tExit line because not video.", columns)
            continue


        if path in existent_video_paths:
            print("\t\tExit line because duplicated path.", path)
            continue
        else:
            existent_video_paths.append(path)

        #
        # This must be calculated after all the previous tests,
        # to avoid doing unuseful calculations.
        try:
            hash_file = columns[start+4].strip()
        except Exception:
            hash_file = ""
        else:
            # Check if it is a hash, because when the hash is empty, the value is exported as False.
            # Why? Because if the CSV module?
            if len(hash_file) < 10:
                hash_file = ""

        if hash_file == "" and os.path.exists(path):
            print("\t\trecalculating video hash...", path)
            hash_file = __hash_of_file(path)

        if hash_file in existent_video_hashes:
            print("\t\tExit line because duplicated hash", hash_file, path)
            continue

        if os.path.exists(path):
            existent_video_hashes.append(hash_file)

        video = Video(path, name)
        video.set_position(position)
        video.set_ignore(ignore)
        video.set_hash(hash_file)
        playlist.add_video(video)


def discover(playlist, playlist_paths=None, add_func=None):

    print("\tDiscovering new videos...")

    playlist_path_values = [video.get_path() for video in playlist.get_videos()]
    playlist_hash_values = [video.get_hash() for video in playlist.get_videos()]

    if playlist_paths is None:
        playlist_paths = playlist.get_playlist_paths()

    for playlist_path in playlist_paths:

        if os.path.exists(playlist_path.get_path()):
            print("\t\tLoading...", playlist_path.get_path())
        else:
            print("\t\tSkipping...", playlist_path.get_path())
            continue

        for video_path in __generate_videos_list_from_directory(playlist_path.get_path(), playlist_path.get_recursive()):

            if video_path in playlist_path_values:
                continue

            video_hash = __hash_of_file(video_path)
            if video_hash in playlist_hash_values:
                print("\t\t\tSkipping video because hash exist...", video_path)
                continue

            new_video = Video(video_path)
            new_video.set_is_new(True)
            new_video.set_hash(video_hash)
            playlist.add_video(new_video)
            print("\t\t\tAdding...", video_path)
            if add_func is not None:
                add_func(video_path)


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

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

from model.Video import Video
from controller.playlist_factory import _COLUMN_SEPARATOR

_MAGIC_MIMETYPE = magic.open(magic.MAGIC_MIME)
_MAGIC_MIMETYPE.load()


def discover_all(playlist, is_startup, add_func=None):
    auto_discover = False
    for playlist_path in playlist.get_playlist_paths():
        if playlist_path.get_startup_discover():
            auto_discover = True
            break

    if not is_startup or (is_startup and auto_discover):
        discover(playlist, add_func=add_func)


def discover(playlist, playlist_paths=None, add_func=None):
    print("Discovering new videos of '{}'...".format(playlist.get_name()))

    current_data = {video.get_hash(): video.get_path() for video in playlist.get_videos()}

    if playlist_paths is None:
        playlist_paths = playlist.get_playlist_paths()

    for playlist_path in playlist_paths:

        if os.path.exists(playlist_path.get_path()):
            print("\tDiscovering...", playlist_path.get_path())
        else:
            print("\tSkipping...", playlist_path.get_path())
            continue

        for video_path in __get_videos_from_dir(playlist_path.get_path(),
                                                playlist_path.get_recursive()):

            if video_path in current_data.values():
                continue  # No message on already added videos

            video_hash = __file_hash(video_path)
            if video_hash in current_data.keys():

                imported_path = current_data[video_hash]

                if not os.path.exists(imported_path):
                    # The video was renamed, use the new path instead
                    video = playlist.get_video_by_hash(video_hash)
                    video.set_path(video_path)
                    video.set_is_new(True)
                    current_data[video_hash] = video_path

                    print("\t\tUpdating path of video:")
                    print("\t\t\tOld path:", imported_path)
                    print("\t\t\tNew path:", video_path)
                    continue
                else:
                    print("\t\tSkipping video because hash exists...", video_hash)
                    print("\t\t\tImported path:", imported_path)
                    print("\t\t\tSkipped path:", video_path)
                    continue

            new_video = Video(video_path)
            new_video.set_is_new(True)
            new_video.set_hash(video_hash)
            playlist.add_video(new_video)
            current_data[video_hash] = video_path
            print("\t\tAdding...", video_path)
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


def __file_hash(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()


def __get_videos_from_dir(dir_path, recursive):
    if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
        return []

    elif _COLUMN_SEPARATOR in dir_path:
        print("\tWarning:__get_videos_from_dir excluded an invalid path=", dir_path)
        return []

    paths = []

    if recursive:
        for dp, dn, filenames in os.walk(dir_path):
            for filename in filenames:
                path = os.path.join(dp, filename)
                if _COLUMN_SEPARATOR in path:
                    print("\tWarning:__get_videos_from_dir excluded an invalid path=", path)
                else:
                    paths.append(path)
    else:
        for filename in os.listdir(dir_path):
            path = os.path.join(dir_path, filename)
            if _COLUMN_SEPARATOR in path:
                print("\tWarning:__get_videos_from_dir excluded an invalid path=", path)
            else:
                paths.append(path)

    return paths

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


def discover(playlist, playlist_paths=None, add_func=None, update_func=None, quit_func=None):
    print("Discovering new videos of '{}'...".format(playlist.get_name()))

    current_data = {video.get_hash(): video.get_path() for video in playlist.get_videos()}

    if playlist_paths is None:
        playlist_paths = playlist.get_playlist_paths()

    for playlist_path in playlist_paths:
        __discover_playlist_path(playlist=playlist,
                                 playlist_path=playlist_path,
                                 exclude_data=list(current_data.values()),
                                 current_data=current_data,
                                 add_func=add_func,
                                 update_func=update_func,
                                 quit_func=quit_func)


def __discover_playlist_path(playlist,
                             playlist_path,
                             exclude_data,
                             current_data,
                             add_func=None,
                             update_func=None,
                             quit_func=None):
    source_path = playlist_path.get_path()

    if os.path.exists(source_path):
        print("\tDiscovering...", source_path)
    else:
        print("\tSkipping...", source_path)
        return

    if not os.path.exists(source_path) or not os.path.isdir(source_path):
        return

    elif _COLUMN_SEPARATOR in source_path:
        print("\tWarning:__get_videos_from_dir excluded an invalid path=", source_path)
        return

    if playlist_path.get_recursive():
        for dp, dn, filenames in os.walk(source_path):
            for filename in filenames:
                __discover_video(playlist=playlist,
                                 file_path=os.path.join(dp, filename),
                                 exclude_paths=exclude_data,
                                 current_data=current_data,
                                 add_func=add_func,
                                 update_func=update_func)

                if quit_func is not None and quit_func():
                    return
    else:
        for filename in os.listdir(source_path):
            __discover_video(playlist=playlist,
                             file_path=os.path.join(source_path, filename),
                             exclude_paths=exclude_data,
                             current_data=current_data,
                             add_func=add_func,
                             update_func=update_func)

            if quit_func is not None and quit_func():
                return


def __discover_video(playlist, file_path, exclude_paths, current_data, add_func=None, update_func=None):
    if file_path in exclude_paths:
        return

    elif file_path.endswith(".part"):
        return

    elif _COLUMN_SEPARATOR in file_path:
        print("\tWarning:__discover_video excluded an invalid path=", file_path)
        return

    elif not __file_is_video(file_path):
        return

    elif file_path in current_data.values():
        return  # No message on already added videos

    video_hash = __file_hash(file_path)
    if video_hash in current_data.keys():

        imported_path = current_data[video_hash]

        if not os.path.exists(imported_path):
            # The video was renamed, use the new path instead
            video = playlist.get_video_by_hash(video_hash)
            video.set_path(file_path)
            video.set_is_new(True)
            current_data[video_hash] = file_path

            print("\t\tUpdating path of video:")
            print("\t\t\tOld path:", imported_path)
            print("\t\t\tNew path:", file_path)

            if update_func is not None:
                update_func(playlist, video)

            return
        else:
            print("\t\tSkipping video because hash exists...", video_hash)
            print("\t\t\tImported path:", imported_path)
            print("\t\t\tSkipped path:", file_path)
            return

    new_video = Video(file_path)
    new_video.set_is_new(True)
    new_video.set_hash(video_hash)
    playlist.add_video(new_video)
    current_data[video_hash] = file_path
    print("\t\tAdding...", file_path)
    if add_func is not None:
        add_func(playlist, new_video)


def __file_is_video(path):
    if os.path.islink(path):
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

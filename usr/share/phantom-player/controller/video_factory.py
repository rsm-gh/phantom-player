#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024-2025 Rafael Senties Martinelli.
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

import os
import magic
import inspect
import hashlib

import system_utils
from model.Video import Video
from vlc_utils import get_video_duration
from controller.playlist_factory import _COLUMN_SEPARATOR
from console_printer import print_debug, print_warning

if "mime" in inspect.signature(magic.Magic).parameters: # ahupp version
    _MAGIC_MIMETYPE = magic.Magic(mime=True)
    def get_mime(path:str) -> str:
        return _MAGIC_MIMETYPE.from_file(path)

elif list(__import__('inspect').signature(__import__('magic').Magic).parameters)[0] == 'ms': # very old file-magic
    def get_mime(path:str) -> str:
        ms = magic.open(magic.MAGIC_MIME)
        ms.load()  # loads the default magic database
        mime_type = ms.file(path)
        ms.close()
        return mime_type

else: # python-magic-bin
    _MAGIC_MIMETYPE = magic.Magic()
    def get_mime(path:str) -> str:
        return magic.from_file(path, mime=True)

def discover(playlist, playlist_paths=None, add_func=None, update_func=None, quit_func=None):
    print_debug(f"playlist name={playlist.get_name()}")

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
    print_debug(f"path={source_path}")

    if not os.path.exists(source_path):
        print_debug("Nothing to discover, the path does not exist.", direct_output=True)
        return

    if not os.path.exists(source_path) or not os.path.isdir(source_path):
        return

    elif _COLUMN_SEPARATOR in source_path:
        print_warning(f"excluded an invalid path={source_path}")
        return

    if playlist_path.get_recursive():
        for root, directories, filenames in os.walk(source_path):
            for filename in filenames:
                __discover_video(playlist=playlist,
                                 file_path=system_utils.join_path(root, filename),
                                 exclude_paths=exclude_data,
                                 current_data=current_data,
                                 add_func=add_func,
                                 update_func=update_func)

                if quit_func is not None and quit_func():
                    return
    else:
        for filename in os.listdir(source_path):
            abs_path = system_utils.join_path(source_path, filename)

            if os.path.isfile(abs_path):
                __discover_video(playlist=playlist,
                                 file_path=abs_path,
                                 exclude_paths=exclude_data,
                                 current_data=current_data,
                                 add_func=add_func,
                                 update_func=update_func)

            if quit_func is not None and quit_func():
                return


def __discover_video(playlist,
                     file_path,
                     exclude_paths,
                     current_data,
                     add_func=None,
                     update_func=None):

    if file_path in exclude_paths:
        return

    elif file_path.endswith(".part"):
        return

    elif _COLUMN_SEPARATOR in file_path:
        print_warning("excluded an invalid path={file_path}")
        return

    elif not __file_is_video(file_path):
        return

    elif file_path in current_data.values():
        return  # No message on already added videos

    print_debug(f"playlist name={playlist.get_name()}, file_path={file_path}")

    video_hash = __file_hash(file_path)
    if video_hash in current_data.keys():

        imported_path = current_data[video_hash]

        if os.path.exists(imported_path):
            # The video is already added with a different path
            print_debug(f"\t\tSkipping video because hash exists... {video_hash}", direct_output=True)
            print_debug(f"\t\t\tImported path: {imported_path}", direct_output=True)
            print_debug(f"\t\t\tSkipped path: {file_path}", direct_output=True)
            return
        else:
            # The video was renamed, use the new path instead
            video = playlist.get_video_by_hash(video_hash)
            video.set_path(file_path)
            video.set_is_new(True)
            current_data[video_hash] = file_path

            print_debug("\t\tUpdating path of video:", direct_output=True)
            print_debug(f"\t\t\tOld path: {imported_path}", direct_output=True)
            print_debug(f"\t\t\tNew path: {file_path}", direct_output=True)

            if update_func is not None:
                update_func(playlist, video)

            return

    #
    # Add a new video.
    #
    # It is important to not save the playlist here when a video is added. Because
    # it will make it appear as "new" until the playlist is opened by the user.
    #
    new_video = Video(vhash=video_hash, path=file_path)
    new_video.set_duration(get_video_duration(file_path))
    new_video.set_size(os.path.getsize(file_path))
    new_video.set_is_new(True)

    playlist.add_video(new_video)
    current_data[video_hash] = file_path
    print_debug(f"\t\tAdding...{file_path}", direct_output=True)
    if add_func is not None:
        add_func(playlist, new_video)


def __file_is_video(path:str) -> bool:

    if os.path.islink(path) or path.endswith(".lnk"):
        path = os.path.realpath(path)

    return get_mime(path).startswith("video/")


def __file_hash(file_path):
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256()
        while chunk := f.read(8192):
            file_hash.update(chunk)

    return file_hash.hexdigest()

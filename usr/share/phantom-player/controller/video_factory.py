#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import magic
import hashlib

from model.Video import Video
from vlc_utils import video_duration
from controller.playlist_factory import _COLUMN_SEPARATOR
from console_printer import print_debug, print_warning

_MAGIC_MIMETYPE = magic.open(magic.MAGIC_MIME)
_MAGIC_MIMETYPE.load()


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
    print_debug(f"playlist name={playlist.get_name()}, file_path={file_path}")

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

    video_hash = __file_hash(file_path)
    if video_hash in current_data.keys():

        imported_path = current_data[video_hash]

        if not os.path.exists(imported_path):
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
        else:
            print_debug(f"\t\tSkipping video because hash exists... {video_hash}", direct_output=True)
            print_debug(f"\t\t\tImported path: {imported_path}", direct_output=True)
            print_debug(f"\t\t\tSkipped path: {file_path}", direct_output=True)
            return

    new_video = Video(video_hash, file_path, video_duration(file_path))
    new_video.set_is_new(True)
    playlist.add_video(new_video)
    current_data[video_hash] = file_path
    print_debug(f"\t\tAdding...{file_path}", direct_output=True)
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

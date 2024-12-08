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
from typing import Sequence

from Paths import _SERIES_DIR
from settings import _VIDEO_HASH_SIZE
from model.Playlist import Playlist, LoadStatus
from model.PlaylistPath import PlaylistPath
from model.Video import Video
from vlc_utils import get_video_duration
from console_printer import print_debug, print_error, print_warning

_COLUMN_SEPARATOR = "|"
_VALUE_SEPARATOR = "="

# These must be either GET or SET
_PLAYLIST_ATTR = ('random',
                  'keep_playing',
                  'start_at',
                  'audio_track',
                  'subtitles_track',
                  'current_video_hash')

_PLAYLIST_PATH_ATTR = ('recursive', 'startup_discover')
_VIDEO_ATTR = ('duration', 'progress', 'ignore', 'path', 'name', 'size', 'rating')

_PLAYLIST_SETTINGS_HEADER = """
#
# Playlist file for Phantom-Player
# https://www.phantom-player.com
#
"""


class SaveParams:
    class Section:
        _settings = "[SETTINGS]"
        _sources = "[SOURCES]"
        _videos = "[VIDEOS]"


def load(file_path: str) -> Playlist:
    """Load a playlist from a file."""
    print_debug(f"Path={file_path}")
    file_lines = __get_lines(file_path)

    playlist = Playlist()
    playlist.set_name(os.path.basename(file_path))

    __load_settings(playlist, file_lines)

    for playlist_path in __load_playlist_paths(file_lines):
        added = playlist.add_playlist_path(playlist_path)
        if not added:
            print_error(f'rejected path={file_path}')

    __load_videos(playlist, file_lines)

    return playlist


def save(playlist: Playlist) -> None:
    """Save a playlist to its local file."""
    if playlist.get_load_status() == LoadStatus._waiting_load:
        return

    print_debug(f"Saving... {playlist.get_name()}")

    if not os.path.exists(_SERIES_DIR):
        os.mkdir(_SERIES_DIR)

    data = _PLAYLIST_SETTINGS_HEADER

    #
    # Add the playlist data
    #
    data += "\n\n{}\n\n".format(SaveParams.Section._settings)
    for attr_name in _PLAYLIST_ATTR:
        value = getattr(playlist, "get_" + attr_name)()
        data += f"{attr_name}={value}\n"

    #
    # Add the source's data
    #
    data += f"\n\n{SaveParams.Section._sources}\n\n"
    for playlist_path in playlist.get_playlist_paths():
        data += __join_obj_attributes(playlist_path.get_path(), playlist_path, _PLAYLIST_PATH_ATTR)

    #
    # Add the video's data
    #
    data += f"\n\n{SaveParams.Section._videos}\n\n"
    for video in playlist.get_videos():
        data += __join_obj_attributes(video.get_hash(), video, _VIDEO_ATTR)

    # Write the file
    with open(playlist.get_save_path(), mode='w', encoding='utf-8') as f:
        f.write(data)


def __load_value_boolean(value: str, default: bool, param_name: str) -> bool:

    match value.lower().strip():
        case 'true':
            return True
        case 'false':
            return False
        case _:
            print_warning(f"\tError getting {param_name}")
            return default


def __load_value_int(value: str, default: int, param_name: str) -> int:
    try:
        return int(value)

    except ValueError:
        print_warning(f"\tError getting {param_name}")

    return default


def __load_settings(playlist: Playlist, file_lines: Sequence[str]) -> None:
    random = False
    keep_playing = False
    start_at = 0
    audio_track = 0
    subtitles_track = 0
    current_video_hash = ""

    for line in __get_section_content(file_lines, SaveParams.Section._settings):

        if _VALUE_SEPARATOR not in line:
            print_error(f"Error parsing header, line={line}")
            continue

        param_name = line.split(_VALUE_SEPARATOR)[0].strip()
        value = line.split(_VALUE_SEPARATOR)[1].strip()

        match param_name:

            case "random":
                random = __load_value_boolean(value, random, param_name)

            case "keep_playing":
                keep_playing = __load_value_boolean(value, keep_playing, param_name)

            case 'start_at':
                start_at = __load_value_int(value, start_at, param_name)

            case 'audio_track':
                audio_track = __load_value_int(value, audio_track, param_name)

            case 'subtitles_track':
                subtitles_track = __load_value_int(value, subtitles_track, param_name)

            case 'current_video_hash':
                current_video_hash = value

            case _:
                print_error(f"Error: wrong attr name on line={line}")

    #
    # Create the playlist (without loading the videos)
    #
    playlist.set_random(random)
    playlist.set_keep_playing(keep_playing)
    playlist.set_audio_track(audio_track)
    playlist.set_subtitles_track(subtitles_track)
    playlist.set_start_at(start_at)
    playlist.set_current_video_hash(current_video_hash)


def __load_playlist_paths(file_lines: Sequence[str]) -> list[PlaylistPath]:
    playlist_paths = []

    for line in __get_section_content(file_lines, SaveParams.Section._sources):

        recursive = False
        r_startup = False

        #
        # Read the data
        #
        columns = line.split(_COLUMN_SEPARATOR)

        data_path = columns[0].strip()
        if "/" not in data_path and "\\" not in data_path:
            print("\tError: invalid path", line)
            continue
        columns.pop(0)

        # Read the rest of the columns
        for column in columns:
            if _VALUE_SEPARATOR not in column:
                print("\tWarning: Path with invalid column.", line)

            param_name = column.split(_VALUE_SEPARATOR)[0].strip()
            value = column.split(_VALUE_SEPARATOR)[1].strip()

            match param_name:
                case "recursive":
                    recursive = __load_value_boolean(value, recursive, param_name)

                case "startup_discover":
                    r_startup = __load_value_boolean(value, r_startup, param_name)

                case _:
                    print("\tWarning: Path with ignored parameter", line)

        playlist_path = PlaylistPath(path=data_path,
                                     recursive=recursive,
                                     startup_discover=r_startup)

        playlist_paths.append(playlist_path)

    return playlist_paths


def __load_videos(playlist: Playlist, file_lines: Sequence[str]) -> None:
    imported_hash_paths = {}

    for line in __get_section_content(file_lines, SaveParams.Section._videos):

        path = ""
        name = ""
        progress = 0
        duration = 0
        rating = 0
        size = 0
        ignore = False

        #
        # Read the data
        #
        columns = line.split(_COLUMN_SEPARATOR)

        # Since hashes are the ID of videos, if there's no hash, the
        # video shall be rejected.
        hash_file = columns[0].strip()
        if len(hash_file) < _VIDEO_HASH_SIZE:
            print("\tError: Video with invalid hash.", line)
            continue

        columns.pop(0)

        # Read the rest of the columns
        for column in columns:
            if _VALUE_SEPARATOR not in column:
                print("\tWarning: Video with invalid column.", line)

            param_name = column.split(_VALUE_SEPARATOR)[0].strip()
            value = column.split(_VALUE_SEPARATOR)[1].strip()

            match param_name:
                case "path":
                    if "/" in value or "\\" in value:
                        path = value
                    else:
                        print("\tError: Video with invalid path.", line)
                        continue

                case "name":
                    name = value

                case "progress":
                    progress = __load_value_int(value, progress, param_name)

                case "duration":
                    duration = __load_value_int(value, duration, param_name)

                case "size":
                    size = __load_value_int(value, size, param_name)

                case 'rating':
                    rating = __load_value_int(value, rating, param_name)

                case "ignore":
                    ignore = __load_value_boolean(value, ignore, param_name)

                case _:
                    print("\tWarning: Video with ignored parameter", line)

        #
        # Check for valid lines
        #
        if path == "":
            print("\tError: Video without path.", line)
            continue

        # This test was removed to improve the time when starting the software.
        # Normally, this filter was already applied when importing the videos
        # for the first time.
        #
        # elif os.path.exists(path) and not __file_is_video(path, True):
        #    print("\t\tSkipping line because not video.", columns)
        #    continue

        elif path in imported_hash_paths.values():
            print("\tError: Video already path added", line)
            continue

        elif hash_file in imported_hash_paths.keys():
            print("\tError: Video hash already imported", hash_file)
            print("\t\tImported path:", imported_hash_paths[hash_file])
            print("\t\tSkipped path:", path)
            continue

        if os.path.exists(path):
            # This is only to have backwards compatibility with the new columns
            # while developing the software.

            if duration <= 0:
                duration = get_video_duration(path)

            if size <= 0:
                size = os.path.getsize(path)

        video = Video(vhash=hash_file, path=path, name=name)
        video.set_duration(duration)
        video.set_progress(progress)
        video.set_ignore(ignore)
        video.set_rating(rating)
        video.set_size(size)
        playlist.add_video(video)
        imported_hash_paths[hash_file] = path


def __join_obj_attributes(obj_id: str, obj: object, attr_list: Sequence[str]) -> str:
    line_data = obj_id
    for attr_name in attr_list:
        value = getattr(obj, "get_" + attr_name)()
        line_data += _COLUMN_SEPARATOR + f"{attr_name}={value}"

    return line_data + "\n"


def __get_section_content(file_lines: Sequence[str], section_name: str) -> list[str]:
    content = []

    section_found = False
    for line in file_lines:
        if line == section_name:
            section_found = True

        elif section_found:
            if line.startswith("["):
                break

            content.append(line)

    return content


def __get_lines(file_path: str) -> list[str]:
    with open(file_path, mode='rt', encoding='utf-8') as f:
        lines = f.readlines()

    clean_lines = []
    for line in lines:
        line = line.strip()

        if not line.startswith("#") and line != "":
            clean_lines.append(line)

    return clean_lines

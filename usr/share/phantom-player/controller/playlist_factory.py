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

from Paths import _SERIES_DIR
from settings import _VIDEO_HASH_SIZE
from model.Playlist import Playlist, LoadStatus
from model.PlaylistPath import PlaylistPath
from model.Video import Video
from vlc_utils import video_duration

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


class SaveParams:
    class Section:
        _settings = "[SETTINGS]"
        _sources = "[SOURCES]"
        _videos = "[VIDEOS]"


def str_to_boolean(value):
    return value.lower().strip() == "true"


def load(file_path):
    print("Loading...", file_path)
    file_lines = __get_lines(file_path)

    playlist = Playlist()
    playlist.set_name(os.path.basename(file_path))

    __load_settings(playlist, file_lines)

    for playlist_path in __load_paths(file_lines):
        added = playlist.add_playlist_path(playlist_path)
        if not added:
            print('\tError rejected path=' + file_path)

    __load_videos(playlist, file_lines)

    return playlist


def save(playlist):
    if playlist.get_load_status() == LoadStatus._waiting_load:
        return

    print("Saving... {}".format(playlist.get_name()))

    if not os.path.exists(_SERIES_DIR):
        os.mkdir(_SERIES_DIR)

    data = """
#
# Playlist file for Phantom-Player
# https://github.com/rsm-gh/phantom-player
#
"""

    #
    # Add the playlist data
    #
    data += "\n\n{}\n\n".format(SaveParams.Section._settings)
    for attr_name in _PLAYLIST_ATTR:
        value = getattr(playlist, "get_" + attr_name)()
        data += "{}={}\n".format(attr_name, value)

    #
    # Add the source's data
    #
    data += "\n\n{}\n\n".format(SaveParams.Section._sources)
    for playlist_path in playlist.get_playlist_paths():
        data += __join_line_attrs(playlist_path.get_path(), playlist_path, _PLAYLIST_PATH_ATTR)

    #
    # Add the video's data
    #
    data += "\n\n{}\n\n".format(SaveParams.Section._videos)
    for video in playlist.get_videos():
        data += __join_line_attrs(video.get_hash(), video, _VIDEO_ATTR)

    # Write the file
    with open(playlist.get_save_path(), mode='w', encoding='utf-8') as f:
        f.write(data)


def __load_settings(playlist, file_lines):
    random = False
    keep_playing = False
    start_at = 0
    audio_track = 0
    subtitles_track = 0
    current_video_hash = ""

    for line in __get_section_content(file_lines, SaveParams.Section._settings):

        if _VALUE_SEPARATOR not in line:
            print("Error parsing header, line=", line)
            continue

        param_name = line.split(_VALUE_SEPARATOR)[0].strip()
        value = line.split(_VALUE_SEPARATOR)[1].strip()

        match param_name:

            case "random":
                try:
                    random = str_to_boolean(value)
                except Exception:
                    print("\tError getting 'random'")

            case "keep_playing":
                try:
                    keep_playing = str_to_boolean(value)
                except Exception:
                    print("\tError getting 'keep_playing'")

            case 'start_at':
                try:
                    start_at = float(value)
                except Exception:
                    print("\tError getting 'start_at'")

            case 'audio_track':
                try:
                    audio_track = int(value)
                except Exception:
                    print("\tError getting 'audio_track'")

            case 'subtitles_track':
                try:
                    subtitles_track = int(value)
                except Exception:
                    print("\tError getting 'subtitles_track'")
                    subtitles_track = 0

            case 'current_video_hash':
                try:
                    current_video_hash = value
                except Exception:
                    print("\tError getting 'current_video_hash'")

            case _:
                print("Error: wrong attr name on line=", line)

    #
    # Create the playlist (without loading the videos)
    #
    playlist.set_random(random)
    playlist.set_keep_playing(keep_playing)
    playlist.set_audio_track(audio_track)
    playlist.set_subtitles_track(subtitles_track)
    playlist.set_start_at(start_at)
    playlist.set_current_video_hash(current_video_hash)


def __load_paths(file_lines):
    paths = []

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

            parameter = column.split(_VALUE_SEPARATOR)[0].strip()
            value = column.split(_VALUE_SEPARATOR)[1].strip()

            match parameter:
                case "recursive":
                    try:
                        recursive = str_to_boolean(value)
                    except Exception:
                        print("\tEWarning: Path with invalid recursive", line)

                case "startup_discover":
                    try:
                        r_startup = str_to_boolean(value)
                    except Exception:
                        print("\tWarning: Path with invalid startup_discover", line)

                case _:
                    print("\tWarning: Path with ignored parameter", line)

        playlist_path = PlaylistPath(path=data_path,
                                     recursive=recursive,
                                     startup_discover=r_startup)

        paths.append(playlist_path)

    return paths


def __load_videos(playlist, file_lines):
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

            parameter = column.split(_VALUE_SEPARATOR)[0].strip()
            value = column.split(_VALUE_SEPARATOR)[1].strip()

            match parameter:
                case "path":
                    if "/" in value or "\\" in value:
                        path = value
                    else:
                        print("\tError: Video with invalid path.", line)
                        continue

                case "name":
                    name = value

                case "progress":
                    try:
                        progress = int(value)
                    except Exception:
                        print("\tWarning: Video with invalid progress.", line)

                case "duration":
                    try:
                        duration = int(value)
                    except Exception:
                        print("\tWarning: Video with invalid duration.", line)

                case "size":
                    try:
                        size = int(value)
                    except Exception:
                        print("\tWarning: Video with invalid size.", line)

                case 'rating':
                    try:
                        rating = int(value)
                    except Exception:
                        print("\tError getting 'rating'")

                case "ignore":
                    try:
                        ignore = str_to_boolean(value)
                    except Exception:
                        print("\tWarning: Video with invalid ignore state", line)

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
                duration = video_duration(path)

            if size <= 0:
                size = os.path.getsize(path)

        video = Video(hash_file, path, duration, name)
        video.set_progress(progress)
        video.set_ignore(ignore)
        video.set_rating(rating)
        video.set_size(size)
        playlist.add_video(video)
        imported_hash_paths[hash_file] = path


def __join_line_attrs(obj_id, obj, attr_list):
    line_data = obj_id
    for attr_name in attr_list:
        value = getattr(obj, "get_" + attr_name)()
        line_data += _COLUMN_SEPARATOR + "{}={}".format(attr_name, value)

    return line_data + "\n"


def __get_section_content(lines, section_name):
    content = []

    section_found = False
    for line in lines:
        if line == section_name:
            section_found = True

        elif section_found:
            if line.startswith("["):
                break
            else:
                content.append(line)

    return content


def __get_lines(file_path):
    with open(file_path, mode='rt', encoding='utf-8') as f:
        lines = f.readlines()

    clean_lines = []
    for line in lines:
        line = line.strip()

        if not line.startswith("#") and line != "":
            clean_lines.append(line)

    return clean_lines

#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2015, 2024 Rafael Senties Martinelli.
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

import settings
from console_printer import print_error
from model.Playlist import Playlist
from model.Video import Video

class CurrentMedia:
    def __init__(self, playlist: None | Playlist=None) -> None:
        self._playlist = playlist
        self._video = None
        self.__video_cached_progress = 0

    def is_playlist(self, playlist: Playlist) -> bool:

        if self._playlist is None:
            return False

        return self._playlist.get_guid() == playlist.get_guid()

    def end_video_progress(self) -> None:

        if self._video is not None:
            self._video.end_progress()

    def set_video(self, video: Video) -> None:

        if self._playlist is None:
            return

        elif not self._playlist.has_video(video):
            print_error(f"video name={video.get_name()} hash={video.get_hash()} not found in playlist={self._playlist.get_name()}")

        self._video = video
        self.__video_cached_progress = self._video.get_progress()
        self._playlist.set_current_video_hash(video.get_hash())

    def set_video_progress(self, value: int) -> bool:

        if self._video is None:
            return False

        self._video.set_progress(value)

        if abs(self.__video_cached_progress - value) >= settings._SAVE_PLAYLISTS_SECONDS:
            self.__video_cached_progress = value
            return True

        return False


    def get_next_video(self) -> None | Video:

        if self._playlist is None:
            return None

        if self._playlist.get_random():
            video = self._playlist.get_next_random_video()
        else:
            video = self._playlist.get_next_organized_video(self._video)

        return video

    def get_video_ended(self) -> bool:

        if self._video is None:
            return True

        return self._video.ended()

    def get_video_hash(self) -> None | str:

        if self._video is None:
            return None

        return self._video.get_hash()

    def get_video_by_hash(self, video_hash: str) -> None | Video:

        if self._playlist is None:
            return None

        return self._playlist.get_video_by_hash(video_hash)
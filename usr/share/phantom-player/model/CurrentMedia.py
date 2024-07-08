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

class CurrentMedia:
    def __init__(self, playlist=None):
        self._playlist = playlist
        self._video = None

    def is_playlist(self, playlist):
        if self._playlist is not None:
            return self._playlist.get_guid() == playlist.get_guid()

        return False

    def get_next_video(self):

        if self._playlist.get_random():
            video = self._playlist.get_next_random_video()
        else:
            video = self._playlist.get_next_organized_video(self._video)

        self._video = video

        return video

    def current_video(self):
        return self._video

    def set_video_by_hash(self, video_hash):

        if self._playlist is None:
            return None

        self._video = self._playlist.get_video_by_hash(video_hash)
        return self._video

    def get_video_by_hash(self, video_hash):

        if self._playlist is None:
            return None

        return self._playlist.get_video_by_hash(video_hash)

    def get_video_hash(self):

        if self._video is None:
            return None

        return self._video.get_hash()

    def set_video_progress(self, value):

        if self._video is None:
            return

        self._video.set_progress(value)

    def get_video_percent(self):

        if self._video is None:
            return

        return self._video.get_percent()

    def get_video_ended(self):

        if self._video is None:
            return True

        return self._video.ended()


#!/usr/bin/python3
#

#  Copyright (C) 2014-2015, 2024 Rafael Senties Martinelli.
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

class CurrentMedia:
    def __init__(self, playlist=None):
        self._playlist = playlist
        self.__video = None

    def is_playlist(self, playlist):
        if self._playlist is not None:
            return self._playlist.get_id() == playlist.get_id()

        return False

    def get_next_video(self):

        if self._playlist.get_random():
            video = self._playlist.get_next_random_video()
        else:
            video = self._playlist.get_next_organized_video(self.__video)

        self.__video = video

        return video

    def current_video(self):
        return self.__video

    def get_video(self, video_name):

        if self._playlist is None:
            return None

        self.__video = self._playlist.get_video(video_name)
        return self.__video

    def get_video_id(self):

        if self.__video is None:
            return None

        return self.__video.get_id()

    def set_video_position(self, pos):

        if self.__video is None:
            return

        self.__video.set_position(pos)


    def get_video_progress(self):

        if self.__video is None:
            return

        return self.__video.get_progress()

#!/usr/bin/python3

#
#    This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024-2025 Rafael Senties Martinelli.
#
#  This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License 2.1 as
#   published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/lgpl-2.1.en.html>.
#

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
            video = self._playlist.get_next_ordered_video(self._video)

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


    def get_videos_by_hash(self, videos_hash: [str]) -> [Video]:

        if self._playlist is None:
            return []

        return self._playlist.get_videos_by_hash(videos_hash)
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

import os
import random

import Paths
import settings
from copy import copy
from model.Video import Video
from model.PlaylistPath import PlaylistPath
from system_utils import format_img

_SAVE_EXTENSION = '.cfg'


class LoadStatus:
    _waiting_load = 0  # Local file not yet loaded
    _loading = 1  # Discovering files
    _loaded = 2  # Files discovered


class TimeValue:
    _minium = 0
    _maximum = 59 * 60 + 59


class Track:
    class Value:
        _disabled = -1
        _undefined = 0

    class Type:
        _audio = 0
        _subtitles = 1
        _video = 2


class Playlist(object):

    def __init__(self) -> None:

        self.__number = -1
        self.__name = ""
        self.__playlist_paths = {}
        self.__random = False
        self.__keep_playing = False
        self.__hidden = False
        self.__start_at = 0
        self.__audio_track = Track.Value._undefined
        self.__subtitles_track = Track.Value._undefined
        self.__load_status = LoadStatus._waiting_load
        self.__current_video_hash = ""

        # Variables
        self.__videos_list = []
        self.__videos_dict = {}
        self.__active_videos_nb = 0

    def has_video(self, video:Video) -> bool:
        return video.get_hash() in self.__videos_dict

    def is_missing(self) -> bool:

        if len(self.__playlist_paths) == 0:
            return False  # Playlists without paths should be displayed

        for path in self.__playlist_paths.keys():
            if os.path.exists(path):
                return False

        return True

    def can_recursive(self, rec_playlist_path:PlaylistPath) -> bool:

        for playlist_path in self.__playlist_paths.values():

            if playlist_path.get_path() == rec_playlist_path.get_path():
                continue

            elif playlist_path.get_path().startswith(rec_playlist_path.get_path()):
                return False

        return True

    def restart(self) -> None:
        for video in self.__videos_list:
            video.set_progress(0)

    def move(self, videos:[Video], up:bool) -> None:

        if len(self.__videos_list) == 0 or len(videos) == 0:
            return

        if up:
            if videos[0].get_number() <= self.__videos_list[0].get_number():
                return

            step = -1 # move to top
        else:
            if videos[-1].get_number() >= self.__videos_list[-1].get_number():
                return

            step = 1 # move to bottom


        for video in videos:
            index = self.__videos_list.index(video)
            self.__videos_list.remove(video)
            self.__videos_list.insert(index + step, video)

        self.__recalculate_videos_nb()


    def reorder_by_name(self) -> None:
        """
            It is not possible to create a dictionary only by name
            because multiple episodes could have the same name.
        """
        videos_data = {"{}={}".format(video.get_name(), video.get_path()): video for video in self.__videos_list}
        self.__videos_list = []
        for key, value in sorted(videos_data.items()):
            self.__videos_list.append(value)

        self.__recalculate_videos_nb()

    def requires_discover(self, is_startup:bool) -> bool:

        auto_discover = False
        for playlist_path in self.get_playlist_paths():
            if playlist_path.get_startup_discover():
                auto_discover = True
                break

        if not is_startup or (is_startup and auto_discover):
            return True

        return False

    def remove_videos(self, videos:[Video]) -> None:
        for video in videos:
            self.__videos_list.remove(video)
            del self.__videos_dict[video.get_hash()]

        self.__recalculate_videos_nb()

    def update_playlist_path(self,
                             playlist_path:PlaylistPath,
                             new_path:str) -> PlaylistPath:

        self.__playlist_paths.pop(playlist_path.get_path())

        new_playlist_path = PlaylistPath(new_path,
                                         playlist_path.get_recursive(),
                                         playlist_path.get_startup_discover())
        self.__playlist_paths[new_playlist_path.get_path()] = new_playlist_path

        return new_playlist_path

    def remove_playlist_path(self,
                             playlist_path:PlaylistPath,
                             only_recursive_children:bool=False) -> None:
        """
            only_recursive_children is used to remove the list of
            videos when the user deactivates "Recursive".
        """
        remove_videos = self.get_videos_by_playlist_path(playlist_path, only_recursive_children)
        for video in remove_videos:
            self.__videos_list.remove(video)
            del self.__videos_dict[video.get_hash()]

        self.__recalculate_videos_nb()

        if not only_recursive_children:
            # The playlist path must be removed AFTER removing the videos.
            self.__playlist_paths.pop(playlist_path.get_path())

        return remove_videos

    def add_playlist_path(self, new_playlist_path: PlaylistPath) -> bool:

        for playlist_path in self.__playlist_paths.values():

            # if the path already exists
            if new_playlist_path.get_path() == playlist_path.get_path():
                return False

            # if the path is already included in a recursive path
            elif playlist_path.get_recursive() and new_playlist_path.get_path().startswith(playlist_path.get_path()):
                return False

        self.__playlist_paths[new_playlist_path.get_path()] = new_playlist_path

        return True

    def add_video(self, video:Video) -> None:

        if video.get_hash() in self.__videos_dict:
            raise ValueError(f"Attempting to add a duplicated video hash {video.get_hash()}")

        video.set_number(len(self.__videos_list) + 1)
        self.__videos_list.append(video)
        self.__videos_dict[video.get_hash()] = video
        self.__active_videos_nb += 1

    def get_path_stats(self, playlist_path:PlaylistPath) -> (int, int, int):

        active = 0
        ignored = 0
        missing = 0

        path = playlist_path.get_path()
        recursive = playlist_path.get_recursive()

        for video in self.__videos_list:

            video_dirname = os.path.dirname(video.get_path())

            if recursive:
                if not video_dirname.startswith(path):
                    continue

            elif video_dirname != path:
                continue

            if video.get_ignore():
                ignored += 1

            elif not video.exists():
                missing += 1

            else:
                active += 1

        return active, ignored, missing

    def get_load_status(self) -> int:
        return self.__load_status

    def get_guid(self) -> int:
        return self.__number

    def get_hidden(self) -> bool:
        return self.__hidden

    def get_playlist_path(self, path:str) -> PlaylistPath | None:
        try:
            return self.__playlist_paths[path]
        except KeyError:
            return None

    def get_playlist_paths(self) -> [PlaylistPath]:
        return [playlist_path for path, playlist_path in
                sorted(self.__playlist_paths.items(), key=lambda item: item[0])]

    def get_save_path(self) -> str:
        return os.path.join(Paths._SERIES_DIR, self.__name + _SAVE_EXTENSION)

    def get_start_at(self) -> int:
        return self.__start_at

    def get_icon_path(self, allow_default:bool=True) -> str | None:

        if self.__name != "":

            icon_path = os.path.join(Paths._SERIES_DIR, self.__name + ".png")

            if not allow_default:
                return icon_path

            elif os.path.exists(icon_path) and os.path.isfile(icon_path):
                return icon_path

        if allow_default:
            return Paths._ICON_LOGO_BIG

        return None

    def get_name(self) -> str:
        return self.__name

    def get_percent(self) -> int:

        total_of_videos = 0
        total_percent = 0
        for video in self.__videos_list:
            if not video.get_ignore():
                total_percent += video.get_percent()
                total_of_videos += 1

        if total_of_videos <= 0:
            return 0

        return int(round(total_percent / total_of_videos))

    def get_next_ordered_video(self, after=None):
        """
            Get the next video.

            If a video is provided, get the video next to this one, and
            if there is no next video to the one provided, go to the beginning.
        """

        after_found = False

        for video in self.__videos_list:

            if after is not None:
                if video == after:
                    after_found = True
                    continue

                elif not after_found:
                    continue

            if video.exists() and not video.ended() and not video.get_ignore():
                return video

        # Try to return a video from the beginning
        if after is not None:
            return self.get_next_ordered_video()

        return None

    def get_next_random_video(self) -> Video | None:

        videos = []
        for video in self.__videos_list:
            if not video.ended() and video.exists() and not video.get_ignore():
                videos.append(video)

        if not videos:
            return None

        elif len(videos) == 1:
            return videos[0]

        return random.choice(videos)

    def get_audio_track(self) -> int:
        return self.__audio_track

    def get_subtitles_track(self) -> int:
        return self.__subtitles_track

    def get_random(self) -> bool:
        return self.__random

    def get_current_video_hash(self) -> str:
        """This method is called by a getattr(), do not remove it."""
        return self.__current_video_hash

    def get_video_by_path(self, path: str) -> Video | None:
        for video in self.__videos_list:
            if video.get_path() == path:
                return video

        return None

    def get_video_by_hash(self, video_hash: str) -> Video | None:
        try:
            video = self.__videos_dict[video_hash]
        except KeyError:
            video = None

        return video

    def get_videos_by_hash(self, videos_hash: [str]) -> [Video]:
        videos = []

        for video_hash in videos_hash:
            try:
                video = self.__videos_dict[video_hash]
            except KeyError:
                pass
            else:
                videos.append(video)

        return videos

    def get_videos_by_playlist_path(self,
                                    playlist_path:PlaylistPath,
                                    only_recursive_children:bool=False) -> [Video]:
        """
            only_recursive_children is used to obtain the list of
            videos when the user deactivates "Recursive".
        """
        path = playlist_path.get_path()
        recursive = playlist_path.get_recursive()

        if path not in self.__playlist_paths.keys():
            return []

        videos = []
        for video in self.__videos_list:
            video_dirname = os.path.dirname(video.get_path())

            if video_dirname.startswith(path):

                if path == video_dirname:
                    if not only_recursive_children:
                        videos.append(video)

                elif recursive:
                    videos.append(video)

        return videos

    def get_last_played_video(self) -> Video | None:
        return self.get_video_by_hash(self.__current_video_hash)

    def get_videos(self) -> [Video, ...]:
        return copy(self.__videos_list)

    def get_keep_playing(self) -> bool:
        return self.__keep_playing

    def set_guid(self, value: int) -> None:
        self.__number = int(value)

    def set_hidden(self, value: bool) -> None:
        self.__hidden = value

    def set_load_status(self, value: LoadStatus) -> None:
        if value not in (LoadStatus._waiting_load, LoadStatus._loading, LoadStatus._loaded):
            raise ValueError("wrong value={}".format(value))

        self.__load_status = value

    def set_keep_playing(self, value: bool) -> None:
        self.__keep_playing = value

    def set_current_video_hash(self, value: str) -> None:
        self.__current_video_hash = str(value)

    def set_start_at(self, value: int) -> None:
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_start_at error:")
            print(str(e))
            value = 0

        if value > TimeValue._minium:
            if value > TimeValue._maximum:
                self.__start_at = TimeValue._maximum
            else:
                self.__start_at = value
        else:
            self.__start_at = TimeValue._minium

    def set_audio_track(self, value: int) -> None:
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_audio_track error:")
            print(str(e))
            value = Track.Value._undefined

        self.__audio_track = value

    def set_subtitles_track(self, value: int) -> None:
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_subtitles_track error:")
            print(str(e))
            value = Track.Value._undefined

        self.__subtitles_track = value

    def set_random(self, is_random: bool) -> None:
        self.__random = is_random

    def set_name(self, new_name: str, force: bool = False) -> None:
        """
            Set a new name, or rename.
        """
        if new_name.lower().endswith(_SAVE_EXTENSION):
            new_name = new_name.rsplit(".", 1)[0]

        if new_name == self.__name and not force:
            return

        elif self.__name == "":
            self.__name = new_name
            return

        old_icon_path = self.get_icon_path(allow_default=False)
        old_save_path = self.get_save_path()

        self.__name = new_name

        if os.path.exists(old_save_path):
            os.rename(old_save_path, self.get_save_path())

        if os.path.exists(old_icon_path):
            os.rename(old_icon_path, self.get_icon_path(allow_default=False))

    def set_icon_path(self, src_path: str) -> None:

        paste_path = self.get_icon_path(allow_default=False)
        if os.path.exists(src_path) and src_path == paste_path:
            return

        #
        # Remove the existent image
        #
        current_icon_path = self.get_icon_path(allow_default=False)
        if current_icon_path is not None and os.path.exists(current_icon_path):
            os.remove(self.get_icon_path(allow_default=False))

        #
        # Format the size & copy the new image
        #
        format_img(read_path=src_path,
                   write_path=self.get_icon_path(allow_default=False),
                   width=settings.IconSize.Big._width,
                   height=settings.IconSize.Big._height,
                   extension="png")

    def __recalculate_videos_nb(self) -> None:
        for i, video in enumerate(self.__videos_list, 1):
            video.set_number(i)

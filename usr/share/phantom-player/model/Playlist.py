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

import settings
import Paths
from copy import copy
from model.PlaylistPath import PlaylistPath
from system_utils import format_img

_SAVE_EXTENSION = '.cfg'


class LoadStatus:
    _waiting_load = 0 # Local file not yet loaded
    _loading = 1 # Discovering files
    _loaded = 2 # Files discovered


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

    def __init__(self):

        self.__number = -1
        self.__name = ""
        self.__playlist_paths = {}
        self.__random = False
        self.__keep_playing = False
        self.__start_at = 0.0
        self.__audio_track = Track.Value._undefined
        self.__subtitles_track = Track.Value._undefined
        self.__load_status = LoadStatus._waiting_load
        self.__current_video_hash = ""

        # Variables
        self.__videos_list = []
        self.__videos_dict = {}
        self.__active_videos_nb = 0

    def has_video(self, video):
        return video.get_hash() in self.__videos_dict

    def is_missing(self):

        if len(self.__playlist_paths) == 0:
            return False  # Playlists without paths should be displayed

        for path in self.__playlist_paths.keys():
            if os.path.exists(path):
                return False

        return True

    def can_recursive(self, rec_playlist_path):

        for playlist_path in self.__playlist_paths.values():

            if playlist_path.get_path() == rec_playlist_path.get_path():
                continue

            elif playlist_path.get_path().startswith(rec_playlist_path.get_path()):
                return False

        return True

    def restart(self):
        for video in self.__videos_list:
            video.set_progress(0)

    def reorder(self, new_order_indexes):
        """ Choices are "up" or "down" """

        self.__videos_list = [self.__videos_list[i - 1] for i in new_order_indexes]

        for i, video in enumerate(self.__videos_list, 1):
            video.set_number(i)

    def reorder_down(self, videos):
        """
            Move to the first indexes of the list.
        """
        if len(self.__videos_list) == 0 or len(videos) == 0:
            return

        # already in the last position
        elif videos[0].get_number() <= self.__videos_list[0].get_number():
            return

        for video in videos:
            index = self.__videos_list.index(video)
            self.__videos_list.remove(video)
            self.__videos_list.insert(index - 1, video)

        self.__recalculate_videos_nb()

    def reorder_up(self, videos):
        """
            Move to the last indexes of the list.
        """

        if len(self.__videos_list) == 0 or len(videos) == 0:
            return

        # already in the last position
        elif videos[-1].get_number() >= self.__videos_list[-1].get_number():
            return

        for video in reversed(videos):
            index = self.__videos_list.index(video)
            self.__videos_list.remove(video)
            self.__videos_list.insert(index + 1, video)

        self.__recalculate_videos_nb()

    def reorder_by_name(self):
        """
            It is not possible to create a dictionary only by name
            because multiple episodes could have the same name.
        """
        videos_data = {"{}={}".format(video.get_name(), video.get_path()): video for video in self.__videos_list}
        self.__videos_list = []
        for key, value in sorted(videos_data.items()):
            self.__videos_list.append(value)

        self.__recalculate_videos_nb()

    def requires_discover(self, is_startup):

        auto_discover = False
        for playlist_path in self.get_playlist_paths():
            if playlist_path.get_startup_discover():
                auto_discover = True
                break

        if not is_startup or (is_startup and auto_discover):
            return True

        return False

    def remove_videos(self, videos):
        for video in videos:
            self.__videos_list.remove(video)
            del self.__videos_dict[video.get_hash()]

        self.__recalculate_videos_nb()

    def update_playlist_path(self, playlist_path, new_path):
        self.__playlist_paths.pop(playlist_path.get_path())

        new_playlist_path = PlaylistPath(new_path,
                                         playlist_path.get_recursive(),
                                         playlist_path.get_startup_discover())
        self.__playlist_paths[new_playlist_path.get_path()] = new_playlist_path

        return new_playlist_path

    def remove_playlist_path(self, playlist_path, only_recursive_children=False):
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

    def add_playlist_path(self, new_playlist_path):

        for playlist_path in self.__playlist_paths.values():

            # if the path already exists
            if new_playlist_path.get_path() == playlist_path.get_path():
                return False

            # if the path is already included in a recursive path
            elif playlist_path.get_recursive() and new_playlist_path.get_path().startswith(playlist_path.get_path()):
                return False

        self.__playlist_paths[new_playlist_path.get_path()] = new_playlist_path

        return True

    def add_video(self, video):

        if video.get_hash() in self.__videos_dict:
            raise ValueError("Attempting to add a duplicated video hash "+video.get_hash())

        video.set_number(len(self.__videos_list) + 1)
        self.__videos_list.append(video)
        self.__videos_dict[video.get_hash()] = video
        self.__active_videos_nb += 1

    def get_path_stats(self, playlist_path):

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

    def get_load_status(self):
        return self.__load_status

    def get_guid(self):
        return self.__number

    def get_playlist_path(self, path):
        try:
            return self.__playlist_paths[path]
        except KeyError:
            return None

    def get_playlist_paths(self):
        return [playlist_path for path, playlist_path in
                sorted(self.__playlist_paths.items(), key=lambda item: item[0])]

    def get_save_path(self):
        return os.path.join(Paths._SERIES_DIR, self.__name + _SAVE_EXTENSION)

    def get_start_at(self):
        return self.__start_at

    def get_icon_path(self, allow_default=True):

        if self.__name != "":

            icon_path = os.path.join(Paths._SERIES_DIR, self.__name + ".png")

            if not allow_default:
                return icon_path

            elif os.path.exists(icon_path) and os.path.isfile(icon_path):
                return icon_path

        if allow_default:
            return Paths._ICON_LOGO_BIG

        return None

    def get_name(self):
        return self.__name

    def get_percent(self):

        total_of_videos = 0
        total_percent = 0
        for video in self.__videos_list:
            if not video.get_ignore():
                total_percent += video.get_percent()
                total_of_videos += 1

        if total_of_videos <= 0:
            return 0

        return int(round(total_percent / total_of_videos))

    def get_next_organized_video(self, after=None):
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
            return self.get_next_organized_video()

        return None

    def get_next_random_video(self):

        videos = []
        for video in self.__videos_list:
            if not video.ended() and video.exists() and not video.get_ignore():
                videos.append(video)

        if not videos:
            return None

        elif len(videos) == 1:
            return videos[0]

        return random.choice(videos)

    def get_audio_track(self):
        return self.__audio_track

    def get_subtitles_track(self):
        return self.__subtitles_track

    def get_random(self):
        return self.__random

    def get_current_video_hash(self):
        """This method is called by a getattr(), do not remove it."""
        return self.__current_video_hash

    def get_video_by_path(self, path):
        for video in self.__videos_list:
            if video.get_path() == path:
                return video

        return None

    def get_video_by_hash(self, video_hash):
        try:
            video = self.__videos_dict[video_hash]
        except KeyError:
            video = None

        return video

    def get_videos_by_hash(self, videos_hashes):
        videos = []

        for video_hash in videos_hashes:
            try:
                video = self.__videos_dict[video_hash]
                videos.append(video)
            except KeyError:
                pass

        return videos

    def get_videos_by_playlist_path(self, playlist_path, only_recursive_children=False):
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

    def get_last_played_video(self):
        return self.get_video_by_hash(self.__current_video_hash)

    def get_videos(self):
        return copy(self.__videos_list)

    def get_keep_playing(self):
        return self.__keep_playing

    def set_guid(self, value):
        self.__number = value

    def set_load_status(self, value):
        if value not in (LoadStatus._waiting_load, LoadStatus._loading, LoadStatus._loaded):
            raise ValueError("wrong value={}".format(value))

        self.__load_status = value

    def set_keep_playing(self, value):
        self.__keep_playing = value

    def set_current_video_hash(self, value):
        self.__current_video_hash = value

    def set_start_at(self, value):
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

    def set_audio_track(self, value):
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_audio_track error:")
            print(str(e))
            value = Track.Value._undefined

        self.__audio_track = value

    def set_subtitles_track(self, value):
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_subtitles_track error:")
            print(str(e))
            value = Track.Value._undefined

        self.__subtitles_track = value

    def set_random(self, is_random):
        self.__random = is_random

    def set_name(self, new_name, force=False):
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

    def set_icon_path(self, src_path):

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

    def __recalculate_videos_nb(self):
        for i, video in enumerate(self.__videos_list, 1):
            video.set_number(i)

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

import os
import random

import settings
import Paths
from model.Video import VideoPosition
from system_utils import format_img

_SAVE_EXTENSION = '.cfg'


class LoadStatus:
    _waiting_load = 0
    _loading = 1
    _loaded = 2


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
        _spu = 2


class Playlist(object):

    def __init__(self):

        self.__guid = -1
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
        self.__videos_instances = []
        self.__active_videos_nb = 0

    def restart(self):
        for video in self.__videos_instances:
            video.set_position(VideoPosition._start)

    def reorder(self, new_order_indexes):
        """ Choices are "up" or "down" """

        self.__videos_instances = [self.__videos_instances[i - 1] for i in new_order_indexes]

        for i, video in enumerate(self.__videos_instances, 1):
            video.set_guid(i)

    def remove_videos(self, videos):
        for video in videos:
            self.__videos_instances.remove(video)

        self.__recalculate_videos_guid()

    def __recalculate_videos_guid(self):
        for i, video in enumerate(self.__videos_instances, 1):
            video.set_guid(i)

    def remove_playlist_path(self, playlist_path):

        path = playlist_path.get_path()
        recursive = playlist_path.get_recursive()

        if path not in self.__playlist_paths.keys():
            return []

        self.__playlist_paths.pop(path)

        removed_videos = []
        for video in self.__videos_instances:
            video_dirname = os.path.dirname(video.get_path())
            if recursive:
                if video_dirname.startswith(path):
                    removed_videos.append(video)

            elif path == video_dirname:
                removed_videos.append(video)

        for video in removed_videos:
            self.__videos_instances.remove(video)

        self.__recalculate_videos_guid()

        return removed_videos

    def remove_recursive_videos(self, playlist_path):

        path = playlist_path.get_path()

        if path not in self.__playlist_paths.keys():
            return []

        removed_videos = []
        for video in self.__videos_instances:

            video_dirname = os.path.dirname(video.get_path())

            if video_dirname == path:
                pass  # only children shall be removed

            elif video_dirname.startswith(path):
                removed_videos.append(video)

        for video in removed_videos:
            self.__videos_instances.remove(video)

        self.__recalculate_videos_guid()

        return removed_videos

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
        video.set_guid(len(self.__videos_instances) + 1)
        self.__videos_instances.append(video)
        self.__active_videos_nb += 1

    def clean_videos(self):
        """Delete the hidden and un-existing videos"""

        videos = []
        for video in self.__videos_instances:
            if not os.path.exists(video.get_path()) and video.get_ignore():
                pass
            else:
                videos.append(video)

        self.__videos_instances = videos

    def update_not_hidden_videos(self):
        self.__active_videos_nb = len([0 for video in self.__videos_instances if video.get_ignore()])

    def has_existent_paths(self):
        for path in self.__playlist_paths.keys():
            if os.path.exists(path):
                return True

        return False

    def can_recursive(self, rec_playlist_path):

        for playlist_path in self.__playlist_paths.values():

            if playlist_path.get_path() == rec_playlist_path.get_path():
                continue

            elif playlist_path.get_path().startswith(rec_playlist_path.get_path()):
                return False

        return True

    def get_path_stats(self, playlist_path):

        active = 0
        ignored = 0
        missing = 0

        path = playlist_path.get_path()
        recursive = playlist_path.get_recursive()

        for video in self.__videos_instances:

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
        return self.__guid

    def get_linked_videos(self, path):

        try:
            playlist_path = self.__playlist_paths[path]
        except KeyError:
            return []

        recursive = playlist_path.get_recursive()
        media_path = playlist_path.get_path()

        linked_videos = []
        for video in self.__videos_instances:

            if recursive and video.get_path().startswith(media_path):
                linked_videos.append(video)

            elif os.path.dirname(video.get_path()) == media_path:
                linked_videos.append(video)

        return linked_videos

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

        if allow_default:
            if not self.get_load_status():
                return Paths._ICON_LOADING_PLAYLIST

        if self.__name != "":

            icon_path = os.path.join(Paths._SERIES_DIR, self.__name + ".png")

            if not allow_default:
                return icon_path

            elif os.path.exists(icon_path) and os.path.isfile(icon_path):
                return icon_path

        if allow_default:
            return Paths._ICON_LOGO_MEDIUM

        return None

    def get_name(self):
        return self.__name

    def get_first_video(self):
        if len(self.__videos_instances) <= 0:
            return None

        return self.__videos_instances[0]

    def get_progress(self):

        total_of_videos = 0
        total_percent = 0
        for video in self.__videos_instances:
            if not video.get_ignore():
                total_percent += video.get_progress()
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

        for video in self.__videos_instances:

            if after is not None:
                if video == after:
                    after_found = True
                    continue

                elif not after_found:
                    continue

            if video.exists() and not video.get_played() and not video.get_ignore():
                return video

        # Try to return a video from the beginning
        if after is not None:
            return self.get_next_organized_video()

        return None

    def get_next_random_video(self):

        videos = []
        for video in self.__videos_instances:
            if not video.get_played() and video.exists() and not video.get_ignore():
                videos.append(video)

        if not videos:
            return None

        elif len(videos) == 1:
            return videos[0]

        return random.choice(videos)

    def get_videos_nb(self):
        return self.__active_videos_nb

    def get_audio_track(self):
        return self.__audio_track

    def get_subtitles_track(self):
        return self.__subtitles_track

    def get_random(self):
        return self.__random

    def get_video_by_guid(self, video_guid):
        for video in self.__videos_instances:
            if video.get_guid() == video_guid:
                return video

        return None

    def get_video_by_hash(self, video_hash):
        for video in self.__videos_instances:
            if video.get_hash() == video_hash:
                return video

        return None

    def get_videos_by_guid(self, videos_guid):
        videos = []

        for video_guid in videos_guid:
            video = self.get_video_by_guid(video_guid)
            if video is not None:
                videos.append(video)

        return videos

    def get_last_played_video_guid(self):

        if self.__current_video_hash == "":
            return None

        for video in self.__videos_instances:
            if video.get_hash() == self.__current_video_hash:
                return video.get_guid()

        return None

    def get_videos(self):
        return self.__videos_instances

    def get_keep_playing(self):
        return self.__keep_playing

    def get_current_video_hash(self):
        return self.__current_video_hash

    def set_guid(self, value):
        self.__guid = value

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
                   width=settings._DEFAULT_IMG_WIDTH,
                   height=settings._DEFAULT_IMG_HEIGHT,
                   extension="png")

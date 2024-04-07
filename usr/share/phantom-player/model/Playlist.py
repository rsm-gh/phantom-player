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

    def __init__(self,
                 pid,
                 name="",
                 is_random=False,
                 keep_playing=True,
                 start_at=0,
                 audio_track=Track.Value._undefined,
                 subtitles_track=Track.Value._undefined,
                 current_video_hash=""):

        self.__id = pid
        self.__name = ""

        self.__playlist_paths = {}
        self.__random = False
        self.__keep_playing = False
        self.__start_at = 0.0
        self.__audio_track = Track.Value._undefined
        self.__subtitles_track = Track.Value._undefined
        self.__loaded = False

        self.__current_video_hash = current_video_hash

        self.set_name(name)

        self.set_random(is_random)
        self.set_keep_playing(keep_playing)
        self.set_audio_track(audio_track)
        self.set_subtitles_track(subtitles_track)
        self.set_start_at(start_at)

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
            video.set_id(i)

    def update_ids(self):
        for i, video in enumerate(self.__videos_instances, 1):
            video.set_id(i)

    def remove_playlist_path(self, playlist_path, only_recursive=False):

        path = playlist_path.get_path()

        if path not in self.__playlist_paths.keys():
            return []

        if not only_recursive:
            self.__playlist_paths.pop(path)

        removed_videos = []
        for video in self.__videos_instances:

            video_dirname = os.path.dirname(video.get_path())

            print(path, video_dirname, only_recursive, path == video_dirname)

            if only_recursive:
                if video_dirname == path:
                    pass # only children shall be removed

                elif video_dirname.startswith(video_dirname):
                    removed_videos.append(video)

            elif video_dirname == video_dirname:
                removed_videos.append(video)

        for video in removed_videos:
            self.__videos_instances.remove(video)

        self.update_ids()

        return removed_videos



    def add_playlist_path(self, playlist_path):
        if playlist_path.get_path() in self.__playlist_paths.keys():
            return False

        self.__playlist_paths[playlist_path.get_path()] = playlist_path

        return True

    def add_video(self, video):
        video.set_id(len(self.__videos_instances) + 1)
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

    def missing_videos(self, videos_id):
        """Return if from the selected videos there is someone missing"""

        for vid in videos_id:
            for video in self.__videos_instances:
                if video.get_id() == vid and not os.path.exists(video.get_path()):
                    return True

        return False

    def ignore_video(self, video_name):

        for video in self.__videos_instances:
            if video.get_name() == video_name:

                if os.path.exists(video.get_path()):
                    video.set_ignore(True)
                else:
                    self.__videos_instances.remove(video)

                self.__active_videos_nb -= 1
                self.update_ids()
                self.update_not_hidden_videos()

                break

    def dont_ignore_video(self, video_name):
        for video in self.__videos_instances:
            if video.get_name() == video_name:
                video.set_ignore(False)

                self.__active_videos_nb -= 1
                self.update_ids()
                self.update_not_hidden_videos()

                return video

        return None

    def find_video(self, video_id, new_path):
        """
            Try to find videos other videos in case
            the name of an extension changed, or the start part
            of the video.

            Ex 1:
                foo.ogg -> foo
                faa.ogg -> faa
            Or
                Videos-video700 -> video700
                videos-video800 -> video800

        Could this be more powerful and search other kinds of string sequences?

            ex:
                video-VIDEO700 -> video-video700
                video-VIDEO800 -> video-video800

        """

        #
        #    change the path of the selected video
        #
        video = self.get_video(video_id)
        video_name = video.get_name()

        if video is None:
            return

        video.set_path(new_path)

        # Find the pattern
        new_name = os.path.basename(new_path).strip()
        old_name = video_name.strip()

        len_new_name = len(new_name)
        len_old_name = len(video_name)

        found_videos = 0
        if new_name in old_name or old_name in new_name:

            if len_new_name > len_old_name:
                patt = new_name.replace(old_name, '')

                # Check if there are other missing videos with the same pattern
                for video in self.__videos_instances:
                    if not os.path.exists(video.get_path()):
                        video_name = video.get_name()
                        video_path = video.get_path()
                        basedir = os.path.dirname(video_path) + "/"
                        basedir.replace("//", "/")

                        if os.path.exists(basedir + patt + video_name):
                            video.set_path(basedir + patt + video_name)
                            found_videos += 1

                        elif os.path.exists(video_path + patt):
                            video.set_path(video_path + patt)
                            found_videos += 1


            elif len_old_name > len_new_name:
                patt = old_name.replace(new_name, '')

                # Check if there are other missing videos with the same pattern
                for video in self.__videos_instances:
                    if not os.path.exists(video.get_path()):

                        possible_path = video.get_path().replace(patt, '')

                        if os.path.exists(possible_path):
                            video.set_path(possible_path)
                            found_videos += 1

            if found_videos > 0:
                return found_videos
            else:
                return False

    def find_videos(self, path):

        video_counter = 0
        for video in self.__videos_instances:
            if not os.path.exists(video.get_path()):
                full_path = os.path.join(path, video.get_full_name())
                if os.path.exists(full_path):
                    video_counter += 1
                    video.set_path(full_path)

        return video_counter

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

    def get_loaded(self):
        return self.__loaded

    def get_id(self):
        return self.__id

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
        path = os.path.join(Paths._SERIES_DIR, self.__name)
        if not path.lower().endswith(".csv"):
            path += ".csv"

        return path

    def get_start_at(self):
        return self.__start_at

    def get_icon_path(self, allow_default=True):

        if allow_default:
            if not self.get_loaded():
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

    def get_nb_videos(self):
        return self.__active_videos_nb

    def get_audio_track(self):
        return self.__audio_track

    def get_subtitles_track(self):
        return self.__subtitles_track

    def get_random(self):
        return self.__random

    def get_video(self, video_id):
        for video in self.__videos_instances:
            if video.get_id() == video_id:
                return video

        return None

    def get_last_played_video_id(self):

        if self.__current_video_hash == "":
            return None

        for video in self.__videos_instances:
            if video.get_hash() == self.__current_video_hash:
                return video.get_id()

        return None

    def get_videos(self):
        return self.__videos_instances

    def get_keep_playing(self):
        return self.__keep_playing

    def get_current_video_hash(self):
        return self.__current_video_hash

    def set_loaded(self, value):
        self.__loaded = value

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

    def set_video_position(self, video_to_find, position):
        for video in self.__videos_instances:
            if video_to_find.get_id() == video.get_id():
                video.set_position(position)
                return

    def set_name(self, new_name, force=False):
        """
            Set a new name, or rename.
        """
        if new_name.lower().endswith(".csv"):
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



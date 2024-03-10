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
import csv
import shutil
import random

from Paths import _ICON_LOGO_MEDIUM, _SERIES_DIR
from model.Video import VideoPosition

class Track:
    class Value:
        disabled = -1
        undefined = 0

    class Type:
        audio = 0
        subtitles = 1
        spu = 2

class Playlist(object):

    def __init__(self,
                 name="",
                 data_path="",
                 icon_extension="",
                 recursive=False,
                 r_startup=False,
                 is_random=False,
                 keep_playing=True,
                 start_at=0.0,
                 audio_track=Track.Value.undefined,
                 subtitles_track=Track.Value.undefined):

        self.__name = ""
        self.__icon_extension = icon_extension
        self.__data_path = data_path

        self.__recursive = False
        self.__random = False
        self.__r_startup = False

        self.__keep_playing = False
        self.__start_at = 0.0
        self.__audio_track = Track.Value.undefined
        self.__subtitles_track = Track.Value.undefined

        self.set_name(name)
        self.set_recursive(recursive)
        self.set_r_startup(r_startup)

        self.set_random(is_random)
        self.set_keep_playing(keep_playing)
        self.set_audio_track(audio_track)
        self.set_subtitles_track(subtitles_track)
        self.set_start_at(start_at)

        # Variables
        self.__videos_instances = []
        self.__active_videos_nb = 0

    def save(self):

        if not os.path.exists(_SERIES_DIR):
            os.mkdir(_SERIES_DIR)

        with open(self.get_save_path(), mode='wt', encoding='utf-8') as f:
            csv_list = csv.writer(f, delimiter='|')

            csv_list.writerow([self.__random,
                               self.__keep_playing,
                               self.__start_at,
                               self.__audio_track,
                               self.__subtitles_track,
                               self.__icon_extension])

            csv_list.writerow([self.__data_path, self.__recursive, self.__r_startup])

            for video in self.__videos_instances:
                csv_list.writerow([video.get_id(),
                                   video.get_path(),
                                   video.get_name(),
                                   video.get_position(),
                                   video.get_ignore()])

    def restart(self):
        for video in self.__videos_instances:
            video.set_position(VideoPosition.start)

        self.save()

    def reorder(self, new_order_indexes):
        """ Choices are "up" or "down" """

        self.__videos_instances = [self.__videos_instances[i - 1] for i in new_order_indexes]

        for i, video in enumerate(self.__videos_instances, 1):
            video.set_id(i)

        self.save()

    def update_ids(self):
        for i, video in enumerate(self.__videos_instances, 1):
            video.set_id(i)

    def add_video(self, video):

        if video.get_id() == -1:
            video.set_id(len(self.__videos_instances) + 1)

        self.__videos_instances.append(video)
        self.__active_videos_nb += 1

    def clean_videos(self):

        videos = []
        for video in self.__videos_instances:
            if not os.path.exists(video.get_path()) and video.get_ignore():
                '''Delete the hidden and un-existing videos'''
            else:
                videos.append(video)

        self.__videos_instances = videos

    def update_not_hidden_videos(self):
        self.__active_videos_nb = len([0 for video in self.__videos_instances if video.get_ignore()])

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
                self.save()

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

    def find_playlist(self, path):
        self.__data_path = path
        self.find_videos(path)
        self.update_not_hidden_videos()
        self.save()

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

            self.save()

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

        if video_counter > 0:
            self.save()

        return video_counter

    def get_save_path(self):
        path = os.path.join(_SERIES_DIR, self.__name)
        if not path.lower().endswith(".csv"):
            path += ".csv"

        return path

    def get_start_at(self):
        return self.__start_at

    def get_icon_path(self, allow_default=True):

        if self.__name != "":

            icon_path = os.path.join(_SERIES_DIR, self.__name + "." + self.__icon_extension)

            if not allow_default:
                return icon_path

            elif os.path.exists(icon_path) and os.path.isfile(icon_path):
                return icon_path

        if allow_default:
            return _ICON_LOGO_MEDIUM

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

            if video.exists() and not video.get_was_played() and not video.get_ignore():
                return video

        # Try to return a video from the beginning
        if after is not None:
            return self.get_next_organized_video()

        return None

    def get_next_random_video(self):

        videos = []
        for video in self.__videos_instances:
            if not video.get_was_played() and video.exists() and not video.get_ignore():
                videos.append(video)

        if not videos:
            return None

        elif len(videos) == 1:
            return videos[0]

        return random.choice(videos)

    def get_nb_videos(self):
        return self.__active_videos_nb

    def get_data_path(self):
        return self.__data_path

    def get_audio_track(self):
        return self.__audio_track

    def get_subtitles_track(self):
        return self.__subtitles_track

    def get_random(self):
        return self.__random

    def get_recursive(self):
        return self.__recursive

    def get_r_startup(self):
        return self.__r_startup

    def get_video(self, video_id):
        for video in self.__videos_instances:
            if video.get_id() == video_id:
                return video

        return None

    def get_videos(self):
        return self.__videos_instances

    def get_keep_playing(self):
        return self.__keep_playing

    def set_keep_playing(self, value):
        self.__keep_playing = value

    def set_start_at(self, value):
        try:
            value = float(value)
        except Exception as e:
            print(self.__name)
            print("set_start_at error:")
            print(str(e))
            value = 0.0

        if value > 0:
            self.__start_at = value
        else:
            self.__start_at = 0.0

    def set_recursive(self, recursive):
        self.__recursive = recursive

    def set_audio_track(self, value):
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_audio_track error:")
            print(str(e))
            value = Track.Value.undefined

        self.__audio_track = value

    def set_subtitles_track(self, value):
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_subtitles_track error:")
            print(str(e))
            value = Track.Value.undefined

        self.__subtitles_track = value

    def set_random(self, is_random):
        self.__random = is_random

    def set_r_startup(self, r_startup):
        self.__r_startup = r_startup

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

    def set_icon_path(self, path):

        #
        # Remove the existent image
        #
        current_icon_path = self.get_icon_path(allow_default=False)
        if current_icon_path is not None and os.path.exists(current_icon_path):
            os.remove(self.get_icon_path(allow_default=False))

        #
        # Set the new image
        #

        file_name = os.path.basename(path)

        if '.' in file_name:
            self.__icon_extension = file_name.rsplit(".", 1)[1]
        else:
            self.__icon_extension = ""

        if os.path.exists(path):
            shutil.copy2(path, self.get_icon_path(allow_default=False))

    def set_data_path(self, path):
        self.__data_path = path

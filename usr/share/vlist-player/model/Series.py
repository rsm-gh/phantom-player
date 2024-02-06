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

import os  # why is os not being detected on pycharm?
import gi
import csv
import magic
import shutil
import random

gi.require_version('Gtk', '3.0')
from gi.repository.GdkPixbuf import Pixbuf

from Paths import *
from model.Video import Video, path_is_video, generate_list_from_videos_folder

MAGIC_MIMETYPE = magic.open(magic.MAGIC_MIME)
MAGIC_MIMETYPE.load()


class Series(object):

    def __init__(self,
                 path,
                 data_path,
                 recursive,
                 is_random,
                 keep_playing,
                 start_at=0.0,
                 audio_track=-2,
                 subtitles_track=-2):

        self.__path = path
        self.__name = os.path.basename(path)
        self.__recursive = False
        self.__random = False
        self.__keep_playing = False
        self.__start_at = 0.0
        self.__audio_track = -2
        self.__subtitles_track = -2

        self.set_recursive(recursive, False)
        self.set_random(is_random, False)
        self.set_keep_playing(keep_playing, False)
        self.set_audio_track(audio_track, False)
        self.set_subtitles_track(subtitles_track, False)
        self.set_start_at(start_at, False)

        # Variables
        self.__videos_instances = []
        self.__nb_videos = 0
        self.__series_img_size = 30
        self.__series_pixbuf = None
        self.__load_image()

        # change the name of the series in case it has been renamed.
        if data_path and os.path.exists(data_path):
            file_name = os.path.basename(data_path)
            if file_name[:-4] != self.__name:
                self.__name = file_name[:-4]

        if os.path.exists(SERIES_PATH.format(self.__name)):

            """
                Get the number of rows of the file, this is important in case there be an error with the id's
            """
            number_of_rows = 0
            if os.path.exists(SERIES_PATH.format(self.__name)):
                with open(SERIES_PATH.format(self.__name), mode='rt', encoding='utf-8') as f:
                    number_of_rows = len(f.readlines())

            """
                Load the videos (and their data) from the program files
            """
            with open(SERIES_PATH.format(self.__name), mode='rt', encoding='utf-8') as f:
                rows = csv.reader(f, delimiter='|')
                next(f)
                for row in rows:
                    try:
                        path = row[1].strip()
                    except Exception:
                        print("error getting the path")
                        path = False

                    """
                        check for duplicates
                    """
                    if path and not any(
                            path == video.get_path() for video in self.__videos_instances) and path_is_video(path,
                                                                                                             True):
                        try:
                            video_id = int(row[0])
                        except Exception:
                            print("error getting the id")
                        else:
                            """
                                check if the Id has already been used
                            """
                            for video in self.__videos_instances:
                                if video_id == video.get_id():
                                    # Send the video to the end
                                    number_of_rows += 1
                                    video_id = number_of_rows
                                    print("Incrementing duplicated id")

                            try:
                                play = row[2]
                            except Exception:
                                play = 'true'

                            try:
                                o_played = row[3]
                            except Exception:
                                o_played = 'false'

                            try:
                                r_played = row[4]
                            except Exception:
                                r_played = 'false'

                            try:
                                position = float(row[5])
                            except Exception:
                                position = 0.0

                            try:
                                display = row[6]
                            except Exception:
                                display = 'true'

                            video = Video(path, video_id)
                            video.load_info(play, o_played, r_played, position, display)

                            self.__videos_instances.append(video)
                            self.__nb_videos += 1

        """
            Get the videos from the folder. This will find new videos.
        """
        for video_path in generate_list_from_videos_folder(self.__path, self.__recursive):
            if not any(video_path == video.get_path() for video in self.__videos_instances):

                self.__nb_videos += 1
                new_video = Video(video_path, self.__nb_videos)

                if os.path.exists(new_video.get_path()):
                    new_video.set_state_new()
                else:
                    # In case it is a broken link:
                    new_video.update_state()

                self.__videos_instances.append(new_video)

        self.clean_episodes()
        self.update_ids()  # this is in case there were videos with duplicated ids
        self.write_data()

    def write_data(self):

        if not os.path.exists(FOLDER_LIST_PATH):
            os.mkdir(FOLDER_LIST_PATH)

        with open(SERIES_PATH.format(self.__name), mode='wt', encoding='utf-8') as f:
            csv_list = csv.writer(f, delimiter='|')

            csv_list.writerow([self.__path,
                               self.__recursive,
                               self.__random,
                               self.__keep_playing,
                               self.__start_at,
                               self.__audio_track,
                               self.__subtitles_track])

            for video in self.__videos_instances:
                csv_list.writerow([video.get_id(),
                                   video.get_path(),
                                   video.get_play(),
                                   video.get_o_played(),
                                   video.get_r_played(),
                                   video.get_position(),
                                   video.get_display()])

    def rename(self, new_name):
        # update the data file
        if os.path.exists(SERIES_PATH.format(self.__name)):
            os.rename(SERIES_PATH.format(self.__name), SERIES_PATH.format(new_name))

        # update the class
        self.__name = new_name

    def find_series(self, path):
        self.__path = path
        self.__load_image()
        self.find_videos(path)
        self.update_not_hidden_videos()
        self.write_data()

    def find_video(self, episode_name, new_path):
        """     
            Try to find videos other videos in case
            the name of an extension changed, or the start part
            of the episode.
            
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

        """
            change the path of the selected episode
        """
        for episode in self.__videos_instances:
            if episode_name == episode.get_name():
                episode.set_path(new_path)
                break

        # Find the pattern

        new_name = os.path.basename(new_path).strip()
        old_name = episode_name.strip()

        len_new_name = len(new_name)
        len_old_name = len(episode_name)

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

            self.write_data()

            if found_videos > 0:
                return found_videos
            else:
                return False

    def update_not_hidden_videos(self):
        self.__nb_videos = len([0 for video in self.__videos_instances if video.get_display()])

    def find_videos(self, path):

        path = path + '/'
        path.replace('//', '/')

        video_counter = 0
        for video in self.__videos_instances:
            if not os.path.exists(video.get_path()):
                if os.path.exists(path + video.get_name()):
                    video_counter += 1
                    video.set_path(path + video.get_name())

        if video_counter > 0:
            self.write_data()

        return video_counter

    def ignore_video(self, del_video):
        """ Ignore a video from the series by giving its name.
        """

        for video in self.__videos_instances:
            if video.get_name() == del_video:

                if os.path.exists(video.get_path()):
                    video.set_display(False)
                else:
                    self.__videos_instances.remove(video)

                self.__nb_videos -= 1
                self.update_ids()
                self.write_data()

                self.update_not_hidden_videos()

                break

    def dont_ignore_video(self, video_name):
        for video in self.__videos_instances:
            if video.get_name() == video_name:
                video.set_display(True)

                self.__nb_videos -= 1
                self.update_ids()
                self.write_data()

                self.update_not_hidden_videos()

                break

    def missing_videos(self, episodes_names):
        """Return if from the selected videos there is someone missing"""
        for episode_name in episodes_names:
            for episode in self.__videos_instances:
                if episode.get_name() == episode_name:
                    if not os.path.exists(episode.get_path()):
                        return True

        return False

    def clean_episodes(self):

        videos = []
        for video in self.__videos_instances:
            if video and not os.path.exists(video.get_path()) and not video.get_display():
                '''Delete the hidden and un-existing videos'''
            else:
                videos.append(video)

        self.__videos_instances = videos

    def reorder(self, new_order_indexes):
        """ Choices are "up" or "down" """

        self.__videos_instances = [self.__videos_instances[i - 1] for i in new_order_indexes]

        for i, video in enumerate(self.__videos_instances, 1):
            video.set_id(i)

        self.write_data()

    def change_checkbox_state(self, episode_names, column, state):

        if isinstance(episode_names, str):
            episode_names = [episode_names]

        for episode_name in episode_names:
            for video in self.__videos_instances:

                if video.get_name() == episode_name:

                    if column == 4:
                        video.set_play(state)
                    elif column == 5:
                        video.set_o_played(state)
                    elif column == 6:
                        video.set_r_played(state)

                    break

        self.write_data()

    def mark_episode(self, episode, is_random, new_state):
        for video in self.__videos_instances:
            if video == episode:
                if is_random:
                    video.set_r_played(new_state)
                else:
                    video.set_o_played(new_state)

                self.write_data()
                break

    def restart(self):
        for video in self.__videos_instances:
            video.set_play(True)
            video.set_o_played(False)
            video.set_r_played(False)
            video.set_position(0)

        self.write_data()

    def update_ids(self):
        for i, video in enumerate(self.__videos_instances, 1):
            video.set_id(i)

    def get_start_at(self):
        return self.__start_at

    def get_image(self):
        return self.__series_pixbuf

    def get_name(self):
        return self.__name

    def get_videos(self):
        return self.__videos_instances

    def get_first_episode(self):
        if len(self.__videos_instances) <= 0:
            return None

        return self.__videos_instances[0]

    def get_o_played_stats(self):
        """
            returns: played, total, percent
        """
        self.update_not_hidden_videos()

        i = 0.00
        for video in self.__videos_instances:
            if video.get_o_played() and video.get_display():
                i += 1.00

        if i > 0 and self.__nb_videos > 0:
            return int(i), self.__nb_videos, (i / self.__nb_videos)
        else:
            return 0, self.__nb_videos, 0

    def get_r_played_stats(self):
        """
            returns: played,total,percent
        """
        self.update_not_hidden_videos()

        i = 0.00
        for video in self.__videos_instances:
            if video.get_r_played() and video.get_display():
                i += 1.00

        if i > 0 and self.__nb_videos > 0:
            return int(i), self.__nb_videos, (i / self.__nb_videos)
        else:
            return 0, self.__nb_videos, 0

    def get_o_episode(self, after=None):
        """
            Get the next episode.

            If an episode is provided, get the episode next to this one, and
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

            if not video.get_o_played() and video.get_play() and video.get_path() and video.get_display():
                return video

        # Try to return a video from the beginning
        if after is not None:
            episode = self.get_o_episode()
            if episode:
                return episode

        return None

    def get_r_episode(self):
        for video in self.__videos_instances:
            if not video.get_r_played() and video.get_play() and video.get_path() and video.get_display():
                while True:
                    random_ep = random.randint(0, self.__nb_videos - 1)
                    random_video = self.__videos_instances[random_ep]

                    if not random_video.get_r_played() and random_video.get_play() and random_video.get_path():
                        return random_video

        return None

    def get_nb_videos(self):
        return self.__nb_videos

    def get_path(self):
        return self.__path

    def get_audio_track(self):
        return self.__audio_track

    def get_subtitles_track(self):
        return self.__subtitles_track

    def get_random(self):
        return self.__random

    def get_path_from_video_name(self, name):
        for video in self.__videos_instances:
            if video and video.get_name() == name:
                return video.get_path()

        return None

    def get_video(self, name):
        for video in self.__videos_instances:
            if video and video.get_name() == name:
                return video

        return None

    def get_keep_playing(self):
        return self.__keep_playing

    def set_keep_playing(self, value, write=True):

        self.__keep_playing = value in ('true', 'True', True)

        if write:
            self.write_data()

    def set_start_at(self, value, write=True):
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

        if write:
            self.write_data()

    def set_recursive(self, recursive, write=True):

        self.__recursive = recursive in ('true', 'True', True)

        if write:
            self.write_data()

    def set_audio_track(self, value, write=True):
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_audio_track error:")
            print(str(e))
            value = -2

        if value == -1 or value >= 0:
            self.__audio_track = value
        else:
            self.__audio_track = -2

        if write:
            self.write_data()

    def set_subtitles_track(self, value, write=True):
        try:
            value = int(value)
        except Exception as e:
            print(self.__name)
            print("set_subtitles_track error:")
            print(str(e))
            value = -2

        if value == -1 or value >= 0:
            self.__subtitles_track = value
        else:
            self.__subtitles_track = -2

        if write:
            self.write_data()

    def set_random(self, is_random, write=True):

        self.__random = is_random in ('true', 'True', True)

        if write:
            self.write_data()

    def set_video_position(self, video_to_find, position):
        for video in self.__videos_instances:
            if video_to_find == video:
                video.set_position(position)
                self.write_data()
                return

    def set_name(self, new_name):
        self.__name = new_name

    def set_image(self, path):
        if os.path.exists(path):
            self.__series_pixbuf = Pixbuf.new_from_file_at_size(path,
                                                                self.__series_img_size,
                                                                self.__series_img_size)
            shutil.copy2(path, os.path.join(self.__path, ".folder"))

    def __load_image(self):
        """
            Set the default image
        """
        if not os.path.exists(self.__path):
            image_path = ICON_ERROR_BIG
        else:
            image_path = ICON_LOGO_MEDIUM

            for extension in ('', '.png', '.jpg', '.jpeg'):
                possible_image = os.path.join(self.__path, '.folder' + extension)
                if os.path.exists(possible_image):
                    image_path = possible_image
                    break

        self.__series_pixbuf = Pixbuf.new_from_file_at_size(image_path,
                                                            self.__series_img_size,
                                                            self.__series_img_size)

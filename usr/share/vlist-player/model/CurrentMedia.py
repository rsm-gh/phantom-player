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
    def __init__(self, series=None):
        self.series = series
        self.__episode = None

    def is_series_name(self, series_name):
        if self.series is not None:
            return self.series.get_name() == series_name

        return False

    def mark_seen_episode(self):
        self.__episode.set_position(0)
        self.series.mark_episode(self.__episode, self.series.get_random(), True)

    def get_next_episode(self):

        if self.series.get_random():
            episode = self.series.get_r_episode()
        else:
            episode = self.series.get_o_episode(self.__episode)

        self.__episode = episode

        return episode

    def current_episode(self):
        return self.__episode

    def get_episode(self, episode_name):
        self.__episode = self.series.get_video(episode_name)
        return self.__episode

    def get_episode_name(self):

        if self.__episode is None:
            return None

        return self.__episode.get_name()

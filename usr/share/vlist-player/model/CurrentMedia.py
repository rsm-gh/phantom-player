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
    def __init__(self, series=None, video=None, random=None, mark=None):
        self.series = series
        self.video = video
        self.random = random
        self.mark = mark

    def next_episode(self, random):

        if random:
            video = self.series.get_r_episode()
        else:
            video = self.series.get_o_episode()

        self.random = random
        self.video = video

        return video



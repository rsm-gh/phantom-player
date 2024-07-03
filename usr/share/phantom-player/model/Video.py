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


class Video(object):

    def __init__(self, vhash, path, duration, name=""):

        if vhash == "":
            raise ValueError("Can not add a video with an empty hash.")

        self.__path = path
        self.__name = name
        self.__extension = ""
        self.__number = -1
        self.__is_new = False
        self.__progress = 0
        self.__ignore = False
        self.__hash = vhash
        self.__duration = int(duration)

        #
        # Initialize the attributes
        #

        path_basename = os.path.basename(self.__path)
        if '.' in path_basename:
            name, extension = path_basename.rsplit(".", 1)
            if len(extension) <= 4:
                self.__extension = extension
                if self.__name == "":
                    self.__name = name

        elif self.__name == "":
            self.__name = path_basename

    def exists(self):
        return os.path.exists(self.__path)

    def ended(self):
        return self.__progress >= self.__duration

    def get_duration(self):
        return self.__duration

    def get_extension(self):
        return self.__extension

    def get_name(self):
        return self.__name

    def get_full_name(self):
        return self.__name + "." + self.__extension

    def get_number(self):
        return self.__number

    def get_ignore(self):
        return self.__ignore

    def get_path(self):
        return self.__path

    def get_hash(self):
        return self.__hash

    def get_progress(self):
        return self.__progress

    def get_percent(self):

        if self.__duration <= 0:
            return 0

        percent = int(self.__progress / self.__duration * 100)

        if percent > 100:
            print("Warning: un-valid percent", percent, self.__duration, self.__progress, self.__path)
            percent = 100

        elif percent == 100 and not self.ended():
            percent = 99

        return percent

    def get_is_new(self):
        return self.__is_new

    def set_path(self, path):
        self.__path = path
        if self.__name == "":
            self.__name = os.path.basename(path)

    def set_is_new(self, value):
        self.__is_new = value

    def set_progress(self, value):
        """
            :value: integer or None. if filled with none, it will be set to the maximum.
        """

        if value is None:
            value = self.__duration

        self.__progress = int(value)

    def set_ignore(self, bool_value):
        self.__ignore = bool_value

    def set_number(self, integer):
        if int(integer) < 0:
            raise ValueError("video number error " + self.__name)
        else:
            self.__number = int(integer)

    def set_name(self, name):
        self.__name = name

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


class VideoPosition:
    _start = 0
    _end = 1


class VideoProgress:
    _start = 0
    _end = 100


class Video(object):

    def __init__(self, path, name="", vhash=""):

        self.__path = path
        self.__name = name
        self.__extension = ""
        self.__guid = -1
        self.__is_new = False
        self.__position = VideoPosition._start
        self.__ignore = False
        self.__hash = vhash

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

    def get_extension(self):
        return self.__extension

    def get_name(self):
        return self.__name

    def get_full_name(self):
        return self.__name + "." + self.__extension

    def get_guid(self):
        return self.__guid

    def get_ignore(self):
        return self.__ignore

    def get_path(self):
        return self.__path

    def get_hash(self):
        return self.__hash

    def get_position(self):
        return self.__position

    def get_progress(self):
        return round(self.__position * VideoProgress._end)

    def get_is_new(self):
        return self.__is_new

    def get_played(self):
        # It is better to use the progress here to avoid having approximation
        # issues with the position.
        return self.get_progress() >= VideoProgress._end

    def set_path(self, path):
        self.__path = path
        if self.__name == "":
            self.__name = os.path.basename(path)

    def exists(self):
        return os.path.exists(self.__path)

    def set_hash(self, value):
        self.__hash = value

    def set_is_new(self, value):
        self.__is_new = value

    def set_position(self, pos):
        if VideoPosition._end >= pos >= VideoPosition._start:
            self.__position = pos
        else:
            print(self.__name, "wrong set_position", pos)

    def set_ignore(self, bool_value):
        self.__ignore = bool_value

    def set_guid(self, integer):
        if int(integer) < 0:
            print("video id error " + self.__name)
        else:
            self.__guid = int(integer)

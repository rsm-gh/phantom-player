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
        self.__rating = 0
        self.__size = 0

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

    def get_rating(self):
        return self.__rating

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

    def get_size(self):
        return self.__size

    def set_size(self, bytes_nb):
        if bytes_nb >= 0:
            self.__size = bytes_nb

    def set_rating(self, value):
        self.__rating = value

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
            self.__progress = self.__duration
        else:
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

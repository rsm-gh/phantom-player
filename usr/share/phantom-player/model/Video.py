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

from console_printer import print_warning


class Video(object):

    def __init__(self,
                 vhash: str,
                 path: str,
                 name: str=""):

        if vhash == "":
            raise ValueError("Can not add a video with an empty hash.")

        self.__hash = vhash
        self.__path = path
        self.__name = name
        self.__extension = ""
        self.__is_new = False
        self.__ignore = False

        self.__duration = 0
        self.__size = 0
        self.__number = -1
        self.__progress = 0
        self.__rating = 0

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

    def exists(self) -> bool:
        return os.path.exists(self.__path)

    def end_progress(self):
        self.__progress = self.__duration

    def ended(self) -> bool:
        return self.__progress >= self.__duration

    def get_rating(self) -> int:
        return self.__rating

    def get_duration(self) -> int:
        return self.__duration

    def get_extension(self) -> str:
        return self.__extension

    def get_name(self) -> str:
        return self.__name

    def get_full_name(self) -> str:
        return self.__name + "." + self.__extension

    def get_number(self) -> int:
        return self.__number

    def get_ignore(self) -> bool:
        return self.__ignore

    def get_path(self) -> str:
        return self.__path

    def get_hash(self) -> str:
        return self.__hash

    def get_progress(self) -> int:
        return self.__progress

    def get_percent(self) -> int:

        if self.__duration <= 0:
            return 0

        percent = int(self.__progress / self.__duration * 100)

        if percent > 100:
            print_warning(f"un-valid percent={percent}, duration={self.__duration}. progress={self.__progress}\n path={self.__path}")
            percent = 100

        elif percent == 100 and not self.ended():
            percent = 99

        return percent

    def get_is_new(self) -> bool:
        return self.__is_new

    def get_size(self) -> int:
        return self.__size

    def set_size(self, bytes_nb: int) -> None:
        if bytes_nb >= 0:
            self.__size = bytes_nb

    def set_duration(self, seconds: int) -> None:
        if seconds >= 0:
            self.__duration = seconds

    def set_rating(self, value: int) -> None:
        self.__rating = int(value)

    def set_path(self, path: str) -> None:
        self.__path = path
        if self.__name == "":
            self.__name = os.path.basename(path)

    def set_is_new(self, value: bool) -> None:
        self.__is_new = value

    def set_progress(self, value: int) -> None:
        self.__progress = int(value)

    def set_ignore(self, value: bool) -> None:
        self.__ignore = value

    def set_number(self, value: int) -> None:
        if int(value) < 0:
            raise ValueError("video number error " + self.__name)
        else:
            self.__number = int(value)

    def set_name(self, name: str) -> None:
        self.__name = name

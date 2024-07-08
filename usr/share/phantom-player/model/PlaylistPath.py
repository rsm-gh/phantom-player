#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2024 Rafael Senties Martinelli.
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


class PlaylistPath:

    def __init__(self, path, recursive, startup_discover):
        """
            The PlaylistPaths are stored in a dictionary with the path as key, so
            once created, this attribute shall not be modified.
        """

        while path.endswith('/'):  # Linux
            path = path[:-1]

        while path.endswith('\\'):  # Windows
            path = path[:-1]

        self.__path = path
        self.__recursive = recursive
        self.__startup_discover = startup_discover

    def get_path(self):
        return self.__path

    def get_recursive(self):
        return self.__recursive

    def get_startup_discover(self):
        return self.__startup_discover

    def set_recursive(self, value):
        self.__recursive = value

    def set_startup_discover(self, value):
        self.__startup_discover = value

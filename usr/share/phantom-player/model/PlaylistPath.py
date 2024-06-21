#!/usr/bin/python3
#

#  Copyright (C) 2024 Rafael Senties Martinelli.
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

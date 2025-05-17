#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2014 Rafael Senties Martinelli.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of either:
#
#   - the GNU Lesser General Public License as published by
#     the Free Software Foundation, version 2.1 only, or
#
#   - the GNU General Public License as published by
#     the Free Software Foundation, version 3 only.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the applicable licenses for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# version 2.1 and the GNU General Public License version 3
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-2.1-only OR GPL-3.0-only


class PlaylistPath:

    def __init__(self, path: str, recursive: bool, startup_discover: bool) -> None:
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

    def get_path(self) -> str:
        return self.__path

    def get_recursive(self) -> bool:
        return self.__recursive

    def get_startup_discover(self) -> bool:
        return self.__startup_discover

    def set_recursive(self, value: bool) -> None:
        self.__recursive = value

    def set_startup_discover(self, value: bool) -> None:
        self.__startup_discover = value

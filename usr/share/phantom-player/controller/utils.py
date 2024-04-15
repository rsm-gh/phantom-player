#!/usr/bin/python3

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


def str_to_boolean(value):
    return value.lower().strip() == "true"


def read_lines(file_path):
    with open(file_path, mode='rt', encoding='utf-8') as f:
        lines = f.readlines()

    clean_lines = []
    for line in lines:
        line = line.strip()

        if not line.startswith("#") and line != "":
            clean_lines.append(line)

    return clean_lines

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
import magic

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

magic_mimetype = magic.open(magic.MAGIC_MIME)
magic_mimetype.load()


def path_is_video(path, forgive_broken_links=False):
    if os.path.islink(path):
        if forgive_broken_links and not os.path.exists(os.path.realpath(path)):
            return True

        mimetype = magic_mimetype.file(os.path.realpath(path))
    else:
        mimetype = magic_mimetype.file(path)

    if 'video/' in mimetype:
        return True

    return False


def generate_list_from_videos_folder(dir_path, recursive):
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        if recursive:
            paths = [os.path.join(dp, filename) for dp, dn, filenames in os.walk(dir_path) for filename in filenames]
        else:
            paths = [os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]

        return [path for path in sorted(paths) if path_is_video(path)]

    return []


class Video(object):

    def __init__(self, path, video_id):

        self.__path = path
        self.__name = ""
        self.__empty_name = ""
        self.__extension = ""
        self.__dir_path = ""

        self.__id = -1
        self.__state = Gtk.STOCK_DIALOG_WARNING

        self.__play = True
        self.__o_played = False
        self.__r_played = False
        self.__position = 0
        self.__display = True

        #
        # Initialize the attributes
        #

        self.set_id(video_id)

        try:
            self.__name = os.path.basename(path)
            self.__dir_path = os.path.dirname(path)
        except Exception:
            print("wrong path", path)
        else:
            self.__empty_name, self.__extension = os.path.splitext(self.__name)

            if len(self.__extension) > 4:  # it is probably not an extension...
                self.__empty_name = self.__empty_name + self.__extension
                self.__extension = ''

        self.update_state()

    def update_state(self):
        if os.path.exists(self.__path):
            self.__state = Gtk.STOCK_APPLY
        else:
            self.__state = Gtk.STOCK_DIALOG_WARNING

    def load_info(self, play, o_played, r_played, position, display):

        if play.strip().lower() == 'false':
            self.set_play(False)

        if o_played.strip().lower() == 'true':
            self.set_o_played(True)

        if r_played.strip().lower() == 'true':
            self.set_r_played(True)

        if position > 0:
            self.set_position(position)

        if display.strip().lower() != 'true':
            self.set_display(False)

    def get_extension(self):
        return self.__extension

    def get_empty_name(self):
        return self.__empty_name

    def set_path(self, path):
        self.__path = path
        self.__name = os.path.basename(path)
        self.update_state()

    def set_state_new(self):
        self.__state = Gtk.STOCK_ADD

    def set_state(self, pixbuffer):
        self.__state = pixbuffer

    def get_position(self):
        return self.__position

    def set_position(self, pos):
        if 1 > pos >= 0:
            self.__position = pos
        else:
            print(self.__name, "wrong set_position")

    def get_display(self):
        return self.__display

    def set_display(self, bool_value):
        self.__display = bool_value

    def get_path(self):
        return self.__path

    def get_name(self):
        return self.__name

    def get_state(self):
        return self.__state

    def get_play(self):
        return self.__play

    def get_o_played(self):
        return self.__o_played

    def get_r_played(self):
        return self.__r_played

    def set_r_played(self, bool_value):
        self.__r_played = bool_value

    def set_o_played(self, bool_value):
        self.__o_played = bool_value

    def set_play(self, bool_value):
        self.__play = bool_value

    def set_id(self, integer):
        if int(integer) < 0:
            print("video id error " + self.__name)
        else:
            self.__id = int(integer)

    def get_id(self):
        return self.__id
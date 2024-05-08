#!/usr/bin/python3
#

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli.
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
#

import os
import gi
import sys

os.environ["GDK_BACKEND"] = "x11"
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from view.MediaPlayerWidget import MediaPlayerWidget, VLC_INSTANCE


class MediaPlayer(Gtk.Window):

    def __init__(self):
        super().__init__()

        self.__mp_widget = MediaPlayerWidget(root_window=self)
        self.add(self.__mp_widget)
        self.connect('delete-event', self.quit)

        self.set_size_request(600, 300)
        self.show_all()

    def quit(self, *_):
        self.__mp_widget.quit()
        Gtk.main_quit()

    def play_video(self, path):
        self.__mp_widget.set_video(path,
                                   position=.5,
                                   play=False,
                                   subtitles_track=2)


if __name__ == '__main__':
    player = MediaPlayer()
    player.play_video('/home/rsm/Videos/test.mkv')
    Gtk.main()
    VLC_INSTANCE.release()

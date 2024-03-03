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
import sys
import gi

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, _PROJECT_DIR)

os.environ["GDK_BACKEND"] = "x11"
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from view.MediaPlayerWidget import MediaPlayerWidget, VLC_INSTANCE

class MediaPlayer(Gtk.Window):

    def __init__(self, app):
        super().__init__(application=app)

        self.__media_player_widget = MediaPlayerWidget(self, application=app)
        self.set_child(self.__media_player_widget)
        self.connect('close-request', self.quit)

        self.set_size_request(600, 300)
        self.show()


    def quit(self, *_):
        self.__media_player_widget.quit()

    def play_video(self, path):
        self.__media_player_widget.set_video(path,
                                             position=.1,
                                             play=True)


def on_activate(app):
    player = MediaPlayer(app)
    player.play_video('/home/cadweb/Documents/Backup/VHS  EVENTOS ARETE 1998 1999  PARTE 2.mpg')
    player.present()

if __name__ == '__main__':
    APP = Gtk.Application(application_id='com.senties-martinelli.MediaPlayer')
    APP.connect('activate', on_activate)
    APP.run(None)
    VLC_INSTANCE.release()

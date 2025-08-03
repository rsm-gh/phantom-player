#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024-2025 Rafael Senties Martinelli.
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

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from env import *

from gi.repository import Gtk
from view.GtkPlayer import GtkPlayer


class MediaPlayer(Gtk.Window):

    def __init__(self):
        super().__init__(title="Phantom Media Player")

        self.__mp_widget = GtkPlayer(root_window=self)
        self.add(self.__mp_widget)
        self.connect('delete-event', self.quit)

        self.set_size_request(600, 300)
        self.show_all()

    def quit(self, *_):
        self.__mp_widget.quit()
        Gtk.main_quit()

    def play_video(self, path):
        self.__mp_widget.set_video(path,
                                   play=False,
                                   start_at=0,
                                   subtitles_track=2,
                                   custom_title="Custom Title")


if __name__ == '__main__':

    if sys.platform == 'win32':
        video_path = r"C:\Users\rafae\Desktop\Best Of Rodney Mullen.mp4"
    else:
        #video_path = "/home/rsm/Videos/vlc/test.mp4"
        video_path = "/home/rsm/Videos/vlc/test.mkv"
        #video_path = "/home/rsm/Videos/vlc/audio_track.mkv"
        #video_path = "/home/rsm/Videos/Movies/The Matrix Trilogy Complete (1999-2003) 720p 5.1 BRRiP x264 AAC [Team Nanban]/The Matrix Reloaded (2003) 720p 5.1 BRRiP x264 AAC [Team Nanban].mp4"
        #video_path = "/home/rsm/Videos/BMX/DAKOTA ROCHE, COREY MARTINEZ, NATHAN WILLIAMS BMX VIDEO - USA.mp4"

    player = MediaPlayer()
    player.play_video(video_path)
    Gtk.main()

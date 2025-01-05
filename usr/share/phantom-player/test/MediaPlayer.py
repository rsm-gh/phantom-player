#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024-2025 Rafael Senties Martinelli.
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
import sys

if sys.platform == 'win32':

    __UCRT_PATH = r"C:\msys64\ucrt64\bin"

    if not os.path.exists(__UCRT_PATH):
        raise ValueError(__UCRT_PATH+" does not exist.")


    os.chdir(__UCRT_PATH)
    os.add_dll_directory(__UCRT_PATH) #why this is not working?
    #os.environ.setdefault('PYTHON_VLC_LIB_PATH', os.path.join(__UCRT_PATH, "libvlc.dll"))

elif 'linux' in sys.platform:
    os.environ["GDK_BACKEND"] = "x11"

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
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
        #video_path = "/home/rsm/Videos/vlc/test.mkv"
        #video_path = "/home/rsm/Videos/vlc/audio_track.mkv"
        #video_path = "/home/rsm/Videos/Movies/The Matrix Trilogy Complete (1999-2003) 720p 5.1 BRRiP x264 AAC [Team Nanban]/The Matrix Reloaded (2003) 720p 5.1 BRRiP x264 AAC [Team Nanban].mp4"
        video_path = "/home/rsm/Videos/BMX/DAKOTA ROCHE, COREY MARTINEZ, NATHAN WILLIAMS BMX VIDEO - USA.mp4"

    player = MediaPlayer()
    player.play_video(video_path)
    Gtk.main()

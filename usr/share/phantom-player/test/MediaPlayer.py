#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
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

"""
    Patches:
        + Patch 002: `self.__vlc_widget._player.get_media()` is always returning `None`. Why?
            To fix it, I created `self.__media`.

    Remarks:
        + Careful when using `player.pause()`, because if the player is already paused, it may (randomly) start playing.

    Bugs:
        + It is necessary to connect the Scale of the Volume button, to avoid hiding the GUI when pressed.
            I haven't found a solution for this, because the press signals connect to the button and not the scale.
        + VolumeButton: it should get hidden when clicking out of the button. Is this a problem of GTK?

    To do:
        + Add mute shortcut
        + Enable video tracks?
        + On left right arrows?
        + Set custom title? Ex: video name? not video full name?
        + When the media changes, display a label. I think it can be done with the VLC API.
        + When using the +/- signs of the volume button, only change of 1.
        + `player.set_track()` returns a status. It would be good to read the status and display a message in case of error.
"""

import os
import sys

if sys.platform == 'win32':
    #os.add_dll_directory(r"C:\msys64\ucrt64\bin") why this is not working?
    os.chdir(r"C:\msys64\ucrt64\bin")

elif 'linux' in sys.platform:
    os.environ["GDK_BACKEND"] = "x11"

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from view.MediaPlayerWidget import MediaPlayerWidget


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
                                   play=False,
                                   start_at=0,
                                   subtitles_track=2)


if __name__ == '__main__':

    if sys.platform == 'win32':
        video_path = r"C:\Users\rafae\Desktop\Best Of Rodney Mullen.mp4"
    else:
        video_path = "/home/rsm/Videos/vlc/test.mp4"
        #video_path = "/home/rsm/Videos/vlc/test.mkv"
        #video_path = "/home/rsm/Videos/vlc/audio_track.mkv"

    player = MediaPlayer()
    player.play_video(video_path)
    Gtk.main()

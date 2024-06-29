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

"""
    Patches:
        + Patch 001: `media.get_duration()` is not correctly parsed if the video was not played.
            This is strange, because the VLC API says that `parse()` is synchronous, and it should work.
            To fix it, all the properties depending on the media duration are loaded in `self.__on_thread_player_activity()`

        + Patch 002: `self.__vlc_widget.player.get_media()` is always returning `None`. Why?
            To fix it, I created `self.__media`.

    Remarks:
        + Careful when using `player.pause()`, because if the player is already paused, it may (randomly) start playing.

        + The widget uses `set_position()` instead of `set_time()` because:
            + The VLC API says that `time` is not supported for all the formats. This makes the code more complex, but it works good.
            + Saving/Applying the position is pretty easy.
            + `start_at`, `end_at`, and `end_position` are more complex because they depend on the media duration:
                + `start_at` and `end_at` must be saved in `time` format, because it is an input given by the user and, it must be a constant across all media.
                + `end_position` is used to detect when a video has ended. Normally it should be `1`, but the value may change based on a numeric approach. For example, for a very long video, it may be `.9999999`, and for a shorter `.9`.

    Bugs:
        + Test/Fix (when cancel) the option to choose the subtitles' file...
        + It is necessary to connect the Scale of the Volume button, to avoid hiding the GUI when pressed.
            I haven't found a solution for this, because the press signals connect to the button and not the scale.
        + VolumeButton: it should get hidden when clicking out of the button. Is this a problem of GTK?
        + Fix "subtitles from file" should be checked srt file exists.
        + Fix subtitles, if cancel "select from file"...
        + If paused, on button restart, the position is not sent.

    To do:
        + Add mute shortcut
        + Enable video tracks?
        + On left right arrows?
        + Set custom title? Ex: video name? not video full name?
        + When the media changes, display a label. I think it can be done with the VLC API.
        + When using the +/- signs of the volume button, only change of 1.
        + `player.set_track()` returns a status. It would be good to read the status and display a message in case of error.
        + Is it possible to remove the thread `on_thread_player_activity` and replaced by VLC signals?
"""

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
    player.play_video('/run/media/rsm/media/Videos/Ink Master/Season15/Ink.Master.S15E03.1080p.HEVC.x265-MeGusta[eztv.re].mkv')
    Gtk.main()
    VLC_INSTANCE.release()

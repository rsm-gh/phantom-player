#!/usr/bin/python3
#

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

#
# Special thanks to the VideoLAN Team! This file was created by using as example the
# gtk3 example/widget for VLC Python bindings by Olivier Aubert <contact@olivieraubert.net>
#


"""
    To do:
        - I'm searching how to set the audio output device.

    Remarks:
        - It seems to be a problem with the id of GTK windows, so to work, the script must be called as:
            GDK_BACKEND=x11 python3 VLCWidget.py
"""

import gi
import os
import sys
import ctypes
from time import time

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from Paths import *
from controller import vlc
from system_utils import turn_off_screensaver

# Create a single vlc.Instance() to be shared by (possible) multiple players.
if 'linux' in sys.platform:
    # Inform libvlc that Xlib is not initialized for threads
    VLC_INSTANCE = vlc.Instance("--no-xlib")
else:
    VLC_INSTANCE = vlc.Instance()


def gtk_file_chooser(parent, start_path=''):
    window_choose_file = Gtk.FileChooserDialog('Video List Player',
                                               parent,
                                               Gtk.FileChooserAction.OPEN,
                                               (Gtk.STOCK_CANCEL,
                                                Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN,
                                                Gtk.ResponseType.OK))

    window_choose_file.set_default_response(Gtk.ResponseType.NONE)
    window_choose_file.set_icon_from_file(ICON_LOGO_SMALL)
    window_choose_file.set_transient_for(parent)

    if start_path == '':
        window_choose_file.set_current_folder(HOME_PATH)
    else:
        window_choose_file.set_current_folder(start_path)

    response = window_choose_file.run()
    if response == Gtk.ResponseType.OK:
        file_path = window_choose_file.get_filename()
    else:
        file_path = None

    window_choose_file.destroy()
    return file_path


def format_track(track):
    """ Format the tracks provided by pyVLC. Track must be a tuple (int, string)"""

    number = str(track[0])

    try:
        content = track[1].strip().replace('[', '').replace(']', '').replace('_', ' ').title()
    except Exception as e:
        content = track[1]
        print(str(e))

    if len(number) == 0:
        numb = '  '
    elif len(number) == 1:
        numb = ' {}'.format(number)
    else:
        numb = str(number)

    return ' {}   {}'.format(numb, content)

def get_window_pointer(window):
    """ Use the window.__gpointer__ PyCapsule to get the C void* pointer to the window"""
    # get the c gpointer of the gdk window
    ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
    ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
    return ctypes.pythonapi.PyCapsule_GetPointer(window.__gpointer__, None)


class VLCWidget(Gtk.DrawingArea):
    """ This class creates a vlc player built in a Gtk.DrawingArea """

    def __init__(self, root_window=None, fullscreen_window=None):

        super().__init__()
        self.__root_window = root_window
        self.__vlc_widget_on_top = False
        self.__mouse_time = time()
        self.__volume_increment = 3  # %


        self.player = VLC_INSTANCE.media_player_new()

        self.connect('realize', self.__handle_embed)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.__on_mouse_button_press)

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('motion_notify_event', self.__on_motion_notify_event)

        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.connect('scroll_event', self.__on_mouse_scroll)

    def __handle_embed(self, *_):

        if sys.platform == 'win32':
            # get the win32 handle
            gdkdll = ctypes.CDLL('libgdk-3-0.dll')
            handle = gdkdll.gdk_win32_window_get_handle(get_window_pointer(self.get_window()))
            self.player.set_hwnd(handle)

        elif sys.platform == 'darwin':
            # get the nsview pointer. NB need to manually specify function signature
            gdkdll = ctypes.CDLL('libgdk-3.0.dll')
            get_nsview = gdkdll.gdk_quaerz_window_get_nsview
            get_nsview.restype, get_nsview.argtypes = [ctypes.c_void_p], ctypes.c_void_p
            self.player.set_nsobject(get_nsview(get_window_pointer(self.get_window())))

        else:
            self.player.set_xwindow(self.get_window().get_xid())

        return True

    def __on_menu_video_subs_audio(self, _, player_type, track):
        """
            Todo: self.player.XXX_set_track returns a status. It would be good
            to read the status and display a message in case of problem.
        """
        if player_type == 0:
            self.player.audio_set_track(track)

        elif player_type == 1:
            self.player.video_set_track(track)

        elif player_type == 2:
            self.player.video_set_spu(track)

    def __on_mouse_button_press(self, _, event):

        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == 1:  # left click
                self.fullscreen()

        elif event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == 1:  # left click

                if self.__vlc_widget_on_top and self.is_playing():
                    self.player.pause()
                    turn_off_screensaver(False)
                else:
                    self.player.play()
                    turn_off_screensaver(True)

            elif event.button == 3:  # right click
                """
                    Audio, Sound and Subtitles Menu
                """
                self.__menu = Gtk.Menu()

                # Full screen button
                #
                state = self.__root_window.get_window().get_state()

                if Gdk.WindowState.FULLSCREEN & state:
                    menuitem = Gtk.ImageMenuItem("Un-Fullscreen")
                else:
                    menuitem = Gtk.ImageMenuItem("Fullscreen")
                menuitem.connect('activate', self.fullscreen)
                self.__menu.append(menuitem)

                """
                    Audio Menu
                """
                menuitem = Gtk.ImageMenuItem("Audio")
                self.__menu.append(menuitem)
                submenu = Gtk.Menu()
                menuitem.set_submenu(submenu)

                selected_track = self.player.audio_get_track()

                item = Gtk.CheckMenuItem("-1  Disable")
                item.connect('activate', self.__on_menu_video_subs_audio, 0, -1)
                if selected_track == -1:
                    item.set_active(True)

                submenu.append(item)

                try:
                    tracks = [(audio[0], audio[1].decode('utf-8')) for audio in
                              self.player.audio_get_track_description()]
                except Exception as e:
                    tracks = self.player.audio_get_track_description()
                    print(str(e))

                for track in tracks:
                    if 'Disable' not in track:
                        item = Gtk.CheckMenuItem(format_track(track))
                        item.connect('activate', self.__on_menu_video_subs_audio, 0, track[0])
                        if selected_track == track[0]:
                            item.set_active(True)
                        submenu.append(item)

                """
                    Subtitles
                """
                menuitem = Gtk.ImageMenuItem("Subtitles")
                self.__menu.append(menuitem)
                submenu = Gtk.Menu()
                menuitem.set_submenu(submenu)

                selected_track = self.player.video_get_spu()

                item = Gtk.CheckMenuItem("-1  Disable")
                item.connect('activate', self.__on_menu_video_subs_audio, 2, -1)
                if selected_track == -1:
                    item.set_active(True)

                submenu.append(item)

                try:
                    tracks = [(video_spu[0], video_spu[1].decode('utf-8')) for video_spu in
                              self.player.video_get_spu_description()]
                except Exception as e:
                    tracks = self.player.video_get_spu_description()
                    print(str(e))

                for track in tracks:
                    if 'Disable' not in track:
                        item = Gtk.CheckMenuItem(format_track(track))
                        item.connect('activate', self.__on_menu_video_subs_audio, 2, track[0])
                        if selected_track == track[0]:
                            item.set_active(True)
                        submenu.append(item)

                self.__menu.show_all()
                self.__menu.popup(None, None, None, None, event.button, event.time)
                return True

    def __on_motion_notify_event(self, *_):

        print("MOTION IS CALLED")
        if self.__root_window.is_active():
            self.__mouse_time = time()

    def __on_mouse_scroll(self, _, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.volume_up()

        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.volume_down()

    def set_on_top(self, value):
        self.__vlc_widget_on_top = value

    def get_mouse_time(self):
        return self.__mouse_time

    def set_subtitles_from_file(self, *_):
        """
            Todo: read the result of player.video_set_subtitle_file(path) and display a message
            in case of problem.
        """
        path = gtk_file_chooser(self.__root_window)

        if path is not None:
            self.player.video_set_subtitle_file(path)

        return True

    def fullscreen(self, *_):
        if Gdk.WindowState.FULLSCREEN & self.__root_window.get_window().get_state():
            self.__root_window.unfullscreen()
        else:
            self.__root_window.fullscreen()

    def volume_up(self):
        actual_volume = self.player.audio_get_volume()
        if actual_volume + self.__volume_increment <= 100:
            self.player.audio_set_volume(actual_volume + self.__volume_increment)
        else:
            self.player.audio_set_volume(100)

    def volume_down(self):
        actual_volume = self.player.audio_get_volume()
        if actual_volume >= self.__volume_increment:
            self.player.audio_set_volume(actual_volume - self.__volume_increment)
        else:
            self.player.audio_set_volume(0)

    def is_playing(self):
        if self.player.get_state() == vlc.State.Playing:
            return True

        return False

    def is_paused(self):
        if self.player.get_state() == vlc.State.Paused:
            return True

        return False

#!/usr/bin/python3

#
#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli.
#                2017 Olivier Aubert <contact@olivieraubert.net> (gtkvlc.py)
#                2009-2010 the VideoLAN team (gtk2vlc.py)
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
#  You should have received a copy of the GNU General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#

import sys
import vlc
import ctypes
from gi.repository import Gtk

from console_printer import print_info, print_debug


class VLCWidget(Gtk.DrawingArea):
    __gtype_name__ = 'VLCWidget'

    def __init__(self):
        super().__init__(vexpand=True, hexpand=True)

        #
        # VLC Player
        #
        if 'linux' in sys.platform:
            args = ["--no-xlib"]
        else:
            args = []

        self.__vlc_instance = vlc.Instance(args)
        print_info(f"python-vlc version: {vlc.__version__}, generator: {vlc.__generator_version__}, build date:{vlc.build_date}")
        print_info(f"VLC instance: {self.__vlc_instance}, args={args}", direct_output=True)

        self._player = self.__vlc_instance.media_player_new()

        #
        # GTK Signals
        #
        self.connect('realize', self.__on_realize)
        self.connect('draw', self.__on_draw)
        self.connect('destroy', self.__on_destroy)

    def parse_media(self, file_path, timeout=3000):
        media = self.__vlc_instance.media_new_path(file_path)
        media.parse_with_options(vlc.MediaParseFlag.local, timeout)
        return media

    def release(self):
        print_debug()

        if self._player is not None:
            print_debug(f"VLC Player: {self._player}", direct_output=True)
            self._player.stop()
            self._player.release()
            self._player = None

        if self.__vlc_instance is not None:
            print_debug(f"VLC Instance: {self.__vlc_instance}", direct_output=True)
            self.__vlc_instance.release()
            self.__vlc_instance = None


    def __on_realize(self, *_):

        top_level_window = self.get_window()

        if 'linux' in sys.platform:
            self._player.set_xwindow(top_level_window.get_xid())
        else:
            # Use the window.__gpointer__ PyCapsule to get the C void* pointer to the window
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
            window_pointer = ctypes.pythonapi.PyCapsule_GetPointer(top_level_window.__gpointer__, None)

            # GDK DLL
            gdk_dll = ctypes.CDLL('libgdk-3-0.dll')

            if sys.platform == 'win32':
                gdk_dll.gdk_win32_window_get_handle.argtypes = [ctypes.c_void_p]
                gdk_dll.gdk_win32_window_get_handle.restype = ctypes.c_void_p
                handle = gdk_dll.gdk_win32_window_get_handle(window_pointer)
                self._player.set_hwnd(handle)

            elif sys.platform == 'darwin':
                get_nsview = gdk_dll.gdk_quaerz_window_get_nsview
                get_nsview.restype, get_nsview.argtypes = [ctypes.c_void_p], ctypes.c_void_p
                nsview = get_nsview(window_pointer)
                self._player.set_nsobject(nsview)

            else:
                raise ValueError(f"Unsupported platform = {sys.platform}")

        return True

    @staticmethod
    def __on_draw(_widget, cairo_ctx):
        """To redraw the black background when resized"""
        cairo_ctx.set_source_rgb(0, 0, 0)
        cairo_ctx.paint()

    def __on_destroy(self, _widget):
        self.release()
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
import ctypes
import cairo
from gi.repository import Gtk

import vlc_utils
from console_printer import print_debug

class VLCWidget(Gtk.DrawingArea):
    __gtype_name__ = 'VLCWidget'

    def __init__(self) -> None:
        super().__init__(vexpand=True, hexpand=True)

        #
        # VLC Player
        #
        vlc_instance = vlc_utils.get_instance()
        self._player = vlc_instance.media_player_new()

        #
        # GTK Signals
        #
        self.connect('realize', self.__on_realize)
        self.connect('draw', self.__on_draw)
        self.connect('destroy', self.__on_destroy)

    def release(self) -> None:

        print_debug(f"VLC Player: {self._player}")

        if self._player is not None:
            self._player.stop()
            self._player = self._player.release()

        vlc_utils.release_instance()


    def __on_realize(self, _widget: Gtk.Widget) -> None:

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

    @staticmethod
    def __on_draw(_widget: Gtk.Widget, cr: cairo.Context) -> bool:
        """To redraw the black background when resized"""

        cr.set_source_rgb(0, 0, 0)
        cr.paint()

        return True

    def __on_destroy(self, _widget: Gtk.Widget) -> None:
        self.release()
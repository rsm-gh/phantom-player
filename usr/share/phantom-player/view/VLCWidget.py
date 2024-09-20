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
from vlc_utils import _VLC_INSTANCE
from gi.repository import Gtk


class VLCWidget(Gtk.DrawingArea):
    __gtype_name__ = 'VLCWidget'

    def __init__(self):
        super().__init__(vexpand=True, hexpand=True)
        self._player = _VLC_INSTANCE.media_player_new()
        self.connect('realize', self.__on_realize)
        self.connect("draw", self.__on_draw)

    def __on_realize(self, *_):

        top_level_window = self.get_window()

        if 'linux' in sys.platform:
            self._player.set_xwindow(top_level_window.get_xid())
        else:
            gdk_dll = ctypes.CDLL('libgdk-3-0.dll')
            window_pointer = self.get_window_pointer(top_level_window)

            if sys.platform == 'win32':
                # get the win32 handle
                gdk_dll.gdk_win32_window_get_handle.argtypes = [ctypes.c_void_p]
                gdk_dll.gdk_win32_window_get_handle.restype = ctypes.c_void_p
                handle = gdk_dll.gdk_win32_window_get_handle(window_pointer)
                self._player.set_hwnd(handle)

            elif sys.platform == 'darwin':
                # get the nsview pointer. NB needed to manually specify the function signature.
                get_nsview = gdk_dll.gdk_quaerz_window_get_nsview
                get_nsview.restype, get_nsview.argtypes = [ctypes.c_void_p], ctypes.c_void_p
                nsview = get_nsview(window_pointer)
                self._player.set_nsobject(nsview)


        return True

    @staticmethod
    def __on_draw(_, cairo_ctx):
        """To redraw the black background when resized"""
        cairo_ctx.set_source_rgb(0, 0, 0)
        cairo_ctx.paint()

    @staticmethod
    def get_window_pointer(window):
        """ Use the window.__gpointer__ PyCapsule to get the C void* pointer to the window"""
        # get the c gpointer of the gdk window
        ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
        return ctypes.pythonapi.PyCapsule_GetPointer(window.__gpointer__, None)

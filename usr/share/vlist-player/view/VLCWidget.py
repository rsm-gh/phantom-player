#!/usr/bin/python3
#

#
#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli.
#
#   And this code was also inspired from:
#       + gtkvlc.py Copyright (C) 2017 Olivier Aubert <contact@olivieraubert.net>
#       + gtk2vlc.py Copyright (C) 2009-2010 the VideoLAN team.
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
    Note: it seems to be a problem with the id of GTK windows, so to work, the script must be called as:
          GDK_BACKEND=x11 python3 VLCWidget.py
"""

import gi
import os
import sys
import ctypes

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from controller import vlc

# Create a single vlc.Instance() to be shared by (possible) multiple players.
if 'linux' in sys.platform:
    # Inform libvlc that Xlib is not initialized for threads
    VLC_INSTANCE = vlc.Instance("--no-xlib")
else:
    VLC_INSTANCE = vlc.Instance()

class VLCWidget(Gtk.DrawingArea):
    """Simple VLC widget.

    Its player can be controlled through the 'player' attribute, which
    is a vlc.MediaPlayer() instance.
    """
    __gtype_name__ = 'VLCWidget'

    def __init__(self, root_window=None):

        super().__init__()
        self.__root_window = root_window

        self.player = VLC_INSTANCE.media_player_new()

        self.connect('realize', self.__handle_embed)

    def __handle_embed(self, *_):

        if sys.platform == 'win32':
            # get the win32 handle
            gdk_dll = ctypes.CDLL('libgdk-3-0.dll')
            handle = gdk_dll.gdk_win32_window_get_handle(self.get_window_pointer(self.get_window()))
            self.player.set_hwnd(handle)

        elif sys.platform == 'darwin':
            # get the nsview pointer. NB needed to manually specify the function signature.
            gdk_dll = ctypes.CDLL('libgdk-3.0.dll')
            get_nsview = gdk_dll.gdk_quaerz_window_get_nsview
            get_nsview.restype, get_nsview.argtypes = [ctypes.c_void_p], ctypes.c_void_p
            self.player.set_nsobject(get_nsview(self.get_window_pointer(self.get_window())))

        else:
            self.player.set_xwindow(self.get_window().get_xid())

        return True

    @staticmethod
    def get_window_pointer(window):
        """ Use the window.__gpointer__ PyCapsule to get the C void* pointer to the window"""
        # get the c gpointer of the gdk window
        ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
        return ctypes.pythonapi.PyCapsule_GetPointer(window.__gpointer__, None)
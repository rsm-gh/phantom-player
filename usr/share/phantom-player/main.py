#!/usr/bin/python3
#

#  Copyright (C) 2024 Rafael Senties Martinelli
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

import os
import sys
import gi

os.environ["GDK_BACKEND"] = "x11"
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')  # is this necessary?
from gi.repository import Gtk

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from view.PhantomPlayer import PhantomPlayer


class PhantomApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__phantom_player = None

    def do_activate(self):
        active_window = self.props.active_window
        if active_window:
            active_window.present()
        else:
            self.__phantom_player = PhantomPlayer(application=self)
            self.__phantom_player.present()


app = PhantomApp(application_id="com.senties-martinelli.PhantomPlayer")
app.run(sys.argv)
print("PhantomApp Ended.")

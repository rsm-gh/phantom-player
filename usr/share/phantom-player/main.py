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
gi.require_version('PangoCairo', '1.0')  # necessary for the cell renderers
from gi.repository import Gtk, Gio

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from view.PhantomPlayer import PhantomPlayer

"""
Todo: Normally files should be opened by doing:

    1) app.set_flags(Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
    2) defining the action:
        a) connecting the open signal, app.connect('open', self.__on_open..)
        b) defining the method do_open(self, files, n_files, hint)

But it I could not make it work, so the only workaround was to use HANDLES_COMMAND_LINE.
"""


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

    def do_command_line(self, command_line):
        args = command_line.get_arguments()
        args.pop(0)

        self.activate()

        if self.__phantom_player is None:
            print("Critical Error: do_command_line > self.__phantom_player is None")
            return 1

        self.__phantom_player.wait_ready()

        if len(args) > 0:
            file_path = ""
            for arg in args:
                if arg.startswith('--open-file='):
                    file_path = arg.split("=", 1)[1]
                    break
                else:
                    print("Error: non valid CMD argument '{}'".format(arg))
                    return 1

            if file_path != "":
                if not os.path.exists(file_path):
                    print("Error: requesting to open un-existing file '{}'".format(file_path))
                    return 1

                elif self.__phantom_player is not None:
                    if not self.__phantom_player.open_file(file_path):
                        print("Error: requesting to open '{}' while the software is busy.".format(file_path))
                        return 1

        return 0


app = PhantomApp(application_id="com.senties-martinelli.PhantomPlayer")
app.set_flags(Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
app_status = app.run(sys.argv)
sys.exit(app_status)

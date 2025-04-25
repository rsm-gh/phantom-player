#!/usr/bin/python3

#
#    This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024-2025 Rafael Senties Martinelli.
#
#  This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License 2.1 as
#   published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/lgpl-2.1.en.html>.
#

"""
    The "Open" file feature is implemented with HANDLES_COMMAND_LINE instead of
    HANDLES_OPEN because there may be more commands in the future.
"""

from env import *

import sys
from gi.repository import Gtk, Gio
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
                    print(f"Error: non valid CMD argument '{arg}'")
                    return 1

            if file_path != "":
                if not os.path.exists(file_path):
                    print(f"Error: requesting to open un-existing file '{file_path}'")
                    return 1

                elif self.__phantom_player is not None:
                    if not self.__phantom_player.open_file(file_path):
                        print("Error: requesting to open '{}' while the software is busy.".format(file_path))
                        return 1

        return 0


if __name__ == "__main__":

    _APP = PhantomApp(application_id="com.senties-martinelli.PhantomPlayer")
    _APP.set_flags(Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
    _APP_STATUS = _APP.run(sys.argv)
    sys.exit(_APP_STATUS)

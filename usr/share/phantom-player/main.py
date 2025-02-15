#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024-2025 Rafael Senties Martinelli.
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

#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
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

import os
import sys

if sys.platform == 'win32':

    __UCRT_PATH = r"C:\msys64\ucrt64\bin"

    if not os.path.exists(__UCRT_PATH):
        raise ValueError(__UCRT_PATH+" does not exist.")

    #os.add_dll_directory(r"C:\msys64\ucrt64\bin") why this is not working?
    os.chdir(__UCRT_PATH)

elif 'linux' in sys.platform:
    os.environ["GDK_BACKEND"] = "x11"

import gi
gi.require_version('GLib', "2.0")
gi.require_version('PangoCairo', '1.0')  # necessary for the cell renderers
gi.require_version('Gtk', '3.0')
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


if __name__ == "__main__":

    _APP = PhantomApp(application_id="com.senties-martinelli.PhantomPlayer")
    _APP.set_flags(Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
    _APP_STATUS = _APP.run(sys.argv)
    sys.exit(_APP_STATUS)

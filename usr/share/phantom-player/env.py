#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2024-2025 Rafael Senties Martinelli.
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

def __set_windows():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): # Running on pyinstaller
        __LIBS_PATH = os.path.join(os.path.dirname(sys.executable), "_internal")
    else:
        pass

    __LIBS_PATH = r"C:\msys64\ucrt64\bin"

    print("LIBS PATH", __LIBS_PATH, flush=True)

    if not os.path.exists(__LIBS_PATH):
        raise ValueError(__LIBS_PATH+" does not exist.")

    os.chdir(__LIBS_PATH)
    os.add_dll_directory(__LIBS_PATH) # why this is not working?
    os.environ.setdefault('PYTHON_VLC_LIB_PATH', os.path.join(__LIBS_PATH, "libvlc.dll"))


def __set_gnu_linux():
    os.environ["GDK_BACKEND"] = "x11"


#
# Prepare the env
#

if sys.platform == 'win32':
    __set_windows()

elif 'linux' in sys.platform:
    __set_gnu_linux()

else:
    raise ValueError("Unsupported platform")

#
# Set the GTk versions
#

import gi
gi.require_version('GLib', "2.0")
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')  # necessary for the cell renderers
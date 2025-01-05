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

import os
import sys

if sys.platform == 'win32':

    __UCRT_PATH = r"C:\msys64\ucrt64\bin"

    if not os.path.exists(__UCRT_PATH):
        raise ValueError(__UCRT_PATH+" does not exist.")

    os.chdir(__UCRT_PATH)
    #os.add_dll_directory(__UCRT_PATH) # why this is not working?
    os.environ.setdefault('PYTHON_VLC_LIB_PATH', os.path.join(__UCRT_PATH, "libvlc.dll"))

elif 'linux' in sys.platform:
    os.environ["GDK_BACKEND"] = "x11"

import gi
gi.require_version('GLib', "2.0")
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')  # necessary for the cell renderers
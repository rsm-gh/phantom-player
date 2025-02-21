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

import system_utils

def __set_windows():

    #
    # Define de library paths
    #

    vlc_path = r"C:\Program Files\VideoLan"

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): # Running on pyinstaller
        libs_path = system_utils.join_path(os.path.dirname(sys.executable), "_internal")
    else:
        libs_path = r"C:\msys64\ucrt64\bin"

        if not os.path.exists(vlc_path):
            # + UCRT VLC libraries from the bin directory work fine, but it is very difficult to collect the codecs.
            # + It's a bad practice to use different source files for Dev and for the compilation.
            vlc_path = libs_path
            print("WARNING: VLC is being used from the UCRT64 directory, the build will have missing codecs.\n")

    #
    # Verify the paths
    #

    for path in (vlc_path, libs_path):
        if not os.path.exists(path):
            raise ValueError(path+" does not exist.")

    #
    # Set the environment
    #

    os.chdir(libs_path)
    os.add_dll_directory(libs_path) # this seems to have no effect, but I rather let it

    os.environ['PYTHON_VLC_MODULE_PATH'] = vlc_path
    os.environ['PYTHON_VLC_LIB_PATH'] = system_utils.join_path(vlc_path, r"VLC\libvlc.dll")


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
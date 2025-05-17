#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of either:
#
#   - the GNU Lesser General Public License as published by
#     the Free Software Foundation, version 2.1 only, or
#
#   - the GNU General Public License as published by
#     the Free Software Foundation, version 3 only.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the applicable licenses for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# version 2.1 and the GNU General Public License version 3
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-2.1-only OR GPL-3.0-only

import os
import sys

import system_utils

def __set_windows():

    #
    # Define de library paths
    #
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): # Running on pyinstaller
        libs_path = system_utils.join_path(os.path.dirname(sys.executable), "_internal")
        vlc_path = libs_path
    else:
        libs_path = r"C:\msys64\ucrt64\bin"
        vlc_path = r"C:\Program Files\VideoLan"

        if not os.path.exists(vlc_path):
            # UCRT VLC libraries from the bin directory work fine, but it is very difficult to collect the codecs.
            # It's a bad practice to use different source files for Dev and for the compilation.
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
#!/usr/bin/python3
#

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli.
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

import os
import webbrowser

def open_link(link):
    webbrowser.open('https://github.com/rsm-gh/vlist-player/issues', new=2)

def open_directory(path):
    os.system('''exo-open "{0}" '''.format(os.path.dirname(path)))


def turn_off_screensaver(state):
    """ True = Turn off screen saver """

    if state:
        try:
            os.system('''xset s off''')
        except Exception:
            print("It wasn't possible to turn off the screensaver")
    else:
        try:
            os.system('''xset s on''')
        except Exception:
            print("It wasn't possible to turn on the screensaver")


def get_active_window_title():
    output = os.popen('''xprop -id $(xprop -root _NET_ACTIVE_WINDOW | cut -d ' ' -f 5) WM_NAME''')
    output = str(output.read())

    try:
        return output.split('''= "''')[1][:-2]
    except Exception:
        print("It wasn't possible to get the window name")
        return None


class EventCodes:
    class Cursor:
        left_click = 1
        right_click = 3

    class Keyboard:
        esc = 65307
        f11 = 65480
        space_bar = 32
        enter = 65293
        arrow_up = 65362
        arrow_down = 65364
        arrow_right = 65363
        arrow_left = 65361
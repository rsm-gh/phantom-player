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
from PIL import Image


def open_directory(path):
    if not os.path.exists(path):
        raise ValueError('Path does not exist', path)

    elif not os.path.isdir(path):
        raise ValueError('Path is not a directory', path)

    # Put the most popular (robust) at the beginning
    file_managers = ['exo-open',
                     'nautilus',
                     'dolphin',
                     'konqueror',
                     'nemo',
                     'pcmanfm',
                     'doublecmd-gtk',
                     'nnn',
                     'krusader']

    # Check if a file manager exist in the system (to avoid un-necessary commands)
    for file_manager in file_managers:
        if os.path.exists("/usr/bin/{}".format(file_manager)):
            file_managers = [file_manager]
            break

    # Try to open the directory
    for program_name in file_managers:
        exit_code = os.system('''{} "{}" &'''.format(program_name, path))
        if exit_code == 0:
            break


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


def format_img(read_path, write_path, width=None, height=None, max_width=None, extension=None):
    """
        Code taken from www.cad-viewer.org
        Either fill width & height, or max_width
    """

    image = Image.open(read_path)

    #
    # Resize larger/smaller images
    #

    img_width, img_height = image.size

    if max_width is not None and img_width > max_width:

        new_height = int(max_width * img_height / img_width)
        image = image.resize((max_width, new_height))

    else:

        width_resizing = False

        if width is not None and img_width != width:

            new_height = int(width * img_height / img_width)

            if new_height >= height:
                image = image.resize((width, new_height))
                width_resizing = True

        if not width_resizing:

            img_width, img_height = image.size

            if height is not None and img_height != height:
                new_width = int(height * img_width / img_height)

                image = image.resize((new_width, height))

        #
        # Crop the excess
        #
        if width is not None and height is not None:

            img_width, img_height = image.size

            if img_width > width or img_height > height:

                if img_height > height:
                    delta_h = (img_height - height) / 2
                else:
                    delta_h = 0

                if img_width > width:
                    delta_w = (img_width - width) / 2
                else:
                    delta_w = 0

                image = image.crop((delta_w, delta_h, width + delta_w, height + delta_h))

    image.save(write_path, format=extension)

    return image.size


class EventCodes:
    class Cursor:
        _left_click = 1
        _middle_click = 2
        _right_click = 3

    class Keyboard:
        _esc = 65307
        _f11 = 65480
        _space_bar = 32
        _enter = 65293
        _arrow_up = 65362
        _arrow_down = 65364
        _arrow_right = 65363
        _arrow_left = 65361
        _back = 65288
        _letter_f = 102
        _letter_s = 115

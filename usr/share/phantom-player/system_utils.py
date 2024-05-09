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
        left_click = 1
        middle_click = 2
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

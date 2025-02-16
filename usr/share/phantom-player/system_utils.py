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
from PIL import Image

from console_printer import print_warning, print_debug

# Put the most popular (robust) at the beginning
__POPULAR_FILE_MANAGERS = ('exo-open',
                           'nautilus',
                           'dolphin',
                           'konqueror',
                           'nemo',
                           'pcmanfm',
                           'doublecmd-gtk',
                           'nnn',
                           'krusader')

# Check if a file manager exists in the system (to avoid unnecessary commands)
_INSTALLED_FILE_MANAGERS = []
for file_manager in __POPULAR_FILE_MANAGERS:
    if os.path.exists(f"/usr/bin/{file_manager}"):
        _INSTALLED_FILE_MANAGERS.append(file_manager)

_INSTALLED_FILE_MANAGERS = tuple(_INSTALLED_FILE_MANAGERS)


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

def has_non_empty_dirs(path: str) -> bool:
    """Check if a directory has non-empty subdirectories (only one level)."""

    if not os.path.exists(path):
        return False

    for name in os.listdir(path):
        abs_path = os.path.join(path, name)
        if os.path.isdir(abs_path) and len(os.listdir(abs_path)) > 0:
            return True

    return False


def open_directory(path: str) -> bool:
    print_debug()

    if not os.path.exists(path):
        print_warning('Path does not exist', path)
        return False

    elif not os.path.isdir(path):
        print_warning('Path is not a directory', path)
        return False

    elif 'linux' not in sys.platform:
        print_warning(f'Unsupported platform {sys.platform}')
        return False

    # Try to open the directory
    for program_name in _INSTALLED_FILE_MANAGERS:
        cmd = f'{program_name} "{path}"'
        print_debug(cmd, direct_output=True)
        exit_code = os.system(cmd)
        if exit_code == 0:
            return True

    return False


def turn_off_screensaver(state: bool) -> None:
    """ Turn of off screen saver """

    if "linux" not in sys.platform:
        print_warning("Can not pause the screen saver.")
        return

    if state:
        try:
            os.system('xset s off')
        except Exception:
            print_warning("It wasn't possible to turn off the screensaver")
    else:
        try:
            os.system('xset s on')
        except Exception:
            print_warning("It wasn't possible to turn on the screensaver")


def format_img(read_path: str,
               write_path: str,
               width: None | int=None,
               height: None | int=None,
               max_width: None | int=None,
               extension: str=None) -> tuple[int, int]:
    """
        Code taken from www.cad-viewer.org
        Either fill width & height, or max_width
        The function will return the new image size (width, height)
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

#!/usr/bin/python3
#

#  Copyright (C) 2016, 2019, 2024 Rafael Senties Martinelli.
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

from gi.repository import Gtk, Gdk, PangoCairo, GObject

from view.gtk_utils import get_general_font_description


def format_bytes(num, binary=False):
    """ Format a byte number into a human-readable string."""

    if binary:
        multiple = 1024
        suffix = 'i'
    else:
        multiple = 1000
        suffix = ""

    for unit in ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z'):
        if abs(num) < multiple:
            return '{0} {1}{2}'.format(round(num, 1), unit + suffix, 'B')
        num /= multiple

    return '{0} {1}{2}'.format(round(num, 1), 'Y' + suffix, 'B')


class CellRendererBytes(Gtk.CellRenderer):
    """ CellRenderer to display kilobytes, ex: 234234 -> 03:54 """

    __gproperties__ = {
        'bytes': ('glong',  # type
                  "long prop",  # nick
                  "A property that contains a number of bytes.",  # blurb
                  0,  # min
                  9223372036854775807,  # max
                  0,  # default
                  GObject.PARAM_READWRITE  # flags
                  ),

        'color': (Gdk.RGBA,  # type
                  "text color",  # nick
                  "Text color of the rating",  # blurb
                  GObject.PARAM_READWRITE,  # flags
                  ),

    }

    def __init__(self):
        super().__init__()
        self.bytes = 0
        self.binary = False
        self.color = Gdk.RGBA()

        self.font_description = get_general_font_description()

        # the formatted value is stored to gain in performance when calling do_render().
        self.__formated_bytes = ''

    def do_set_property(self, pspec, value):
        self.__formated_bytes = format_bytes(self.bytes, self.binary)
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_render(self, cr, _widget, _background_area, cell_area, _flags):
        cr.set_source_rgb(self.color.red, self.color.green, self.color.blue)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(self.font_description)
        layout.set_text(self.__formated_bytes, -1)
        cr.save()
        #  PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x, cell_area.y)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

    """
    def activate(self, event, widget, path, background_area, cell_area, flags):
        print(flags)

    def do_get_size(self, widget, cell_area):
        return (0, 0, cell_area.width, cell_area.height)
        return (0, 0, self.kilobytes.get_width(), self.kilobytes.get_height())
    """


GObject.type_register(CellRendererBytes)

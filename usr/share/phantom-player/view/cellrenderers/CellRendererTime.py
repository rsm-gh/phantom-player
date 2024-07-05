#!/usr/bin/python3
#

#  Copyright (C) 2016, 2024 Rafael Senties Martinelli
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

from datetime import timedelta
from gi.repository import Gtk, Gdk, PangoCairo, GObject

from view.gtk_utils import get_general_font_description


def format_seconds(seconds):
    time_string = str(timedelta(seconds=seconds)).split('.')[0]

    # remove the hours if they are not necessary.
    try:
        if int(time_string.split(':', 1)[0]) == 0:
            time_string = time_string.split(':', 1)[1]
    except Exception:
        pass

    return time_string


class CellRendererTime(Gtk.CellRenderer):
    """ CellRenderer to display milliseconds to time, ex: 234234 -> 03:54 """

    __gproperties__ = {
        'time': ('glong',  # type
                 "integer prop",  # nick
                 "A property that contains a number in seconds",  # blurb
                 0,  # min
                 9223372036854775807,  # max
                 0,  # default
                 GObject.PARAM_READWRITE  # flags
                 ),

        'color': (Gdk.RGBA,  # type
                  "text color",  # nick
                  "Text color of the time",  # blurb
                  GObject.PARAM_READWRITE,  # flags
                  ),
    }

    def __init__(self):
        super().__init__()
        self.time = 0
        self.color = Gdk.RGBA()
        self.font_description = get_general_font_description()

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_render(self, cr, _widget, _background_area, cell_area, _flags):
        cr.set_source_rgb(self.color.red, self.color.green, self.color.blue)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(self.font_description)
        layout.set_text(format_seconds(self.time), -1)
        cr.save()
        #  PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x, cell_area.y)
        PangoCairo.show_layout(cr, layout)
        cr.restore()


GObject.type_register(CellRendererTime)

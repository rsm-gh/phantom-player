#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2016, 2024 Rafael Senties Martinelli.
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

from datetime import datetime
from gi.repository import Gtk, Gdk, GLib, PangoCairo, GObject

from view.gtk_utils import get_general_font_description


def format_timestamp(number):
    if number == 0:
        return ''

    return str(datetime.fromtimestamp(number))


class CellRendererTimeStamp(Gtk.CellRenderer):
    """ CellRenderer to display timestamps, Ex: 10000 to '1970-01-01 01:16:40' """

    __gproperties__ = {
        'timestamp': ('gint64',  # type
                      "integer prop",  # nick
                      "A property that contains a number in milliseconds",  # blurb
                      0,  # min
                      GLib.MAXINT64,  # max
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
        self.timestamp = 0
        self.color = Gdk.RGBA()
        self.font_description = get_general_font_description()

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    """
    def activate(self, event, widget, path, background_area, cell_area, flags):
        print(flags)
    
    def do_get_size(self, widget, cell_area):
        return (0, 0, cell_area.width, cell_area.height)
        return (0, 0, self.kilobytes.get_width(), self.kilobytes.get_height())
    """

    def do_render(self, cr, _widget, _background_area, cell_area, _flags):
        cr.set_source_rgb(self.color.red, self.color.green, self.color.blue)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(self.font_description)
        layout.set_text(format_timestamp(self.timestamp), -1)
        cr.save()
        #  PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x, cell_area.y)
        PangoCairo.show_layout(cr, layout)
        cr.restore()


GObject.type_register(CellRendererTimeStamp)

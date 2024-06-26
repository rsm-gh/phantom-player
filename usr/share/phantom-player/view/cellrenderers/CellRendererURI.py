#!/usr/bin/python3
#

#  Copyright (C) 2016, 2019 Rafael Senties Martinelli
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


import gi

gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, PangoCairo, GObject

from urllib.parse import unquote

from .constants import FONT_COLOR, GENERAL_FONT_DESCRIPTION


def format_uri(uri: str):
    """
        Format an uri to a filesystem path.
    """
    return unquote(uri).replace('file://', '')


class CellRendererURI(Gtk.CellRenderer):
    """ CellRenderer to display filesystem paths."""

    __gproperties__ = {
        'uri': ('gchararray',  # type
                'string prop',  # nick
                'A property that contains a filesystem path',  # blurb
                '',  # default
                GObject.PARAM_READWRITE  # flags
                ),
    }

    def __init__(self):
        super().__init__()
        self.uri = ''

        # the formatted value is stored to gain in performance when calling do_render().
        self.__formated_uri = ''

    def do_set_property(self, pspec, value):
        self.__formated_uri = format_uri(self.uri)
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_render(self, cr, _widget, _background_area, cell_area, _flags):
        cr.set_source_rgb(FONT_COLOR[0], FONT_COLOR[1], FONT_COLOR[2])
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(GENERAL_FONT_DESCRIPTION)
        layout.set_text(self.__formated_uri, -1)
        cr.save()
        # PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x, cell_area.y)
        PangoCairo.show_layout(cr, layout)
        cr.restore()


#     def activate(self, event, widget, path, background_area, cell_area, flags):
#         print(flags)

# def do_get_size(self, widget, cell_area):
# return (0, 0, cell_area.width, cell_area.height)
# return (0, 0, self.kilobytes.get_width(), self.kilobytes.get_height())


GObject.type_register(CellRendererURI)

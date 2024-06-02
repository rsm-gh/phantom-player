#!/usr/bin/python3
#

#  Copyright (C) 2016, 2024  Rafael Senties Martinelli
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
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA.

import os
from math import pi

from gi.repository import Gtk, Gdk, GObject, PangoCairo
from gi.repository.GdkPixbuf import Pixbuf

from settings import _DEFAULT_IMG_WIDTH, _DEFAULT_IMG_HEIGHT
from view.CellRenderers.constants import FONT_COLOR, GENERAL_FONT_DESCRIPTION


class CellRendererPlaylist(Gtk.CellRenderer):
    """ CellRenderer to display the Playlist images """

    __gproperties__ = {
        'progress': (int,  # type
                     "playlist progress",  # nick
                     "A property that contains the percent progress of the playlist",  # blurb
                     0,  # min
                     100,  # max
                     0,  # default
                     GObject.PARAM_READWRITE  # flags
                     ),

        'name': ('gchararray',  # type
                 "playlist name",  # nick
                 "Playlist Name",  # blurb
                 '',  # default
                 GObject.PARAM_READWRITE  # flags
                 ),

        'pixbuf': (Pixbuf,  # type
                   "playlist pixbuf",  # nick
                   "Image of the playlist",  # blurb
                   GObject.PARAM_READWRITE,  # flags
                   ),
    }

    def __init__(self):
        super().__init__()
        self.progress = 0
        self.name = ""
        self.pixbuf = Pixbuf()
        self.__formated_text = ""

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)
        self.__formated_text = self.format_long_text(self.name)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_get_size(self, widget, cell_area):
        #return (0, 0, cell_area.width, cell_area.height)
        return 0, 0, _DEFAULT_IMG_WIDTH, _DEFAULT_IMG_HEIGHT + 27

    def do_render(self, cr, widget, background_area, cell_area, flags):

        cr.set_source_rgba(.149, .149, .149, 1)
        cr.set_line_width(1)
        cr.rectangle(cell_area.x, cell_area.y, _DEFAULT_IMG_WIDTH, _DEFAULT_IMG_HEIGHT + 27)
        cr.fill()

        #self.__draw_rectangle(cr, [cell_area.y,
        #                                cell_area.x,
        #                                cell_area.x+20,
        #                                cell_area.x-20], 10)

        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, cell_area.x, cell_area.y)
        cr.paint()

        self.__draw_progress(cr, cell_area)
        self.__draw_name(cr, cell_area)

        cr.set_source_rgba(.149, .149, .149, 1)
        cr.set_line_width(5)
        cr.rectangle(cell_area.x, cell_area.y, _DEFAULT_IMG_WIDTH, _DEFAULT_IMG_HEIGHT + 27)
        cr.stroke()

    def __draw_name(self, cr, cell_area):
        cr.set_source_rgb(1, 1, 1)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(GENERAL_FONT_DESCRIPTION)
        layout.set_text(self.__formated_text, -1)
        cr.save()
        #PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x + 4, cell_area.y + _DEFAULT_IMG_HEIGHT + 5)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

    def __draw_progress(self, cr, cell_area):
        progress_height = cell_area.y + _DEFAULT_IMG_HEIGHT

        cr.set_line_width(4)

        cr.set_source_rgba(1, .9, .9, 1)
        cr.move_to(cell_area.x, progress_height)
        cr.line_to(cell_area.x + _DEFAULT_IMG_WIDTH, progress_height)
        cr.stroke()

        if self.progress > 0:
            cr.set_source_rgba(1, 0, 0, 1)

            cr.move_to(cell_area.x, progress_height)
            width = int((cell_area.x + _DEFAULT_IMG_WIDTH) * (self.progress / 100))
            cr.line_to(width, progress_height)

        cr.stroke()

    @staticmethod
    def __draw_rectangle(cr, top, bottom, left, right, radius, fill=True):
        """ draws rectangles with rounded (circular arc) corners """
        cr.set_source_rgba(0, 0, 0, 1)
        cr.set_line_width(3)

        cr.rectangle(left, 300, 400, 800)

        #cr.arc(top + radius, left + radius, radius, 2 * (pi / 2), 3 * (pi / 2))
        #cr.arc(bottom - radius, left + radius, radius, 3 * (pi / 2), 4 * (pi / 2))
        #cr.arc(bottom - radius, right - radius, radius, 0 * (pi / 2), 1 * (pi / 2))  # ;o)
        #cr.arc(top + radius, right - radius, radius, 1 * (pi / 2), 2 * (pi / 2))
        #cr.close_path()

        #if fill:
        #    cr.fill()
        #else:
        cr.stroke()

    @staticmethod
    def format_long_text(text, length=11):
        """
            Ex: "Anticonstitutionellement" to "Anticonstitu…"
        """

        if text is None:
            return ''

        elif len(text) > length:
            return text[:length - 3] + '…'

        return text


GObject.type_register(CellRendererPlaylist)

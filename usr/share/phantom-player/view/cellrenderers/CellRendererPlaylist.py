#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2016, 2024 Rafael Senties Martinelli.
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

from gi.repository.GdkPixbuf import Pixbuf
from gi.repository import Gtk, Gdk, GObject, PangoCairo

from settings import IconSize
from view.gtk_utils import get_general_font_description

_PROGRESS_BAR_HEIGHT = 4


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

        'color': (Gdk.RGBA,  # type
                  "text color",  # nick
                  "Text color of the name",  # blurb
                  GObject.PARAM_READWRITE,  # flags
                  ),
    }

    def __init__(self):
        super().__init__()
        self.progress = 0
        self.name = ""
        self.pixbuf = Pixbuf()
        self.color = Gdk.RGBA()
        self.font_description = get_general_font_description()

        self.__formated_text = ""
        self.__icon_width = IconSize.Small._width
        self.__icon_height = IconSize.Small._height

    def set_icon_size(self, width, height):
        self.__icon_width = width
        self.__icon_height = height

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)
        self.__formated_text = self.format_long_text(self.name)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_get_size(self, _widget, _cell_area):
        #  return (0, 0, cell_area.width, cell_area.height)
        return 0, 0, self.__icon_width, self.__icon_height + _PROGRESS_BAR_HEIGHT

    def do_render(self, cr, _widget, _background_area, cell_area, _flags):
        self.__draw_name(cr, cell_area)
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, cell_area.x, cell_area.y)
        cr.paint()

        self.__draw_progress(cr, cell_area)

    def __draw_name(self, cr, cell_area):
        cr.set_source_rgb(self.color.red, self.color.green, self.color.blue)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(self.font_description)
        layout.set_text(self.__formated_text, -1)
        cr.save()
        #  PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x + 2, cell_area.y + self.__icon_height - 25)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

    def __draw_progress(self, cr, cell_area):

        cr.set_line_width(_PROGRESS_BAR_HEIGHT)
        progress_height = cell_area.y + self.__icon_height + _PROGRESS_BAR_HEIGHT - (_PROGRESS_BAR_HEIGHT / 2)

        cr.set_source_rgba(1, .9, .9, 1)
        cr.move_to(cell_area.x, progress_height)
        cr.line_to(cell_area.x + self.__icon_width, progress_height)
        cr.stroke()

        if self.progress > 0:
            cr.set_source_rgba(1, 0, 0, 1)
            cr.move_to(cell_area.x, progress_height)
            width = int(self.__icon_width * (self.progress / 100))
            cr.line_to(cell_area.x + width, progress_height)
            cr.stroke()

    @staticmethod
    def format_long_text(text, length=12):
        """
            Ex: "Anticonstitutionellement" to "Anticonstitu…"
        """

        if text is None:
            return ''

        elif len(text) > length:
            return text[:length - 3] + '…'

        return text


GObject.type_register(CellRendererPlaylist)

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

from urllib.parse import unquote
from gi.repository import Gtk, Gdk, PangoCairo, GObject

from view.gtk_utils import get_general_font_description


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

        'color': (Gdk.RGBA,  # type
                  "text color",  # nick
                  "Text color of the rating",  # blurb
                  GObject.PARAM_READWRITE,  # flags
                  ),

    }

    def __init__(self):
        super().__init__()
        self.uri = ''
        self.color = Gdk.RGBA()
        self.font_description = get_general_font_description()

        # the formatted value is stored to gain in performance when calling do_render().
        self.__formated_uri = ''

    def do_set_property(self, pspec, value):
        self.__formated_uri = format_uri(self.uri)
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_render(self, cr, _widget, _background_area, cell_area, _flags):
        cr.set_source_rgb(self.color.red, self.color.green, self.color.blue)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(self.font_description)
        layout.set_text(self.__formated_uri, -1)
        cr.save()
        # PangoCairo.update_layout(cr, layout)
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

GObject.type_register(CellRendererURI)

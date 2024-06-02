#!/usr/bin/python3
#

#  Copyright (C) 2016, 2019  Rafael Senties Martinelli 
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


import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, PangoCairo, GObject

from .constants import FONT_COLOR, GENERAL_FONT_DESCRIPTION

def format_bytes(num):
    """ Format a bytesnumber into human readable string."""
    
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024:
            return '{0} {1}{2}'.format(round(num,0), unit, 'B')
        num /= 1024
        
    return '{0} {1}{2}'.format(round(num,0), 'Yi', 'B')


class CellRendererBytes(Gtk.CellRenderer):
    """ CellRenderer to display kilobytes, ex: 234234 -> 03:54 """
    
    __gproperties__ = {
        'bytes': (      'glong', # type
                        "long prop", # nick
                        "A property that contains a number of bytes.", # blurb
                        0, # min
                        9223372036854775807, # max
                        0, # default
                        GObject.PARAM_READWRITE # flags
                        ),
    }

    def __init__(self):
        super().__init__()
        self.bytes = 0
        
        # the formatted value is stored to gain in perfomance when calling do_render().
        self.__formated_bytes = '' 
                
    def do_set_property(self, pspec, value):
        self.__formated_bytes = format_bytes(self.bytes)
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)
        
    def do_render(self, cr, widget, background_area, cell_area, flags):
        
        cr.set_source_rgb (FONT_COLOR[0], FONT_COLOR[1], FONT_COLOR[2])
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(GENERAL_FONT_DESCRIPTION)
        layout.set_text(self.__formated_bytes, -1)
        cr.save()
        #PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x, cell_area.y)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

#     def activate(self, event, widget, path, background_area, cell_area, flags):
#         print(flags)
        
    #def do_get_size(self, widget, cell_area):
        #return (0, 0, cell_area.width, cell_area.height)
        #return (0, 0, self.kilobytes.get_width(), self.kilobytes.get_height())

GObject.type_register(CellRendererBytes)


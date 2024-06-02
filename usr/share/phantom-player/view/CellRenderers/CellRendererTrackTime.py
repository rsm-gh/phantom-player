#!/usr/bin/python3
#

#  Copyright (C) 2016  Rafael Senties Martinelli 
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

from datetime import timedelta

from .constants import FONT_COLOR, GENERAL_FONT_DESCRIPTION


def FORMAT_miliseconds(miliseconds):
    time_string=str(timedelta(milliseconds=miliseconds)).split('.')[0]

    # remove the hours if they are not necessary.
    try:
        if int(time_string.split(':',1)[0]) == 0:  
            time_string=time_string.split(':',1)[1]
    except:
        pass
    
    return time_string

class CellRendererTrackTime(Gtk.CellRenderer):
    """ CellRenderer to display miliseconds to time, ex: 234234 -> 03:54 """
    
    __gproperties__ = {
        'miliseconds': (    'glong', # type
                            "integer prop", # nick
                            "A property that contains a number in miliseconds", # blurb
                            0, # min
                            9223372036854775807, # max
                            0, # default
                            GObject.PARAM_READWRITE # flags
                            ),
    }

    def __init__(self):
        super().__init__()
        self.miliseconds = 0
        
    def activate(self, event, widget, path, background_area, cell_area, flags):
        print(flags)
        
    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)
        
    #def do_get_size(self, widget, cell_area):
        #return (0, 0, cell_area.width, cell_area.height)
        #return (0, 0, self.miliseconds.get_width(), self.miliseconds.get_height())

    def do_render(self, cr, widget, background_area, cell_area, flags):
        
        cr.set_source_rgb (FONT_COLOR[0], FONT_COLOR[1], FONT_COLOR[2])
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(GENERAL_FONT_DESCRIPTION)
        layout.set_text(FORMAT_miliseconds(self.miliseconds), -1)
        cr.save()
        #PangoCairo.update_layout(cr, layout)
        cr.move_to(cell_area.x, cell_area.y)
        PangoCairo.show_layout(cr, layout)
        cr.restore()

GObject.type_register(CellRendererTrackTime)


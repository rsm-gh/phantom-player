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
from gi.repository import Gtk, Pango

def GTK_get_default_font_color():
        
    for color in SETTINGS.get_property('gtk-color-scheme').split('\n'):
        if 'text' in color:
            text_color=color.split(':')[1].strip()
            
            if ';' in text_color:
                text_color=text_color.split(';',1)[0]
            
            return text_color

    return '#000000'


def CONVERT_hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


SETTINGS=Gtk.Settings.get_default()

FONT_COLOR=CONVERT_hex_to_rgb(GTK_get_default_font_color())
FONT_STR=SETTINGS.get_property('gtk-font-name')
GENERAL_FONT_DESCRIPTION=Pango.font_description_from_string(FONT_STR)

FONT_TYPE=FONT_STR.rsplit(' ',1)[0]
FONT_SIZE=FONT_STR.rsplit(' ',1)[1]

FONT_CELLRATING='{} {}'.format(FONT_TYPE, int(FONT_SIZE)+5)
FONT_CELLRATING_DESCRIPTION=Pango.font_description_from_string(FONT_CELLRATING)

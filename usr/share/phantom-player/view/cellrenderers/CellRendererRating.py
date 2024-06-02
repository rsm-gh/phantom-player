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


from .constants import FONT_CELLRATING_DESCRIPTION


"""
    I'm currently stuck for detecting the mouse-click/mouse-over so I can change the stars.
"""


class CellRendererRating(Gtk.CellRenderer):
    """ Cellrenderer to display ratings from 0 to 5: ★★★★★, ★★★☆☆, etc """
    
    __gproperties__ = {
        'rating': ( int, # type
                    "integer prop", # nick
                    "A property that contains an integer", # blurb
                    0, # min
                    5, # max
                    0, # default
                    GObject.PARAM_READWRITE # flags
                    ),
    }

    def __init__(self, treeview=False):
        super().__init__()
        self.font_size=15
        self.font="Sans Bold {}".format(self.font_size)
        self.rating = 0
        
        self._clicked=()
        self._clicked_function=False
        
        if treeview:
            self.connect_treeview(treeview)

    def connect_rating(self, treeviewcolumn, column=0, func=False):
        """
            This should be conected once the cellrendere has been
            added to the treeviewcolumn.
            
            column=0, is the number of the rating column at the
            treeview liststore.
            
            func is a function to be called when a rating is edited,
            it must accept the arguments (treeview, treepath, rating)
            
        """
        treeview=treeviewcolumn.get_tree_view()
        treeview.connect('cursor-changed', self.update_from_click)
        self._column=column
        self._liststore=treeview.get_model()
        self._clicked_function=func

    def do_render(self, cr, treeview, background_area, cell_area, flags):
        mouse_x, mouse_y = treeview.get_pointer()
        cell_render_x = mouse_x - cell_area.x
        
        #
        # Update the rating if it was clicked (the liststore is updated too)
        #
        if self._clicked != ():
            x_click_coord=self._clicked[0]
            self._clicked=()
            
            # Check if the click was inside the cell
            #
            if x_click_coord >= cell_area.x and x_click_coord <= cell_area.x+self.font_size*5 and 'SELECTED' in str(flags):
                rating=round(cell_render_x/self.font_size)
                
                if rating >= 0 and rating <= 5 and rating != self.rating:
                    self.rating=rating

                    try:
                        pointing_treepath=treeview.get_path_at_pos(mouse_x, mouse_y-self.font_size)[0]
                        self._liststore[pointing_treepath][self._column]=self.rating
                        
                    except Exception as e:
                        print(e)

                    if self._clicked_function:
                        self._clicked_function(self._liststore, pointing_treepath, rating)

        #
        # Draw the rating
        #
        cr.translate (0, 0)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(FONT_CELLRATING_DESCRIPTION)
    
        y_height_correction=self.font_size/3
        cell_height=self.font_size+1
    
        if 'GTK_CELL_RENDERER_FOCUSED' in str(flags) and self.rating < 5:
            for i in range(5):
                if i < self.rating:
                    layout.set_text("★", -1)
                else:
                    layout.set_text("☆", -1)
                  
                cr.save()
                PangoCairo.update_layout (cr, layout)
                cr.move_to (cell_area.x+i*cell_height, cell_area.y-y_height_correction)
                PangoCairo.show_layout (cr, layout)
                cr.restore()
            
        else:
            for i in range(self.rating):
                layout.set_text("★", -1)
                cr.save()
                PangoCairo.update_layout (cr, layout)
                cr.move_to (cell_area.x+i*cell_height, cell_area.y-y_height_correction)
                PangoCairo.show_layout (cr, layout)
                cr.restore()

    def update_from_click(self, treeview, data=None):
        self._clicked=treeview.get_pointer()

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)
        
    def do_get_size(self, widget, cell_area):
        return (0, 0, self.font_size*5, self.font_size+5)


GObject.type_register(CellRendererRating)

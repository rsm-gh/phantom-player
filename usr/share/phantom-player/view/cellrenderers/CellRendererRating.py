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


from gi.repository import Gtk, Gdk, PangoCairo, GObject

from view.gtk_utils import get_cellrender_font_description


class CellRendererRating(Gtk.CellRenderer):
    """ Cellrenderer to display ratings from 0 to 5: ★★★★★, ★★★☆☆, etc """

    __gproperties__ = {
        'rating': ('gint',  # type
                   "integer prop",  # nick
                   "A property that contains an integer",  # blurb
                   0,  # min
                   5,  # max
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
        self.font_size = 15
        self.rating = 0
        self.color = Gdk.RGBA()
        self.font_description = get_cellrender_font_description()

        self.__cursor_changed_pointer = None
        self.__liststore = None
        self.__rating_column_nb = None
        self.__rating_changed_func = None

    def connect_rating(self, treeview, column=0, func=None):
        """
            This should be connected once the cellrenderer has been added to the treeviewcolumn.
            
            column=0 is the number of the rating column at the treeview liststore.
            
            func is a function to be called when a rating is edited.
            It must accept the arguments (treeview, treepath, rating)
        """
        treeview.connect('cursor-changed', self.__on_cursor_changed)
        self.__rating_column_nb = column
        self.__liststore = treeview.get_model()
        self.__rating_changed_func = func

    def do_render(self, cr, treeview, _background_area, cell_area, flags):

        #
        # Update the rating if it was clicked (the liststore is updated too)
        #
        if self.__cursor_changed_pointer is not None:
            clicked_x, clicked_y = self.__cursor_changed_pointer
            self.__cursor_changed_pointer = None

            # Check if the click was inside the cell
            #
            if cell_area.x <= clicked_x <= cell_area.x + self.font_size * 5 and (Gtk.CellRendererState.SELECTED & flags):
                rating = round((clicked_x - cell_area.x) / self.font_size)

                if 0 <= rating <= 5 and rating != self.rating:

                    try:
                        pointing_treepath = treeview.get_path_at_pos(clicked_x, clicked_y - self.font_size)[0]
                    except Exception as e:
                        print(e)
                    else:

                        self.rating = rating

                        if None not in (self.__liststore, self.__rating_column_nb):
                            self.__liststore[pointing_treepath][self.__rating_column_nb] = rating

                        if self.__rating_changed_func is not None:
                            self.__rating_changed_func(self.__liststore, pointing_treepath, rating)

        #
        # Draw the rating
        #
        cr.set_source_rgb(self.color.red, self.color.green, self.color.blue)
        layout = PangoCairo.create_layout(cr)
        layout.set_font_description(self.font_description)

        y_height_correction = self.font_size / 3
        cell_height = self.font_size + 1

        if Gtk.CellRendererState.FOCUSED & flags:
            for i in range(5):

                cr.move_to(cell_area.x + i * cell_height, cell_area.y - y_height_correction)

                if i < self.rating:
                    layout.set_text("★", -1)
                else:
                    layout.set_text("☆", -1)

                cr.save()
                PangoCairo.update_layout(cr, layout)
                PangoCairo.show_layout(cr, layout)
                cr.restore()

        else:
            for i in range(self.rating):
                cr.move_to(cell_area.x + i * cell_height, cell_area.y - y_height_correction)
                layout.set_text("★", -1)
                cr.save()
                PangoCairo.update_layout(cr, layout)
                PangoCairo.show_layout(cr, layout)
                cr.restore()

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_get_size(self, _widget, _cell_area):
        return 0, 0, self.font_size * 5, self.font_size + 5

    def __on_cursor_changed(self, treeview, *_):
        self.__cursor_changed_pointer = treeview.get_pointer()


GObject.type_register(CellRendererRating)

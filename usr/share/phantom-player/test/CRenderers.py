#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
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

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')  # necessary for the cell renderers
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf


from view import gtk_utils
from view.cellrenderers.CellRendererRating import CellRendererRating
from view.cellrenderers.CellRendererTime import CellRendererTime
from view.cellrenderers.CellRendererBytes import CellRendererBytes
from view.cellrenderers.CellRendererTimeStamp import CellRendererTimeStamp
from view.cellrenderers.CellRendererURI import CellRendererURI
from view.cellrenderers.CellRendererPlaylist import CellRendererPlaylist

from settings import IconSize


class Window(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self)
        self.connect('destroy', self.on_quit)

        box = Gtk.Box()

        _, default_color = gtk_utils.get_default_color()

        liststore = Gtk.ListStore(int, 'glong', str)
        liststore.append([0, 100, '/home/rsm/desktop/abc.ogg'])
        liststore.append([1, 23400, '/home/rsm/desktop/abc.ogg'])
        liststore.append([2, 342342, '/home/rsm/desktop/abc.ogg'])
        liststore.append([3, 5424334, '/home/rsm/desktop/abc.ogg'])
        liststore.append([4, 83994234, '/home/rsm/desktop/abc.ogg'])
        liststore.append([5, 9223375807, '/home/rsm/desktop/abc.ogg'])

        treeview = Gtk.TreeView(model=liststore)

        treeviewcolumn = Gtk.TreeViewColumn("Rating")
        treeviewcolumn.set_resizable(True)
        cellrenderer = CellRendererRating()
        cellrenderer.color = default_color

        treeviewcolumn.pack_start(cellrenderer, True)
        treeviewcolumn.add_attribute(cellrenderer, 'rating', 0)
        treeview.append_column(treeviewcolumn)
        cellrenderer.connect_rating(treeview, column=0, func=self.on_rating_changed)

        treeviewcolumn = Gtk.TreeViewColumn("Time")
        treeviewcolumn.set_resizable(True)
        cellrenderer = CellRendererTime()
        cellrenderer.color = default_color
        treeviewcolumn.pack_start(cellrenderer, True)
        treeviewcolumn.add_attribute(cellrenderer, 'time', 1)
        treeview.append_column(treeviewcolumn)

        treeviewcolumn = Gtk.TreeViewColumn("Bytes")
        treeviewcolumn.set_resizable(True)
        cellrenderer = CellRendererBytes()
        cellrenderer.color = default_color
        treeviewcolumn.pack_start(cellrenderer, True)
        treeviewcolumn.add_attribute(cellrenderer, 'bytes', 1)
        treeview.append_column(treeviewcolumn)

        treeviewcolumn = Gtk.TreeViewColumn("Time Stamp")
        treeviewcolumn.set_resizable(True)
        cellrenderer = CellRendererTimeStamp()
        cellrenderer.color = default_color
        treeviewcolumn.pack_start(cellrenderer, True)
        treeviewcolumn.add_attribute(cellrenderer, 'timestamp', 1)
        treeview.append_column(treeviewcolumn)

        treeviewcolumn = Gtk.TreeViewColumn("URI")
        treeviewcolumn.set_resizable(True)
        cellrenderer = CellRendererURI()
        cellrenderer.color = default_color
        treeviewcolumn.pack_start(cellrenderer, True)
        treeviewcolumn.add_attribute(cellrenderer, 'uri', 2)
        treeview.append_column(treeviewcolumn)

        box.add(treeview)

        #  self.set_default_size(200, 200)
        liststore = Gtk.ListStore(int, Pixbuf, str, int)
        iconview = Gtk.IconView.new()
        iconview.set_model(liststore)

        cellrenderer_playlist = CellRendererPlaylist()
        iconview.pack_start(cellrenderer_playlist, True)
        iconview.add_attribute(cellrenderer_playlist, 'pixbuf', 1)
        iconview.add_attribute(cellrenderer_playlist, 'name', 2)
        iconview.add_attribute(cellrenderer_playlist, 'progress', 3)

        playlist_data = (
            ('playlist toto', 30),
            ('this is a very long name', 100),
            ('playlist yep', 0),
            ('last value', 50)
        )

        default_pixbuf = Pixbuf.new_from_file_at_scale("/home/rsm/Pictures/c1019_chip_lg.jpg",
                                                       IconSize.Big._width,
                                                       IconSize.Big._height,
                                                       True)

        cellrenderer_playlist.set_icon_size(IconSize.Big._width, IconSize.Big._height)

        for name, percent in playlist_data:
            liststore.append([-1, default_pixbuf, name, percent])

        box.add(iconview)

        self.add(box)
        self.show_all()

    @staticmethod
    def on_quit(*_):
        Gtk.main_quit()

    @staticmethod
    def on_rating_changed(liststore, treepath, rating):
        print('CRenderers.on_rating_changed', liststore, treepath, rating)


if __name__ == "__main__":
    _ = Window()
    Gtk.main()

#!/usr/bin/python3

#
#    This file is part of Phantom Player.
#
# Copyright (c) 2014-2015, 2024-2025 Rafael Senties Martinelli.
#
#  This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License 2.1 as
#   published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/lgpl-2.1.en.html>.
#

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from env import *

from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf

from Paths import _ICON_LOGO_BIG
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

        liststore = Gtk.ListStore(int, 'gint64', str)
        liststore.append([0, 100, '/home/rsm/desktop/0.ogg'])
        liststore.append([1, 23400, '/home/rsm/desktop/1.ogg'])
        liststore.append([2, 342342, '/home/rsm/desktop/2.ogg'])
        liststore.append([3, 5424334, '/home/rsm/desktop/3.ogg'])
        liststore.append([4, 83994234, '/home/rsm/desktop/4.ogg'])
        liststore.append([5, 9223375807, '/home/rsm/desktop/5.ogg'])

        treeview = Gtk.TreeView(model=liststore)
        treeview.set_reorderable(True)
        treeview.set_size_request(width=500, height=-1)

        treeview_column = Gtk.TreeViewColumn("Rating")
        treeview_column.set_resizable(True)
        cellrenderer = CellRendererRating()
        cellrenderer.color = default_color

        treeview_column.pack_start(cellrenderer, True)
        treeview_column.add_attribute(cellrenderer, 'rating', 0)
        treeview.append_column(treeview_column)
        cellrenderer.connect_rating(treeview, column=0, func=self.on_rating_changed)

        treeview_column = Gtk.TreeViewColumn("Time")
        treeview_column.set_resizable(True)
        cellrenderer = CellRendererTime()
        cellrenderer.color = default_color
        treeview_column.pack_start(cellrenderer, True)
        treeview_column.add_attribute(cellrenderer, 'time', 1)
        treeview.append_column(treeview_column)

        treeview_column = Gtk.TreeViewColumn("Bytes")
        treeview_column.set_resizable(True)
        cellrenderer = CellRendererBytes()
        cellrenderer.color = default_color
        treeview_column.pack_start(cellrenderer, True)
        treeview_column.add_attribute(cellrenderer, 'bytes', 1)
        treeview.append_column(treeview_column)

        treeview_column = Gtk.TreeViewColumn("Time Stamp")
        treeview_column.set_resizable(True)
        cellrenderer = CellRendererTimeStamp()
        cellrenderer.color = default_color
        treeview_column.pack_start(cellrenderer, True)
        treeview_column.add_attribute(cellrenderer, 'timestamp', 1)
        treeview.append_column(treeview_column)

        treeview_column = Gtk.TreeViewColumn("URI")
        treeview_column.set_resizable(True)
        cellrenderer = CellRendererURI()
        cellrenderer.color = default_color
        treeview_column.pack_start(cellrenderer, True)
        treeview_column.add_attribute(cellrenderer, 'uri', 2)
        treeview.append_column(treeview_column)

        box.add(treeview)

        #  self.set_default_size(200, 200)
        liststore = Gtk.ListStore(int, Pixbuf, str, int)
        iconview = Gtk.IconView.new()
        iconview.set_model(liststore)
        iconview.set_hexpand(True)
        iconview.set_vexpand(True)

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

        default_pixbuf = Pixbuf.new_from_file_at_scale(filename=_ICON_LOGO_BIG,
                                                       width=IconSize.Big._width,
                                                       height=IconSize.Big._height,
                                                       preserve_aspect_ratio=True)

        cellrenderer_playlist.set_icon_size(width=IconSize.Big._width, height=IconSize.Big._height)

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

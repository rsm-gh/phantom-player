#!/usr/bin/python3
#

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli.
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
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import os
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
from gi.repository import Gtk, GObject, Gdk

from Texts import Texts
from Paths import ICON_LOGO_SMALL, HOME_PATH


def gtk_get_first_selected_cell_from_selection(gtk_selection, column=0):
    model, treepaths = gtk_selection.get_selected_rows()

    if treepaths == []:
        return None

    return model[treepaths[0]][column]


def gtk_set_first_selected_cell_from_selection(gtk_selection, column, value):
    model, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        model[treepaths[0]][column] = value


def gtk_remove_first_selected_row_from_liststore(gtk_selection):
    model, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        model.remove(model.get_iter(treepaths[0]))


def gtk_get_merged_cells_from_treepath(gtk_liststore, gtk_treepath, cell1, cell2):
    return '{}{}'.format(gtk_liststore[gtk_treepath][cell1], gtk_liststore[gtk_treepath][cell2])


def gtk_default_font_color():
    settings = Gtk.Settings.get_default()

    colors = settings.get_property('gtk-color-scheme')
    colors = colors.split('\n')

    for color in colors:
        if 'text' in color:
            text_color = color.split(':')[1].strip()

            if ';' in text_color:
                text_color = text_color.split(';', 1)[0]

            return text_color

    return '#000000'


def gtk_info(parent, text1, text2=None):
    dialog = Gtk.MessageDialog(parent,
                               Gtk.DialogFlags.MODAL,
                               Gtk.MessageType.INFO,
                               Gtk.ButtonsType.CLOSE,
                               text1)

    dialog.set_default_response(Gtk.ResponseType.NONE)

    dialog.set_icon_from_file(ICON_LOGO_SMALL)

    if text2 is not None:
        dialog.format_secondary_text(text2)

    response = dialog.run()
    dialog.destroy()


def gtk_folder_chooser(parent):
    window_choose_folder = Gtk.FileChooserDialog(Texts.GUI.title,
                                                 parent,
                                                 Gtk.FileChooserAction.SELECT_FOLDER,
                                                 (Gtk.STOCK_CANCEL,
                                                  Gtk.ResponseType.CANCEL,
                                                  Gtk.STOCK_OPEN,
                                                  Gtk.ResponseType.OK))

    window_choose_folder.set_icon_from_file(ICON_LOGO_SMALL)

    window_choose_folder.set_current_folder(HOME_PATH)

    response = window_choose_folder.run()
    if response == Gtk.ResponseType.OK:
        folder_path = window_choose_folder.get_filename()
        window_choose_folder.destroy()

        if folder_path and os.path.exists(folder_path):
            default_folder_chooser_path = os.path.dirname(folder_path)

        return folder_path
    else:
        window_choose_folder.destroy()
        return False

def gtk_dialog_question(parent, text1, text2):
    dialog = Gtk.MessageDialog(parent,
                               Gtk.DialogFlags.MODAL,
                               Gtk.MessageType.QUESTION,
                               Gtk.ButtonsType.YES_NO,
                               text1)

    dialog.set_icon_from_file(ICON_LOGO_SMALL)

    if text2 is not None:
        dialog.format_secondary_text(text2)

    response = dialog.run()

    dialog.hide()

    if response == Gtk.ResponseType.YES:
        return True

    elif response == Gtk.ResponseType.NO:
        return False

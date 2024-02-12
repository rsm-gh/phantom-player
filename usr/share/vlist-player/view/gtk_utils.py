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

import gi
import os

gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
from gi.repository import Gtk, GObject, Gdk

from Texts import Texts
from Paths import ICON_LOGO_SMALL


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

def gtk_selection_get_first_selected_cell(gtk_selection, column=0):
    model, treepaths = gtk_selection.get_selected_rows()

    if treepaths == []:
        return None

    return model[treepaths[0]][column]


def gtk_selection_set_first_selected_cell(gtk_selection, column, value):
    model, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        model[treepaths[0]][column] = value


def gtk_liststore_remove_first_selected_row(gtk_selection):
    model, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        model.remove(model.get_iter(treepaths[0]))


def gtk_treepath_get_merged_cells(gtk_liststore, gtk_treepath, cell1, cell2):
    return '{}{}'.format(gtk_liststore[gtk_treepath][cell1], gtk_liststore[gtk_treepath][cell2])

def gtk_dialog_file(parent, start_path=None):
    dialog = Gtk.FileChooserDialog(title=Texts.GUI.title,
                                   parent=parent,
                                   action=Gtk.FileChooserAction.SELECT_FOLDER)

    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.CANCEL,
                       Gtk.STOCK_OPEN,
                       Gtk.ResponseType.OK)

    dialog.set_icon_from_file(ICON_LOGO_SMALL)

    if start_path is not None and os.path.exists(start_path):
        dialog.set_current_folder(start_path)

    dir_path = None

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        dir_path = dialog.get_filename()

    dialog.destroy()

    return dir_path

def gtk_dialog_folder(parent, file_filter=None, start_path=None):
    dialog = Gtk.FileChooserDialog(title=Texts.GUI.title,
                                   parent=parent,
                                   action=Gtk.FileChooserAction.OPEN)

    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.CANCEL,
                       Gtk.STOCK_OPEN,
                       Gtk.ResponseType.OK)

    dialog.set_default_response(Gtk.ResponseType.NONE)
    dialog.set_icon_from_file(ICON_LOGO_SMALL)

    dialog.set_transient_for(parent)

    if filter is not None:
        dialog.add_filter(file_filter)

    if start_path is not None and os.path.exists(start_path):
        dialog.set_current_folder(start_path)

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        file_path = dialog.get_filename()
    else:
        file_path = None
    dialog.destroy()

    return file_path


def gtk_dialog_question(parent, text1, text2=None):
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

def gtk_dialog_info(parent, text1, text2=None):
    dialog = Gtk.MessageDialog(parent,
                               Gtk.DialogFlags.MODAL,
                               Gtk.MessageType.INFO,
                               Gtk.ButtonsType.CLOSE,
                               text1)

    dialog.set_default_response(Gtk.ResponseType.NONE)

    dialog.set_icon_from_file(ICON_LOGO_SMALL)

    if text2 is not None:
        dialog.format_secondary_text(text2)

    _ = dialog.run()
    dialog.destroy()

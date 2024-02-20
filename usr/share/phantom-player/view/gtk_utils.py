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

def set_css(widget, css):
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode('utf-8'))
    context = widget.get_style_context()
    context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

def get_default_color(text_type='theme_text_color', widget=None, on_error='#000000'):
    """
        theme_text_color
        warning_color
        error_color
    """

    if widget is None:
        widget = Gtk.Entry()

    found, color = widget.get_style_context().lookup_color(text_type)

    if not found:
        color = Gdk.RGBA()
        color.parse(on_error)

    return found, color

def treeview_selection_get_first_cell(gtk_selection, column=0):
    model, treepaths = gtk_selection.get_selected_rows()

    if not treepaths:
        return None

    return model[treepaths[0]][column]


def treeview_selection_set_first_cell(gtk_selection, column, value):
    model, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        model[treepaths[0]][column] = value


def treeview_selection_remove_first_row(gtk_selection):
    model, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        model.remove(model.get_iter(treepaths[0]))

def dialog_select_directory(parent, start_path=None):
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

def dialog_select_file(parent, file_filter=None, start_path=None):
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

    if file_filter is not None:
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


def dialog_yes_no(parent, text1, text2=None):
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

def dialog_info(parent, text1, text2=None):
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

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

import os
from gi.repository import Gtk, Gdk, Pango

from Texts import Texts
from Paths import _ICON_LOGO_SMALL, _HOME_DIR


class FontColors:
    _default = 'theme_text_color'
    _success = 'success_color'
    _warning = 'warning_color'
    _error = 'error_color'


def set_css(widget, css):
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode('utf-8'))
    context = widget.get_style_context()
    context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)


def bind_header_click(treeview_column, bind_func):
    label = Gtk.Label(treeview_column.get_title())
    label.show()
    treeview_column.set_widget(label)

    widget = treeview_column.get_widget()
    while not isinstance(widget, Gtk.Button):
        widget = widget.get_parent()

    widget.connect('button-press-event', bind_func)


def get_general_font_description():
    settings = Gtk.Settings.get_default()
    font_string = settings.get_property('gtk-font-name')
    return Pango.font_description_from_string(font_string)


def get_cellrender_font_description():
    settings = Gtk.Settings.get_default()
    font_string = settings.get_property('gtk-font-name')

    font_type = font_string.rsplit(' ', 1)[0]
    font_size = font_string.rsplit(' ', 1)[1]

    font_cell = '{} {}'.format(font_type, int(font_size) + 5)
    return Pango.font_description_from_string(font_cell)


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


def iconview_get_first_icon(gtk_iconview, column=0):
    treepaths = gtk_iconview.get_selected_items()

    if not treepaths:
        return None

    liststore = gtk_iconview.get_model()

    return liststore[treepaths[0]][column]


def treeselection_get_first_cell(gtk_selection, column=0):
    liststore, treepaths = gtk_selection.get_selected_rows()

    if not treepaths:
        return None

    return liststore[treepaths[0]][column]


def treeselection_set_first_cell(gtk_selection, column, value):
    liststore, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        liststore[treepaths[0]][column] = value


def treeselection_remove_first_row(gtk_selection):
    liststore, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        liststore.remove(liststore.get_iter(treepaths[0]))


def dialog_select_directory(parent, start_path=None):
    dialog = Gtk.FileChooserDialog(title=Texts.GUI._title,
                                   parent=parent,
                                   action=Gtk.FileChooserAction.SELECT_FOLDER)

    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.CANCEL,
                       Gtk.STOCK_OPEN,
                       Gtk.ResponseType.OK)

    dialog.set_icon_from_file(_ICON_LOGO_SMALL)

    if start_path is not None and os.path.exists(start_path):
        dialog.set_current_folder(start_path)

    dir_path = None

    response = dialog.run()
    if response == Gtk.ResponseType.OK:
        dir_path = dialog.get_filename()

    dialog.destroy()

    return dir_path


def dialog_select_file(parent, file_filter=None, start_path=None):
    dialog = Gtk.FileChooserDialog(title=Texts.GUI._title,
                                   parent=parent,
                                   action=Gtk.FileChooserAction.OPEN)

    dialog.add_buttons(Gtk.STOCK_CANCEL,
                       Gtk.ResponseType.CANCEL,
                       Gtk.STOCK_OPEN,
                       Gtk.ResponseType.OK)

    dialog.set_default_response(Gtk.ResponseType.NONE)
    dialog.set_icon_from_file(_ICON_LOGO_SMALL)

    dialog.set_transient_for(parent)

    if file_filter is not None:
        dialog.add_filter(file_filter)

    if start_path is None or not os.path.exists(start_path):
        dialog.set_current_folder(_HOME_DIR)
    else:
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

    dialog.set_icon_from_file(_ICON_LOGO_SMALL)

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

    dialog.set_icon_from_file(_ICON_LOGO_SMALL)

    if text2 is not None:
        dialog.format_secondary_text(text2)

    _ = dialog.run()
    dialog.destroy()


def window_is_fullscreen(gtk_window):
    window = gtk_window.get_window()

    if window is None:
        return False

    elif Gdk.WindowState.FULLSCREEN & window.get_state():
        return True

    return False

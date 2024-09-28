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
from typing import Callable, Any
from gi.repository import Gtk, Gdk, Pango

from Texts import Texts
from Paths import _ICON_LOGO_SMALL, _HOME_DIR


class FontColors:
    _default = 'theme_text_color'
    _success = 'success_color'
    _warning = 'warning_color'
    _error = 'error_color'


def set_css(widget: Gtk.Widget, css: str) -> None:
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode('utf-8'))
    context = widget.get_style_context()
    context.add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)


def bind_header_click(treeview_column: Gtk.TreeViewColumn,
                      bind_func: Callable) -> None:
    label = Gtk.Label(label=treeview_column.get_title())
    label.show()
    treeview_column.set_widget(label)

    widget = treeview_column.get_widget()
    while not isinstance(widget, Gtk.Button):
        widget = widget.get_parent()

    widget.connect('button-press-event', bind_func)


def get_general_font_description() -> Pango.FontDescription:
    settings = Gtk.Settings.get_default()
    font_string = settings.get_property('gtk-font-name')
    return Pango.font_description_from_string(font_string)


def get_cellrender_font_description() -> Pango.FontDescription:
    settings = Gtk.Settings.get_default()
    font_string = settings.get_property('gtk-font-name')

    font_type = font_string.rsplit(' ', 1)[0]
    font_size = font_string.rsplit(' ', 1)[1]

    font_cell = '{} {}'.format(font_type, int(font_size) + 5)
    return Pango.font_description_from_string(font_cell)


def get_default_color(text_type: str='theme_text_color',
                      widget: None | Gtk.Widget=None,
                      on_error: str='#000000') -> tuple[bool, Gdk.RGBA]:
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


def treeselection_get_first_cell(gtk_selection: Gtk.TreeSelection,
                                 column: int=0) -> Any:
    """This function will return the first value of the column, or none if there are no rows"""
    liststore, treepaths = gtk_selection.get_selected_rows()

    if not treepaths:
        return None

    return liststore[treepaths[0]][column]


def dialog_select_directory(parent: None | Gtk.Widget,
                            start_path=None | str) -> None | str:
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


def dialog_select_file(parent: None | Gtk.Widget,
                       file_filter: None | Gtk.FileFilter = None,
                       start_path: None | str =None) -> None | str:
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


def dialog_yes_no(parent: None | Gtk.Widget,
                  text1: str,
                  text2: None | str =None) -> bool:
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


def dialog_info(parent: None | Gtk.Widget,
                text1: str,
                text2: None | str=None) -> None:
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


def window_is_fullscreen(gtk_window: Gtk.Window) -> bool:
    root_window = gtk_window.get_window()

    if root_window is None:
        return False

    elif Gdk.WindowState.FULLSCREEN & root_window.get_state():
        return True

    return False

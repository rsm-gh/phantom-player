#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2024 Rafael Senties Martinelli.
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
from gi.repository import Gtk

from Texts import Texts
from controller.playlist_factory import _COLUMN_SEPARATOR
from controller.playlist_factory import save as save_playlist
from console_printer import print_error


class DialogRenameSingle:

    def __init__(self, parent, update_func=None):
        self.__video = None
        self.__playlist = None
        self.__update_func = update_func

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), "single-rename.glade"))

        self.__dialog_rename = builder.get_object('dialog_rename')
        self.__switch_hardrive = builder.get_object('switch_hardrive')
        self.__entry_name = builder.get_object('entry_name')
        self.__entry_extension = builder.get_object('entry_extension')
        self.__label_harddrive = builder.get_object('label_harddrive')

        button_apply = builder.get_object('button_apply')
        button_cancel = builder.get_object('button_cancel')

        button_apply.connect('clicked', self.__on_button_apply)
        button_cancel.connect('clicked', self.__on_button_cancel)
        self.__switch_hardrive.connect('notify::active', self.__on_switch_notify_active)

        self.__dialog_rename.set_transient_for(parent)
        self.__dialog_rename.set_modal(True)
        self.__dialog_rename.set_title(Texts.DialogRenameSingle._title)
        self.__update_switch_label()

    def show(self, video, playlist):
        self.__video = video
        self.__playlist = playlist

        if not os.path.exists(video.get_path()):
            self.__switch_hardrive.set_active(False)
            self.__switch_hardrive.set_sensitive(False)
        else:
            self.__switch_hardrive.set_sensitive(True)
        self.__entry_name.set_text(video.get_name())

        extension = video.get_extension()
        if extension != "":
            extension = "." + extension
        self.__entry_extension.set_text(extension)
        self.__dialog_rename.show()
        self.__entry_name.grab_focus()

    def __update_switch_label(self):
        if self.__switch_hardrive.get_active():
            self.__label_harddrive.set_text(Texts.DialogRenameSingle._hdrive_on)
        else:
            self.__label_harddrive.set_text(Texts.DialogRenameSingle._hdrive_off)

    def __on_button_apply(self, *_):

        modify_hdrive = self.__switch_hardrive.get_active()
        current_path = self.__video.get_path()

        new_name = self.__entry_name.get_text().strip()
        if new_name == "":
            return

        elif _COLUMN_SEPARATOR in new_name:
            print_error(f"_COLUMN_SEPARATOR in new name {new_name}")
            return

        elif new_name == self.__video.get_name() and not modify_hdrive:
            # If the file name is the same, but different in the hdrive (the user just changed the option).
            # the code should not quit here.
            self.__dialog_rename.hide()
            return

        full_name = new_name
        extension = self.__video.get_extension()
        if extension != "":
            full_name = full_name + "." + extension

        new_path = os.path.join(os.path.dirname(current_path), full_name)

        if self.__switch_hardrive.get_active() and new_path != current_path:

            if os.path.exists(new_path):
                print_error(f"already existent path {new_path}")
                return

            try:
                os.rename(current_path, new_path)
            except Exception as e:
                print_error(str(e))
                return

            self.__video.set_path(new_path)

        self.__video.set_name(new_name)

        save_playlist(self.__playlist)

        if self.__update_func is not None:
            self.__update_func(self.__video)

        self.__dialog_rename.hide()

    def __on_button_cancel(self, *_):
        self.__dialog_rename.hide()

    def __on_switch_notify_active(self, *_):
        self.__update_switch_label()

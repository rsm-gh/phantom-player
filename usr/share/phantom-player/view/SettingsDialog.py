#!/usr/bin/python3
#

#  Copyright (C) 2024 Rafael Senties Martinelli.
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

import os
import gi
import sys

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GObject, GLib
from gi.repository.GdkPixbuf import Pixbuf

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from Paths import *
from Texts import Texts
from view import gtk_utils
from controller import factory


class ResponseType:
    delete = 0
    restart = 1
    close = 2
    add = 3


class SettingsDialog:

    def __init__(self, parent):

        self.__is_new_playlist = False
        self.__playlist = None
        self.__populating_settings = False
        self.__playlist_names = []

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "settings-dialog.glade"))
        builder.connect_signals(self)

        glade_ids = (
            'settings_dialog',
            'entry_playlist_name',
            'image_playlist',
            'switch_setting_keep_playing',
            'switch_setting_random_playing',
            'spinbutton_subtitles',
            'spinbutton_start_at',
            'spinbutton_audio',
            'button_playlist_delete',
            'button_playlist_restart',
            'button_playlist_add',
            'liststore_paths',
            'button_playlist_path_add',
            'button_playlist_path_remove',
            'button_playlist_path_edit',
            'button_playlist_path_reload_all',
        )

        for glade_id in glade_ids:
            setattr(self, glade_id, builder.get_object(glade_id))

        self.settings_dialog.set_transient_for(parent)

    def run(self, playlist, is_new, playlist_names=None):

        self.liststore_paths.clear()

        if playlist_names is None:
            self.__playlist_names = []
        else:
            self.__playlist_names = playlist_names

        if is_new:
            window_title = Texts.WindowSettings.new_title
            self.button_playlist_add.show()
        else:
            window_title = playlist.get_name() + " " + Texts.WindowSettings.edit_title
            self.button_playlist_add.hide()
            self.liststore_paths.append([playlist.get_data_path(), playlist.get_recursive()])

        self.settings_dialog.set_title(window_title)

        self.button_playlist_path_add.set_sensitive(is_new)
        self.button_playlist_path_remove.set_sensitive(False)
        self.button_playlist_path_edit.set_sensitive(not is_new)
        self.button_playlist_path_reload_all.set_sensitive(not is_new)

        self.entry_playlist_name.set_text(playlist.get_name())
        self.switch_setting_keep_playing.set_active(playlist.get_keep_playing())
        self.switch_setting_random_playing.set_active(playlist.get_random())

        pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(), -1, 30)
        self.image_playlist.set_from_pixbuf(pixbuf)
        self.button_playlist_delete.set_sensitive(not is_new)
        self.button_playlist_restart.set_sensitive(not is_new)

        self.__populating_settings = True
        self.spinbutton_audio.set_value(playlist.get_audio_track())
        self.spinbutton_subtitles.set_value(playlist.get_subtitles_track())
        self.spinbutton_start_at.set_value(playlist.get_start_at())
        self.__populating_settings = False

        self.__playlist = playlist
        self.__is_new_playlist = is_new

        response = self.settings_dialog.run()

        if response != ResponseType.delete:
            playlist.set_name(self.entry_playlist_name.get_text())

        self.settings_dialog.hide()
        return response

    def on_switch_setting_keep_playing_button_press_event(self, widget, *_):
        status = not widget.get_active()
        self.__playlist.set_keep_playing(status)

    def on_switch_setting_random_playing_button_press_event(self, widget, *_):
        status = not widget.get_active()
        self.__playlist.set_random(status)

    def on_spinbutton_audio_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__playlist.set_audio_track(value)

    def on_spinbutton_subtitles_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__playlist.set_subtitles_track(value)

    def on_spinbutton_start_at_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = float(spinbutton.get_value())

        str_value = str(value).split('.')
        minutes = int(str_value[0])
        seconds = int(str_value[1])
        if seconds > 60:
            minutes += 1
            spinbutton.set_value(minutes + 0.00)

        self.__playlist.set_start_at(value)

    def on_cellrenderertoggle_playlist_recursive_toggled(self, _, row):
        state = not self.liststore_paths[row][1]
        self.liststore_paths[row][1] = state
        self.__playlist.set_recursive(state)

    def on_button_playlist_delete_clicked(self, *_):
        if gtk_utils.dialog_yes_no(self.settings_dialog,
                                   Texts.DialogPlaylist.confirm_delete.format(self.__playlist.get_name())):
            self.settings_dialog.response(ResponseType.delete)

    def on_button_playlist_add_clicked(self, *_):

        playlist_name = self.entry_playlist_name.get_text().strip()

        if playlist_name == "":
            gtk_utils.dialog_info(self.settings_dialog, Texts.WindowSettings.playlist_name_empty)
            return

        elif playlist_name in self.__playlist_names:
            gtk_utils.dialog_info(self.settings_dialog,
                                  Texts.DialogPlaylist.name_exist.format(playlist_name))
            return

        self.__playlist.set_name(playlist_name)

        self.settings_dialog.response(ResponseType.add)

    def on_button_playlist_close(self, *_):

        if not self.__is_new_playlist:

            new_name = self.entry_playlist_name.get_text().strip()

            if self.__playlist.get_name() == new_name:
                pass

            elif new_name == "":
                gtk_utils.dialog_info(self.settings_dialog, Texts.WindowSettings.playlist_name_empty)
                return

            elif new_name in self.__playlist_names:
                gtk_utils.dialog_info(self.settings_dialog,
                                      Texts.DialogPlaylist.name_exist.format(new_name))
                return

            else:
                self.__playlist.set_name(new_name)


        self.settings_dialog.response(ResponseType.close)

    def on_button_playlist_restart_clicked(self, *_):

        selected_playlist_name = self.__playlist.get_name()

        if gtk_utils.dialog_yes_no(self.settings_dialog,
                                   Texts.DialogPlaylist.confirm_reset.format(selected_playlist_name)):
            self.settings_dialog.response(ResponseType.restart)

    def on_button_playlist_set_image_clicked(self, *_):
        """
            Add a picture to a playlist
        """
        file_filter = Gtk.FileFilter()
        file_filter.set_name('Image')
        file_filter.add_pattern('*.jpeg')
        file_filter.add_pattern('*.jpg')
        file_filter.add_pattern('*.png')

        file = gtk_utils.dialog_select_file(self.settings_dialog, file_filter)
        if file is not None:
            self.__playlist.set_icon_path(file)
            pixbuf = Pixbuf.new_from_file_at_size(file, -1, 30)
            self.image_playlist.set_from_pixbuf(pixbuf)

    def on_button_playlist_path_add_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.settings_dialog)
        if path is None:
            return

        self.liststore_paths.clear()
        self.liststore_paths.append([path, False])

        self.button_playlist_path_add.set_sensitive(False)
        self.button_playlist_path_edit.set_sensitive(True)
        self.button_playlist_path_reload_all.set_sensitive(True)

        self.__playlist.set_path(path)
        factory.load_videos(self.__playlist)

        self.settings_dialog.response(ResponseType.add)

    def on_button_playlist_path_remove_clicked(self, *_):
        pass

    def on_button_playlist_path_edit_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.settings_dialog)
        if path is None:
            return

        self.liststore_paths.clear()
        self.liststore_paths.append([path, False])

        self.__playlist.set_path(path)
        factory.load_videos(self.__playlist)

    def on_button_playlist_path_reload_all_clicked(self, *_):
        factory.load_videos(self.__playlist)

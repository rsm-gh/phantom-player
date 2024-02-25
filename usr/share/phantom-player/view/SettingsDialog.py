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
        self.__icon_path = None

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "settings-dialog.glade"))
        builder.connect_signals(self)

        self.__settings_dialog = builder.get_object('settings_dialog')
        self.__entry_playlist_name = builder.get_object('entry_playlist_name')
        self.__image_playlist = builder.get_object('image_playlist')
        self.__switch_setting_keep_playing = builder.get_object('switch_setting_keep_playing')
        self.__switch_setting_random_playing = builder.get_object('switch_setting_random_playing')
        self.__spinbutton_subtitles = builder.get_object('spinbutton_subtitles')
        self.__spinbutton_start_at = builder.get_object('spinbutton_start_at')
        self.__spinbutton_audio = builder.get_object('spinbutton_audio')
        self.__liststore_paths = builder.get_object('liststore_paths')

        self.__button_path_add = builder.get_object('button_path_add')
        self.__button_path_remove = builder.get_object('button_path_remove')
        self.__button_path_edit = builder.get_object('button_path_edit')
        self.__button_path_reload_all = builder.get_object('button_path_reload_all')

        self.__button_delete = builder.get_object('button_delete')
        self.__button_restart = builder.get_object('button_restart')
        self.__button_add = builder.get_object('button_add')

        self.__settings_dialog.set_transient_for(parent)

    def run(self, playlist, is_new, playlist_names=None):

        self.__liststore_paths.clear()
        self.__icon_path = None

        if playlist_names is None:
            self.__playlist_names = []
        else:
            self.__playlist_names = playlist_names

        self.__button_path_add.set_sensitive(True)

        if is_new:
            window_title = Texts.WindowSettings.new_title
            self.__button_add.show()
        else:
            window_title = playlist.get_name() + " " + Texts.WindowSettings.edit_title
            self.__button_add.hide()

            data_path = playlist.get_data_path()
            if data_path != "":
                self.__button_path_add.set_sensitive(False)
                self.__liststore_paths.append([playlist.get_data_path(), playlist.get_recursive()])

        self.__settings_dialog.set_title(window_title)


        self.__button_path_remove.set_sensitive(False)
        self.__button_path_edit.set_sensitive(not is_new)
        self.__button_path_reload_all.set_sensitive(not is_new)

        self.__entry_playlist_name.set_text(playlist.get_name())
        self.__switch_setting_keep_playing.set_active(playlist.get_keep_playing())
        self.__switch_setting_random_playing.set_active(playlist.get_random())

        pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(), -1, 30)
        self.__image_playlist.set_from_pixbuf(pixbuf)
        self.__button_delete.set_sensitive(not is_new)
        self.__button_restart.set_sensitive(not is_new)

        self.__populating_settings = True
        self.__spinbutton_audio.set_value(playlist.get_audio_track())
        self.__spinbutton_subtitles.set_value(playlist.get_subtitles_track())
        self.__spinbutton_start_at.set_value(playlist.get_start_at())
        self.__populating_settings = False

        self.__playlist = playlist
        self.__is_new_playlist = is_new

        response = self.__settings_dialog.run()

        if response != ResponseType.delete:
            playlist.set_name(self.__entry_playlist_name.get_text())

            if is_new and response == ResponseType.close:
                pass

            elif self.__icon_path is not None:
                playlist.set_icon_path(self.__icon_path)

        self.__settings_dialog.hide()
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
        state = not self.__liststore_paths[row][1]
        self.__liststore_paths[row][1] = state
        self.__playlist.set_recursive(state)

    def on_button_delete_clicked(self, *_):
        if gtk_utils.dialog_yes_no(self.__settings_dialog,
                                   Texts.DialogPlaylist.confirm_delete.format(self.__playlist.get_name())):
            self.__settings_dialog.response(ResponseType.delete)

    def on_button_add_clicked(self, *_):

        playlist_name = self.__entry_playlist_name.get_text().strip()

        if playlist_name == "":
            gtk_utils.dialog_info(self.__settings_dialog, Texts.WindowSettings.playlist_name_empty)
            return

        elif playlist_name in self.__playlist_names:
            gtk_utils.dialog_info(self.__settings_dialog,
                                  Texts.DialogPlaylist.name_exist.format(playlist_name))
            return

        self.__playlist.set_name(playlist_name)

        self.__settings_dialog.response(ResponseType.add)

    def on_button_close(self, *_):

        if not self.__is_new_playlist:

            new_name = self.__entry_playlist_name.get_text().strip()

            if self.__playlist.get_name() == new_name:
                pass

            elif new_name == "":
                gtk_utils.dialog_info(self.__settings_dialog, Texts.WindowSettings.playlist_name_empty)
                return

            elif new_name in self.__playlist_names:
                gtk_utils.dialog_info(self.__settings_dialog,
                                      Texts.DialogPlaylist.name_exist.format(new_name))
                return

            else:
                self.__playlist.set_name(new_name)


        self.__settings_dialog.response(ResponseType.close)

    def on_button_restart_clicked(self, *_):

        selected_playlist_name = self.__playlist.get_name()

        if gtk_utils.dialog_yes_no(self.__settings_dialog,
                                   Texts.DialogPlaylist.confirm_reset.format(selected_playlist_name)):
            self.__settings_dialog.response(ResponseType.restart)

    def on_button_set_image_clicked(self, *_):
        """
            Add a picture to a playlist.
            Note: set_icon_path shall not be called here,
                   because the playlist must be named / renamed first.
        """
        file_filter = Gtk.FileFilter()
        file_filter.set_name('Image')
        file_filter.add_pattern('*.jpeg')
        file_filter.add_pattern('*.jpg')
        file_filter.add_pattern('*.png')

        file = gtk_utils.dialog_select_file(self.__settings_dialog, file_filter)
        if file is not None:
            self.__icon_path = file
            pixbuf = Pixbuf.new_from_file_at_size(file, -1, 30)
            self.__image_playlist.set_from_pixbuf(pixbuf)

    def on_button_path_add_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.__settings_dialog)
        if path is None:
            return

        self.__liststore_paths.clear()
        self.__liststore_paths.append([path, False])

        self.__button_path_add.set_sensitive(False)
        self.__button_path_edit.set_sensitive(True)
        self.__button_path_reload_all.set_sensitive(True)

        self.__playlist.set_data_path(path)
        factory.load_videos(self.__playlist)

    def on_button_path_remove_clicked(self, *_):
        pass

    def on_button_path_edit_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.__settings_dialog)
        if path is None:
            return

        self.__liststore_paths.clear()
        self.__liststore_paths.append([path, False])

        self.__playlist.set_data_path(path)
        factory.load_videos(self.__playlist)

    def on_button_path_reload_all_clicked(self, *_):
        factory.load_videos(self.__playlist)

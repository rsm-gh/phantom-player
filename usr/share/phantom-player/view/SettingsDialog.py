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
import sys
from threading import Thread
from gi.repository import Gtk, GLib, Gdk
from gi.repository.GdkPixbuf import Pixbuf

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(_SCRIPT_DIR))

from Paths import *
from Texts import Texts
from model.PlaylistPath import PlaylistPath
from view import gtk_utils
from view.common import _FONT_DEFAULT_COLOR, _FONT_ERROR_COLOR
from controller import video_factory


class ResponseType:
    _delete = 0
    _restart = 1
    _close = 2
    _add = 3


class PathsListstoreColumns:
    _path = 0
    _recursive = 1
    _r_startup = 2


class SettingsDialog:

    def __init__(self, parent):

        self.__parent = parent
        self.__is_new_playlist = False
        self.__playlist = None
        self.__populating_settings = False
        self.__playlist_names = []
        self.__icon_path = None
        self.__selected_path = None
        self.__edit_path_new_value = None

        #
        # Get the GTK objects
        #
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "settings-dialog.glade"))

        self.__settings_dialog = builder.get_object('settings_dialog')
        self.__entry_playlist_name = builder.get_object('entry_playlist_name')
        self.__image_playlist = builder.get_object('image_playlist')
        self.__switch_keep_playing = builder.get_object('switch_keep_playing')
        self.__switch_random_playing = builder.get_object('switch_random_playing')
        self.__spinbutton_audio = builder.get_object('spinbutton_audio')
        self.__spinbutton_subtitles = builder.get_object('spinbutton_subtitles')
        self.__spinbutton_start_at_min = builder.get_object('spinbutton_start_at_min')
        self.__spinbutton_start_at_sec = builder.get_object('spinbutton_start_at_sec')

        self.__liststore_paths = builder.get_object('liststore_paths')
        self.__button_set_image = builder.get_object('button_set_image')

        self.__treeselection_path = builder.get_object('treeselection_path')
        self.__button_path_add = builder.get_object('button_path_add')
        self.__button_path_remove = builder.get_object('button_path_remove')
        self.__button_path_edit = builder.get_object('button_path_edit')
        self.__button_path_reload_all = builder.get_object('button_path_reload_all')
        self.__cellrenderertoggle_recursive = builder.get_object('cellrenderertoggle_recursive')
        self.__cellrenderertoggle_r_startup = builder.get_object('cellrenderertoggle_r_startup')

        self.__button_delete = builder.get_object('button_delete')
        self.__button_restart = builder.get_object('button_restart')
        self.__button_close = builder.get_object('button_close')
        self.__button_add = builder.get_object('button_add')

        # Edit path
        self.__dialog_edit = builder.get_object('dialog_edit')
        self.__liststore_edit_path = builder.get_object('liststore_edit_path')
        self.__on_button_edit_path_apply = builder.get_object('button_edit_path_apply')
        self.__on_button_edit_path_cancel = builder.get_object('button_edit_path_cancel')

        # Dialog paths
        self.__dialog_paths = builder.get_object('dialog_paths')
        self.__liststore_videos_path = builder.get_object('liststore_videos_path')
        self.__button_path_close = builder.get_object('button_path_close')
        self.__label_dialog_paths = builder.get_object('label_dialog_paths')

        #
        # Connect the signals (not done trough glade because they are private methods)
        #

        self.__button_set_image.connect('clicked', self.__on_button_set_image_clicked)
        self.__switch_keep_playing.connect('button-press-event', self.__on_switch_random_playing_press_event)
        self.__switch_random_playing.connect('button-press-event', self.__on_switch_random_playing_press_event)
        self.__spinbutton_audio.connect('value-changed', self.__on_spinbutton_audio_value_changed)
        self.__spinbutton_subtitles.connect('value-changed', self.__on_spinbutton_subtitles_value_changed)
        self.__spinbutton_start_at_min.connect('value-changed', self.__on_spinbutton_start_at_value_changed)
        self.__spinbutton_start_at_sec.connect('value-changed', self.__on_spinbutton_start_at_value_changed)

        self.__treeselection_path.connect('changed', self.__on_treeselection_path_changed)
        self.__button_path_add.connect('clicked', self.__on_button_path_add_clicked)
        self.__button_path_remove.connect('clicked', self.__on_button_path_remove_clicked)
        self.__button_path_edit.connect('clicked', self.__on_button_path_edit_clicked)
        self.__button_path_reload_all.connect('clicked', self.__on_button_path_reload_all_clicked)
        self.__cellrenderertoggle_recursive.connect('toggled', self.__on_cellrenderertoggle_recursive_toggled)
        self.__cellrenderertoggle_r_startup.connect('toggled', self.__on_cellrenderertoggle_r_startup_toggled)

        self.__button_delete.connect('clicked', self.__on_button_delete_clicked)
        self.__button_restart.connect('clicked', self.__on_button_restart_clicked)
        self.__button_close.connect('clicked', self.__on_button_close_clicked)
        self.__button_add.connect('clicked', self.__on_button_add_clicked)

        # Edit path
        self.__on_button_edit_path_cancel.connect('clicked', self.__on_button_edit_path_cancel_clicked)
        self.__on_button_edit_path_apply.connect('clicked', self.__on_button_edit_path_apply_clicked)

        # Paths
        self.__button_path_close.connect('clicked', self.__on_button_path_close)

        #
        # Extra
        #

        self.__settings_dialog.set_transient_for(parent)

    def run(self, playlist, is_new, playlist_names=None):

        self.__treeselection_path.unselect_all()
        self.__liststore_paths.clear()
        self.__icon_path = None

        if playlist_names is None:
            self.__playlist_names = []
        else:
            self.__playlist_names = playlist_names

        if is_new:
            window_title = Texts.WindowSettings.new_title
            self.__button_add.show()
        else:
            window_title = playlist.get_name() + " " + Texts.WindowSettings.edit_title
            self.__button_add.hide()

            for playlist_path in playlist.get_playlist_paths():
                self.__liststore_paths.append([playlist_path.get_path(),
                                               playlist_path.get_recursive(),
                                               playlist_path.get_startup_discover()])

        self.__settings_dialog.set_title(window_title)
        self.__button_path_reload_all.set_sensitive(not is_new)

        self.__entry_playlist_name.set_text(playlist.get_name())
        self.__switch_keep_playing.set_active(playlist.get_keep_playing())
        self.__switch_random_playing.set_active(playlist.get_random())

        pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(), -1, 30)
        self.__image_playlist.set_from_pixbuf(pixbuf)
        self.__button_delete.set_sensitive(not is_new)
        self.__button_restart.set_sensitive(not is_new)

        self.__populating_settings = True
        self.__spinbutton_audio.set_value(playlist.get_audio_track())
        self.__spinbutton_subtitles.set_value(playlist.get_subtitles_track())
        self.__spinbutton_start_at_min.set_value(playlist.get_start_at() // 60)
        self.__spinbutton_start_at_sec.set_value(playlist.get_start_at() % 60)
        self.__populating_settings = False

        self.__playlist = playlist
        self.__is_new_playlist = is_new

        response = self.__settings_dialog.run()

        if response != ResponseType._delete:
            playlist.set_name(self.__entry_playlist_name.get_text())

            if is_new and response == ResponseType._close:
                pass

            elif self.__icon_path is not None:
                playlist.set_icon_path(self.__icon_path)

        self.__settings_dialog.hide()
        return response

    def __liststore_videos_path_glib_add(self, path):
        self.__liststore_videos_path.append([path])

    def __liststore_videos_path_add(self, path):
        GLib.idle_add(self.__liststore_videos_path_glib_add, path)

    def __thread_discover_paths(self, playlist_path):
        video_factory.discover(self.__playlist,
                               [playlist_path],
                               add_func=self.__liststore_videos_path_add)
        self.__un_freeze_dialog()
        GLib.idle_add(self.__button_path_close.set_sensitive, True)

    def __thread_reload_paths(self):
        video_factory.load(self.__playlist, is_startup=False)
        self.__un_freeze_dialog()

    def __un_freeze_dialog(self):
        cursor = Gdk.Cursor.new_from_name(self.__parent.get_display(), 'default')
        GLib.idle_add(self.__parent.get_root_window().set_cursor, cursor)
        GLib.idle_add(self.__settings_dialog.set_sensitive, True)

    def __freeze_dialog(self):
        self.__settings_dialog.set_sensitive(False)
        self.__parent.get_root_window().set_cursor(
            Gdk.Cursor.new_from_name(self.__parent.get_display(), 'wait'))

    def __on_button_set_image_clicked(self, *_):
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

    def __on_switch_random_playing_press_event(self, widget, *_):
        status = not widget.get_active()
        self.__playlist.set_random(status)

    def __on_switch_keep_playing_press_event(self, widget, *_):
        status = not widget.get_active()
        self.__playlist.set_keep_playing(status)

    def __on_spinbutton_audio_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__playlist.set_audio_track(value)

    def __on_spinbutton_subtitles_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__playlist.set_subtitles_track(value)

    def __on_spinbutton_start_at_value_changed(self, *_):

        if self.__populating_settings:
            return

        minutes = self.__spinbutton_start_at_min.get_value()
        seconds = self.__spinbutton_start_at_sec.get_value()

        self.__playlist.set_start_at(minutes * 60 + seconds)

    def __on_treeselection_path_changed(self, treeselection):
        if treeselection.count_selected_rows() <= 0:
            selection = False
            self.__selected_path = None
        else:
            selection = True
            path = gtk_utils.treeselection_get_first_cell(treeselection, PathsListstoreColumns._path)
            if self.__playlist is None:
                self.__selected_path = None
            else:
                self.__selected_path = self.__playlist.get_playlist_path(path)

        self.__button_path_remove.set_sensitive(selection)
        self.__button_path_edit.set_sensitive(selection)

    def __on_button_path_close(self, *_):
        self.__liststore_videos_path.clear() # to free memory
        self.__dialog_paths.hide()

    def __on_button_path_add_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.__settings_dialog)
        if path is None:
            return

        playlist_path = PlaylistPath(path, recursive=False, startup_discover=False)
        added = self.__playlist.add_playlist_path(playlist_path)

        if not added:
            return

        self.__button_path_reload_all.set_sensitive(True)
        self.__freeze_dialog()

        self.__liststore_paths.append([playlist_path.get_path(),
                                       playlist_path.get_recursive(),
                                       playlist_path.get_startup_discover()])

        self.__label_dialog_paths.set_text(Texts.WindowSettings.importing_videos)
        self.__liststore_videos_path.clear()
        self.__dialog_paths.show()
        self.__button_path_close.set_sensitive(False)

        Thread(target=self.__thread_discover_paths, args=[playlist_path]).start()

    def __on_button_path_remove_clicked(self, *_):
        pass

    def __on_button_path_edit_clicked(self, *_):

        self.__edit_path_new_value = gtk_utils.dialog_select_directory(self.__settings_dialog)
        if self.__edit_path_new_value is None:
            return

        self.__liststore_edit_path.clear()

        current_path = self.__selected_path.get_path()

        for video in self.__playlist.get_linked_videos(current_path):

            old_video_path = video.get_path()

            # Append to current paths
            if os.path.exists(old_video_path):
                old_font = _FONT_DEFAULT_COLOR
            else:
                old_font = _FONT_ERROR_COLOR

            # Append to new paths
            new_video_path = old_video_path.replace(current_path, self.__edit_path_new_value, 1)
            if os.path.exists(new_video_path):
                new_font = _FONT_DEFAULT_COLOR
            else:
                new_font = _FONT_ERROR_COLOR

            self.__liststore_edit_path.append([old_font,
                                               new_font,
                                               old_video_path,
                                               new_video_path])

        self.__dialog_edit.show()

    def __on_button_path_reload_all_clicked(self, *_):
        self.__freeze_dialog()
        Thread(target=self.__thread_reload_paths).start()

    def __on_button_edit_path_apply_clicked(self, *_):

        self.__liststore_edit_path.clear()  # To free memory

        current_path = self.__selected_path.get_path()

        for video in self.__playlist.get_linked_videos(current_path):
            new_path = video.get_path().replace(current_path, self.__edit_path_new_value, 1)
            video.set_path(new_path)

        # Update the path liststore
        for i, row in enumerate(self.__liststore_paths):
            if row[PathsListstoreColumns._path] == current_path:
                self.__liststore_paths[i][PathsListstoreColumns._path] = self.__edit_path_new_value
                break

        self.__selected_path.set_path(self.__edit_path_new_value)

        self.__dialog_edit.hide()

    def __on_button_edit_path_cancel_clicked(self, *_):
        self.__edit_path_new_value = None
        self.__liststore_edit_path.clear()
        self.__dialog_edit.hide()

    def __on_cellrenderertoggle_recursive_toggled(self, _, row):
        """
            This method can be called even if there is no item selected in the liststore.
        """
        path = self.__liststore_paths[row][PathsListstoreColumns._path]
        state = not self.__liststore_paths[row][PathsListstoreColumns._recursive]
        self.__liststore_paths[row][PathsListstoreColumns._recursive] = state

        playlist_path = self.__playlist.get_playlist_path(path)
        if playlist_path is not None:
            playlist_path.set_recursive(state)

    def __on_cellrenderertoggle_r_startup_toggled(self, _, row):
        """
            This method can be called even if there is no item selected in the liststore.
        """
        path = self.__liststore_paths[row][PathsListstoreColumns._path]
        state = not self.__liststore_paths[row][PathsListstoreColumns._r_startup]
        self.__liststore_paths[row][PathsListstoreColumns._r_startup] = state

        playlist_path = self.__playlist.get_playlist_path(path)
        if playlist_path is not None:
            playlist_path.set_startup_discover(state)

    def __on_button_delete_clicked(self, *_):
        if gtk_utils.dialog_yes_no(self.__settings_dialog,
                                   Texts.DialogPlaylist.confirm_delete.format(self.__playlist.get_name())):
            self.__settings_dialog.response(ResponseType._delete)

    def __on_button_close_clicked(self, *_):

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

        self.__settings_dialog.response(ResponseType._close)

    def __on_button_restart_clicked(self, *_):

        selected_playlist_name = self.__playlist.get_name()

        if gtk_utils.dialog_yes_no(self.__settings_dialog,
                                   Texts.DialogPlaylist.confirm_reset.format(selected_playlist_name)):
            self.__settings_dialog.response(ResponseType._restart)

    def __on_button_add_clicked(self, *_):

        playlist_name = self.__entry_playlist_name.get_text().strip()

        if playlist_name == "":
            gtk_utils.dialog_info(self.__settings_dialog, Texts.WindowSettings.playlist_name_empty)
            return

        elif playlist_name in self.__playlist_names:
            gtk_utils.dialog_info(self.__settings_dialog,
                                  Texts.DialogPlaylist.name_exist.format(playlist_name))
            return

        self.__playlist.set_name(playlist_name)

        self.__settings_dialog.response(ResponseType._add)

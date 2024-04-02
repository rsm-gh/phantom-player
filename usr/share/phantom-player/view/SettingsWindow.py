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

class PathsListstoreColumns:
    _path = 0
    _recursive = 1
    _r_startup = 2
    _active = 3
    _ignored = 4
    _missing = 5


class SettingsWindow:

    def __init__(self,
                 parent,
                 playlists,
                 add_function,
                 delete_function,
                 restart_function,
                 close_function):

        self.__parent = parent
        self.__is_new_playlist = False
        self.__populating_settings = False
        self.__playlists = playlists
        self.__current_playlist = None
        self.__icon_path = None
        self.__selected_path = None
        self.__edit_path_new_value = None

        self.__add_function = add_function
        self.__delete_function = delete_function
        self.__restart_function = restart_function
        self.__close_function = close_function

        #
        # Get the GTK objects
        #
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "settings-window.glade"))

        self.__notebook = builder.get_object('notebook')
        self.__button_previous_playlist = builder.get_object('button_previous_playlist')
        self.__button_next_playlist = builder.get_object('button_next_playlist')
        self.__settings_window = builder.get_object('settings_window')
        self.__entry_playlist_name = builder.get_object('entry_playlist_name')
        self.__togglebutton_edit_name = builder.get_object('togglebutton_edit_name')
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
        self.__button_edit_path_apply = builder.get_object('button_edit_path_apply')
        self.__button_edit_path_cancel = builder.get_object('button_edit_path_cancel')

        # Dialog paths
        self.__dialog_paths = builder.get_object('dialog_paths')
        self.__liststore_videos_path = builder.get_object('liststore_videos_path')
        self.__treeselection_videos_path = builder.get_object('treeselection_videos_path')
        self.__button_path_close = builder.get_object('button_path_close')
        self.__label_dialog_paths = builder.get_object('label_dialog_paths')

        #
        # Connect the signals (not done trough glade because they are private methods)
        #
        self.__button_previous_playlist.connect('clicked', self.__on_button_previous_playlist)
        self.__button_next_playlist.connect('clicked', self.__on_button_next_playlist)

        self.__entry_playlist_name.connect('changed', self.__on_entry_playlist_name_changed)
        self.__togglebutton_edit_name.connect('button-press-event', self.__on_togglebutton_edit_name_press_event)
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
        self.__button_edit_path_cancel.connect('clicked', self.__on_button_edit_path_cancel_clicked)
        self.__button_edit_path_apply.connect('clicked', self.__on_button_edit_path_apply_clicked)

        # Paths
        self.__button_path_close.connect('clicked', self.__on_button_path_close)

        #
        # Extra
        #

        self.__settings_window.set_transient_for(parent)

    def show(self, playlist, is_new):

        self.__current_playlist = playlist
        self.__is_new_playlist = is_new
        self.__load_playlist()

        if is_new:
            self.__settings_window.set_title("Playlist Settings")

        self.__settings_window.show()

    def __save_playlist_changes(self):
        new_name = self.__entry_playlist_name.get_text().strip()

        if self.__current_playlist.get_name() == new_name:
            pass

        elif new_name == "":
            gtk_utils.dialog_info(self.__settings_window, Texts.WindowSettings.playlist_name_empty)
            return

        elif new_name in [playlist.get_name().lower() for playlist in self.__playlists.values()]:
            gtk_utils.dialog_info(self.__settings_window,
                                  Texts.DialogPlaylist.name_exist.format(new_name))
            return

        else:
            self.__current_playlist.set_name(new_name)

        if self.__icon_path is not None:
            self.__current_playlist.set_icon_path(self.__icon_path)

    def __get_previous_playlist(self):
        keys = list(self.__playlists.keys())
        prev_index = keys.index(self.__current_playlist.get_id()) - 1

        if prev_index < 0:
            return None

        try:
            prev_playlist_name = keys[prev_index]
        except IndexError:
            return None
        else:
            return self.__playlists[prev_playlist_name]

    def __get_next_playlist(self):
        keys = list(self.__playlists.keys())
        next_index = keys.index(self.__current_playlist.get_id()) + 1

        try:
            next_playlist_name = keys[next_index]
        except IndexError:
            return None
        else:
            return self.__playlists[next_playlist_name]

    def __load_playlist(self):

        if self.__is_new_playlist:
            self.__button_previous_playlist.set_sensitive(False)
            self.__button_next_playlist.set_sensitive(False)
            self.__notebook.set_current_page(0)
        else:
            self.__button_previous_playlist.set_sensitive(self.__get_previous_playlist() is not None)
            self.__button_next_playlist.set_sensitive(self.__get_next_playlist() is not None)

        self.__treeselection_path.unselect_all()
        self.__liststore_paths.clear()
        self.__icon_path = None

        if self.__is_new_playlist:
            self.__button_add.show()
            self.__togglebutton_edit_name.hide()
        else:
            self.__button_add.hide()
            self.__togglebutton_edit_name.show()

            for playlist_path in self.__current_playlist.get_playlist_paths():
                self.__liststore_paths_update_or_add(playlist_path)


        self.__togglebutton_edit_name.set_active(self.__is_new_playlist)

        self.__entry_playlist_name.set_sensitive(self.__is_new_playlist)
        self.__button_path_reload_all.set_sensitive(not self.__is_new_playlist)

        self.__entry_playlist_name.set_text(self.__current_playlist.get_name())
        self.__switch_keep_playing.set_active(self.__current_playlist.get_keep_playing())
        self.__switch_random_playing.set_active(self.__current_playlist.get_random())

        pixbuf = Pixbuf.new_from_file_at_size(self.__current_playlist.get_icon_path(), -1, 30)
        self.__image_playlist.set_from_pixbuf(pixbuf)
        self.__button_delete.set_sensitive(not self.__is_new_playlist)
        self.__button_restart.set_sensitive(not self.__is_new_playlist)

        self.__populating_settings = True
        self.__spinbutton_audio.set_value(self.__current_playlist.get_audio_track())
        self.__spinbutton_subtitles.set_value(self.__current_playlist.get_subtitles_track())
        self.__spinbutton_start_at_min.set_value(self.__current_playlist.get_start_at() // 60)
        self.__spinbutton_start_at_sec.set_value(self.__current_playlist.get_start_at() % 60)
        self.__populating_settings = False


    def __liststore_paths_update_or_add(self, playlist_path, liststore_path=None):

        if liststore_path is None:
            liststore_path = playlist_path.get_path()

        active, ignored, missing = self.__current_playlist.get_path_stats(playlist_path)

        for i, row in enumerate(self.__liststore_paths):
            if row[PathsListstoreColumns._path] == liststore_path:
                self.__liststore_paths[i][PathsListstoreColumns._path] = playlist_path.get_path()
                self.__liststore_paths[i][PathsListstoreColumns._recursive] = playlist_path.get_recursive()
                self.__liststore_paths[i][PathsListstoreColumns._r_startup] = playlist_path.get_startup_discover()
                self.__liststore_paths[i][PathsListstoreColumns._active] = active
                self.__liststore_paths[i][PathsListstoreColumns._ignored] = ignored
                self.__liststore_paths[i][PathsListstoreColumns._missing] = missing
                return

        self.__liststore_paths.append([playlist_path.get_path(),
                                       playlist_path.get_recursive(),
                                       playlist_path.get_startup_discover(),
                                       active,
                                       ignored,
                                       missing])



    def __liststore_videos_path_glib_add(self, path):
        self.__liststore_videos_path.append([path])

    def __liststore_videos_path_add_glib(self, _, video):
        GLib.idle_add(self.__liststore_videos_path_glib_add, video.get_path())

    def __thread_discover_paths(self, playlist_path, end_label, end_text):
        video_factory.discover(self.__current_playlist,
                               [playlist_path],
                               add_func=self.__liststore_videos_path_add_glib)
        GLib.idle_add(end_label.set_text, end_text)
        GLib.idle_add(self.__liststore_paths_update_or_add, playlist_path)
        self.__unfreeze_all()

    def __thread_reload_paths(self):
        video_factory.load(self.__current_playlist, is_startup=False)
        self.__unfreeze_all()

    def __unfreeze_all(self):
        """This method will be called inside a thread"""

        # Dialog paths
        GLib.idle_add(self.__button_path_close.set_sensitive, True)

        # Dialog edit
        GLib.idle_add(self.__button_edit_path_apply.set_sensitive, True)
        GLib.idle_add(self.__button_edit_path_cancel.set_sensitive, True)

        # Settings window
        GLib.idle_add(self.__settings_window.set_sensitive, True)

        # Root Window
        cursor = Gdk.Cursor.new_from_name(self.__parent.get_display(), 'default')
        GLib.idle_add(self.__parent.get_root_window().set_cursor, cursor)



    def __freeze_all(self):

        # Dialog paths
        self.__liststore_videos_path.clear()
        self.__button_path_close.set_sensitive(False)

        # Dialog edit
        self.__liststore_edit_path.clear()
        self.__button_edit_path_apply.set_sensitive(False)
        self.__button_edit_path_cancel.set_sensitive(False)

        # Settings window
        self.__settings_window.set_sensitive(False)

        # Root window
        cursor = Gdk.Cursor.new_from_name(self.__parent.get_display(), 'wait')
        self.__parent.get_root_window().set_cursor(cursor)

    def __on_button_previous_playlist(self, *_):
        self.__save_playlist_changes()
        self.__close_function(self.__current_playlist)
        self.__current_playlist = self.__get_previous_playlist()
        self.__load_playlist()

    def __on_button_next_playlist(self, *_):
        self.__save_playlist_changes()
        self.__close_function(self.__current_playlist)
        self.__current_playlist = self.__get_next_playlist()
        self.__load_playlist()


    def __on_entry_playlist_name_changed(self, *_):

        playlist_name = self.__entry_playlist_name.get_text().strip()

        if playlist_name == "":
            playlist_name = "Playlist Settings"

        self.__settings_window.set_title(playlist_name)

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

        file = gtk_utils.dialog_select_file(self.__settings_window, file_filter)
        if file is not None:
            self.__icon_path = file
            pixbuf = Pixbuf.new_from_file_at_size(file, -1, 30)
            self.__image_playlist.set_from_pixbuf(pixbuf)

    def __on_togglebutton_edit_name_press_event(self, widget, *_):
        status = not widget.get_active()
        self.__entry_playlist_name.set_sensitive(status)

    def __on_switch_random_playing_press_event(self, widget, *_):
        status = not widget.get_active()
        self.__current_playlist.set_random(status)

    def __on_switch_keep_playing_press_event(self, widget, *_):
        status = not widget.get_active()
        self.__current_playlist.set_keep_playing(status)

    def __on_spinbutton_audio_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__current_playlist.set_audio_track(value)

    def __on_spinbutton_subtitles_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__current_playlist.set_subtitles_track(value)

    def __on_spinbutton_start_at_value_changed(self, *_):

        if self.__populating_settings:
            return

        minutes = self.__spinbutton_start_at_min.get_value()
        seconds = self.__spinbutton_start_at_sec.get_value()

        self.__current_playlist.set_start_at(minutes * 60 + seconds)

    def __on_treeselection_path_changed(self, treeselection):
        if treeselection.count_selected_rows() <= 0:
            selection = False
            self.__selected_path = None
        else:
            selection = True
            path = gtk_utils.treeselection_get_first_cell(treeselection, PathsListstoreColumns._path)
            if self.__current_playlist is None:
                self.__selected_path = None
            else:
                self.__selected_path = self.__current_playlist.get_playlist_path(path)

        self.__button_path_remove.set_sensitive(selection)
        self.__button_path_edit.set_sensitive(selection)

    def __on_button_path_close(self, *_):
        self.__liststore_videos_path.clear()  # to free memory
        self.__dialog_paths.hide()

    def __on_button_path_add_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.__settings_window)
        if path is None:
            return

        playlist_path = PlaylistPath(path=path,
                                     recursive=False,
                                     startup_discover=False)
        added = self.__current_playlist.add_playlist_path(playlist_path)
        if not added:
            return

        self.__button_path_reload_all.set_sensitive(True)

        self.__dialog_paths.set_title(Texts.WindowSettings._add_path_title)
        self.__label_dialog_paths.set_text(Texts.WindowSettings._add_path_videos)
        self.__freeze_all()
        self.__dialog_paths.show()

        Thread(target=self.__thread_discover_paths, args=[playlist_path,
                                                          self.__label_dialog_paths,
                                                          Texts.WindowSettings._add_path_videos_done]).start()

    def __on_button_path_remove_clicked(self, *_):
        self.__dialog_paths.set_title(Texts.WindowSettings._remove_recursive_title)
        self.__label_dialog_paths.set_text(Texts.WindowSettings._remove_videos)
        self.__dialog_paths.show()
        removed_videos = self.__current_playlist.remove_playlist_path(self.__selected_path)
        for video in removed_videos:
            self.__liststore_videos_path.append([video.get_path()])
            gtk_utils.treeselection_remove_first_row(self.__treeselection_path)

    def __on_button_path_edit_clicked(self, *_):

        self.__edit_path_new_value = gtk_utils.dialog_select_directory(self.__settings_window)
        if self.__edit_path_new_value is None:
            return

        self.__liststore_edit_path.clear()

        current_path = self.__selected_path.get_path()

        for video in self.__current_playlist.get_linked_videos(current_path):

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
        self.__freeze_all()
        Thread(target=self.__thread_reload_paths).start()

    def __on_button_edit_path_apply_clicked(self, *_):

        self.__liststore_edit_path.clear()  # To free memory

        current_path = self.__selected_path.get_path()

        for video in self.__current_playlist.get_linked_videos(current_path):
            new_path = video.get_path().replace(current_path, self.__edit_path_new_value, 1)
            video.set_path(new_path)

        self.__selected_path.set_path(self.__edit_path_new_value)
        self.__liststore_paths_update_or_add(self.__selected_path, current_path)

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

        playlist_path = self.__current_playlist.get_playlist_path(path)
        playlist_path.set_recursive(state)

        self.__dialog_paths.show()

        if state:
            self.__freeze_all()
            self.__dialog_paths.set_title(Texts.WindowSettings._add_recursive_title)
            self.__label_dialog_paths.set_text(Texts.WindowSettings._adding_recursive_videos)
            Thread(target=self.__thread_discover_paths, args=[playlist_path,
                                                              self.__label_dialog_paths,
                                                              Texts.WindowSettings._adding_recursive_videos_done]).start()
        else:
            self.__dialog_paths.set_title(Texts.WindowSettings._remove_recursive_title)
            self.__label_dialog_paths.set_text(Texts.WindowSettings._remove_videos)
            removed_videos = self.__current_playlist.remove_playlist_path(playlist_path, only_recursive=True)
            for video in removed_videos:
                self.__liststore_videos_path.append([video.get_path()])

            self.__liststore_paths_update_or_add(playlist_path)


    def __on_cellrenderertoggle_r_startup_toggled(self, _, row):
        """
            This method can be called even if there is no item selected in the liststore.
        """
        path = self.__liststore_paths[row][PathsListstoreColumns._path]
        state = not self.__liststore_paths[row][PathsListstoreColumns._r_startup]
        self.__liststore_paths[row][PathsListstoreColumns._r_startup] = state

        playlist_path = self.__current_playlist.get_playlist_path(path)
        if playlist_path is not None:
            playlist_path.set_startup_discover(state)

    def __on_button_delete_clicked(self, *_):
        if gtk_utils.dialog_yes_no(self.__settings_window,
                                   Texts.DialogPlaylist.confirm_delete.format(self.__current_playlist.get_name())):
            self.__settings_window.hide()
            self.__delete_function(self.__current_playlist)

    def __on_button_close_clicked(self, *_):

        if self.__is_new_playlist:
            icon_path = self.__current_playlist.get_icon_path(allow_default=False)
            if icon_path is not None and os.path.exists(icon_path):
                os.remove(icon_path)

        else:
            self.__save_playlist_changes()

        self.__settings_window.hide()

        self.__close_function(self.__current_playlist)

    def __on_button_restart_clicked(self, *_):

        selected_playlist_name = self.__current_playlist.get_name()

        if gtk_utils.dialog_yes_no(self.__settings_window,
                                   Texts.DialogPlaylist.confirm_reset.format(selected_playlist_name)):
            self.__restart_function(self.__current_playlist)

    def __on_button_add_clicked(self, *_):

        playlist_name = self.__entry_playlist_name.get_text().strip()

        if playlist_name == "":
            gtk_utils.dialog_info(self.__settings_window, Texts.WindowSettings.playlist_name_empty)
            return

        elif playlist_name.lower() in [playlist.get_name().lower() for playlist in self.__playlists.values()]:
            gtk_utils.dialog_info(self.__settings_window,
                                  Texts.DialogPlaylist.name_exist.format(playlist_name))
            return

        self.__current_playlist.set_name(playlist_name)
        self.__settings_window.hide()
        self.__add_function(self.__current_playlist)

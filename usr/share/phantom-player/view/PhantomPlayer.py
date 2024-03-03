#!/usr/bin/python3
#

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli
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

"""
    + Fix: when searching in the playlist liststore, the videos shall be emptied.
    + Fix start at
    + Make the signals private
    + Manage multiple paths into the playlist settings menu.
    + Apply the "load video" methods of the settings dialog into a thread.
    + Create the option "end at"
    + Create the "delete video" option (instead of clean)
    + Create a dialog to rename videos.
    + Create a dialog to find videos?
"""

import os
import gi
import sys
from threading import Thread

os.environ["GDK_BACKEND"] = "x11"

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository.GdkPixbuf import Pixbuf

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from Paths import _SERIES_DIR, _CONF_FILE
from Texts import Texts
from view import gtk_utils
from controller.CCParser import CCParser
from controller import factory_video
from controller import factory_playlist
from model.Playlist import Playlist
from model.CurrentMedia import CurrentMedia
from system_utils import EventCodes, open_directory
from view.SettingsDialog import SettingsDialog
from view.SettingsDialog import ResponseType as SettingsDialogResponse
from view.MediaPlayer import MediaPlayerWidget, VLC_INSTANCE, CustomSignals

_DARK_CSS = """
@define-color theme_text_color white;
@define-color warning_color orange;
@define-color error_color red;
@define-color success_color green;

window, treeview, box, menu {
    background: #262626;
    color: white;
}"""


class PlaylistListstoreColumnsIndex:
    icon = 0
    name = 1
    percent = 2


class VideosListstoreColumnsIndex:
    color = 0
    id = 1
    path = 2
    name = 3
    ext = 4
    progress = 5


class GlobalConfigTags:
    checkbox_missing_playlist_warning = "missing-playlist-warning"
    checkbox_hidden_videos = "hidden-videos"
    checkbox_hide_missing_playlist = "hide-missing-playlist"


class PhantomPlayer:

    def __init__(self, application=None, dark_mode=False):

        self.__playlist_new = None
        self.__playlist_selected = None
        self.__playlists = {}
        self.__playlists_loaded = False

        self.__current_media = CurrentMedia()
        self.__is_full_screen = None
        self.__threads = []

        self.__configuration = CCParser(_CONF_FILE, 'phantom-player')

        #
        #   GTK style
        #

        if dark_mode:
            css_style = _DARK_CSS
        else:
            css_style = None

        _, self.__font_default_color = gtk_utils.get_default_color('theme_text_color',
                                                                   on_error="#000000")

        _, self.__font_hide_color = gtk_utils.get_default_color('warning_color',
                                                                on_error="#ff9900")

        _, self.__font_error_color = gtk_utils.get_default_color('error_color',
                                                                 on_error="#ff0000")

        _, self.__font_new_color = gtk_utils.get_default_color('success_color',
                                                               on_error="#009933")

        #
        #   GTK objects
        #
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "main-window.glade"))

        self.__window_root = builder.get_object('window_root')
        self.__window_about = builder.get_object('window_about')
        self.__menubar = builder.get_object('menubar')
        self.__menuitem_playlist = builder.get_object('menuitem_playlist')
        self.__menuitem_playlist_new = builder.get_object('menuitem_playlist_new')
        self.__menuitem_playlist_settings = builder.get_object('menuitem_playlist_settings')
        self.__menuitem_about = builder.get_object('menuitem_about')
        self.__main_paned = builder.get_object('main_paned')
        self.__treeview_videos = builder.get_object('treeview_videos')
        self.__treeview_playlist = builder.get_object('treeview_playlist')
        self.__treeselection_playlist = builder.get_object('treeselection_playlist')
        self.__treeselection_videos = builder.get_object('treeselection_videos')
        self.__checkbox_hidden_items = builder.get_object('checkbox_hidden_items')
        self.__checkbox_hide_ext = builder.get_object('checkbox_hide_ext')
        self.__checkbox_hide_number = builder.get_object('checkbox_hide_number')
        self.__checkbox_hide_path = builder.get_object('checkbox_hide_path')
        self.__checkbox_hide_name = builder.get_object('checkbox_hide_name')
        self.__checkbox_hide_extension = builder.get_object('checkbox_hide_extension')
        self.__checkbox_hide_progress = builder.get_object('checkbox_hide_progress')
        self.__checkbox_hide_warning_missing_playlist = builder.get_object('checkbox_hide_warning_missing_playlist')
        self.__checkbox_hide_missing_playlist = builder.get_object('checkbox_hide_missing_playlist')
        self.__column_number = builder.get_object('column_number')
        self.__column_path = builder.get_object('column_path')
        self.__column_name = builder.get_object('column_name')
        self.__column_extension = builder.get_object('column_extension')
        self.__column_progress = builder.get_object('column_progress')
        self.__liststore_playlist = builder.get_object('liststore_playlist')
        self.__liststore_videos = builder.get_object('liststore_videos')
        box_window = builder.get_object('box_window')

        #
        # GTK Binding
        #

        self.__window_root.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.__window_root.connect('delete-event', self.quit)
        self.__window_root.connect("configure-event", self.__on_window_root_configure_event)
        self.__window_root.connect("visibility_notify_event", self.__on_window_root_notify_event)
        self.__menuitem_playlist.connect("activate", self.__on_menuitem_playlist_activate)
        self.__menuitem_playlist_new.connect("activate", self.__on_menuitem_playlist_new_activate)
        self.__menuitem_playlist_settings.connect("activate", self.__on_menuitem_playlist_settings_activate)
        self.__menuitem_about.connect("activate", self.__on_menuitem_about_activate)
        self.__checkbox_hide_warning_missing_playlist.connect('toggled',
                                                              self.__on_checkbox_hide_warning_missing_playlist_toggled)
        self.__checkbox_hide_missing_playlist.connect('toggled', self.__on_checkbox_hide_missing_playlist_toggled)
        self.__checkbox_hidden_items.connect('toggled', self.__on_checkbox_hidden_items_toggled)
        self.__checkbox_hide_number.connect('toggled', self.__on_checkbox_hide_number_toggled)
        self.__checkbox_hide_path.connect('toggled', self.__on_checkbox_hide_path_toggled)
        self.__checkbox_hide_name.connect('toggled', self.__on_checkbox_hide_name_toggled)
        self.__checkbox_hide_extension.connect('toggled', self.__on_checkbox_hide_extension_toggled)
        self.__checkbox_hide_progress.connect('toggled', self.__on_checkbox_hide_progress_toggled)
        self.__treeview_playlist.connect('button-press-event', self.__on_treeview_playlist_press_event)
        self.__treeview_videos.connect('drag-end', self.__on_treeview_videos_drag_end)
        self.__treeview_videos.connect('button-press-event', self.__on_treeview_videos_press_event)
        self.__treeselection_playlist.connect('changed', self.__on_treeselection_playlist_changed)

        #
        #    Media Player
        #
        self.__media_player = MediaPlayerWidget(self.__window_root,
                                                random_button=True,
                                                keep_playing_button=True,
                                                css_style=css_style)

        self.__media_player.connect(CustomSignals.position_changed, self.__on_media_player_position_changed)
        self.__media_player.connect(CustomSignals.btn_keep_playing_toggled,
                                    self.__on_media_player_btn_keep_playing_toggled)
        self.__media_player.connect(CustomSignals.btn_random_toggled, self.__on_media_player_btn_random_toggled)
        self.__media_player.connect(CustomSignals.video_end, self.__on_media_player_video_end)

        self.__paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.__paned.add1(self.__media_player)
        box_window.remove(self.__main_paned)
        self.__paned.add2(self.__main_paned)
        box_window.pack_start(self.__paned, True, True, 0)

        #
        #    Configuration
        #
        if application is not None:
            self.__window_root.set_application(application)

        self.__settings_dialog = SettingsDialog(self.__window_root)

        self.__checkbox_hide_warning_missing_playlist.set_active(
            self.__configuration.get_bool(GlobalConfigTags.checkbox_missing_playlist_warning))
        self.__checkbox_hidden_items.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags.checkbox_hidden_videos, False))
        self.__checkbox_hide_missing_playlist.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags.checkbox_hide_missing_playlist, False))

        self.__checkbox_hide_number.set_active(self.__configuration.get_bool('hide_video_number'))
        self.__checkbox_hide_path.set_active(self.__configuration.get_bool('hide_video_path'))
        self.__checkbox_hide_name.set_active(self.__configuration.get_bool('hide_video_name'))
        self.__checkbox_hide_extension.set_active(self.__configuration.get_bool('hide_video_extension'))
        self.__checkbox_hide_progress.set_active(self.__configuration.get_bool('hide_video_progress'))

        #
        #    Display the window
        #
        self.__menubar.set_sensitive(False)
        self.__treeview_playlist.set_sensitive(False)
        self.__menuitem_playlist_settings.set_sensitive(False)

        if dark_mode:
            gtk_utils.set_css(self.__window_root, css_style)
            gtk_utils.set_css(self.__treeview_videos, css_style)

        self.__window_root.get_root_window().set_cursor(
            Gdk.Cursor.new_from_name(self.__window_root.get_display(), 'wait'))

        self.__window_root.maximize()
        self.__window_root.show_all()
        self.__media_player.hide_volume_label()

        #
        #    Load the existent playlist
        #
        th = Thread(target=self.__on_thread_load_playlists)
        th.start()
        self.__threads.append(th)

    def present(self):
        self.__window_root.present()


    def join(self):
        for th in self.__threads:
            th.join()

        self.__media_player.join()

    def save(self):
        if self.__playlists_loaded:
            for playlist in self.__playlists.values():
                playlist.save()

    def quit(self, *_):
        self.__media_player.quit()
        VLC_INSTANCE.release()

    def __get_video_color(self, video):
        if video.get_ignore():
            return self.__font_hide_color

        elif video.get_is_new():
            return self.__font_new_color

        elif not video.exists():
            return self.__font_error_color

        return self.__font_default_color

    def __set_video(self, video_id=None, play=True, replay=False, ignore_none=False):

        if self.__current_media.playlist is None:
            return

        if video_id is None:
            video = self.__current_media.get_next_video()
        else:
            video = self.__current_media.get_video(video_id)

        if video is None:
            if not ignore_none:
                gtk_utils.dialog_info(self.__window_root, Texts.DialogPlaylist.all_videos_played)

            self.__window_root.unfullscreen()
            return

        elif not os.path.exists(video.get_path()):
            gtk_utils.dialog_info(self.__window_root, Texts.DialogVideos.missing)
            return

        #
        # Play the video
        #

        position = video.get_position()
        if position >= .9999 and replay:
            position = 0

        self.__media_player.set_video(video.get_path(),
                                      position,
                                      self.__current_media.playlist.get_subtitles_track(),
                                      self.__current_media.playlist.get_audio_track(),
                                      self.__current_media.playlist.get_start_at(),
                                      play)

        if self.__media_player.get_random() != self.__current_media.playlist.get_random():
            self.__media_player.set_random(self.__current_media.playlist.get_random())

        if self.__media_player.get_keep_playing() != self.__current_media.playlist.get_keep_playing():
            self.__media_player.set_keep_playing(self.__current_media.playlist.get_keep_playing())

        self.__liststore_videos_select_current()

    def __playlist_find_videos(self, _, videos_id):

        if len(videos_id) == 1:  # if the user only selected one video to find...

            path = gtk_utils.dialog_select_file(self.__window_root)

            if path is None:
                return

            found_videos = self.__playlist_selected.find_video(videos_id[0], path)
            gtk_utils.dialog_info(self.__window_root, Texts.DialogVideos.other_found.format(found_videos), None)

        else:

            path = gtk_utils.dialog_select_directory(self.__window_root)

            if path is None:
                return

            found_videos = self.__playlist_selected.find_videos(path)
            gtk_utils.dialog_info(self.__window_root, Texts.DialogVideos.found_x.format(found_videos), None)

        if found_videos > 0:
            self.__liststore_videos_populate()

    def __liststore_playlist_set_progress(self, playlist_name, value):
        for i, row in enumerate(self.__liststore_playlist):
            if row[PlaylistListstoreColumnsIndex.name] == playlist_name:
                if row[PlaylistListstoreColumnsIndex.percent] != value:
                    self.__liststore_playlist[i][PlaylistListstoreColumnsIndex.percent] = value
                break

    def __liststore_playlist_append(self, data):
        """
            I do not understand why this must be a separate method.
            It is not possible to call directly: GLib.idle_add(self.__liststore_playlist.append, data)
        """
        self.__liststore_playlist.append(data)

    def __liststore_playlist_populate(self):

        # Populate
        #
        self.__liststore_playlist.clear()

        for name in sorted(self.__playlists.keys()):
            playlist = self.__playlists[name]

            if os.path.exists(playlist.get_data_path()) or not self.__checkbox_hide_missing_playlist.get_active():
                pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(), -1, 30)
                self.__liststore_playlist.append([pixbuf, playlist.get_name(), playlist.get_progress()])

        # Select the current playlist
        #
        current_playlist_name = self.__configuration.get_str('current_playlist')

        for i, row in enumerate(self.__liststore_playlist):
            if row[1] == current_playlist_name:
                self.__treeview_playlist.set_cursor(i)
                return

        self.__treeview_playlist.set_cursor(0)

    def __liststore_videos_populate(self):

        if self.__playlist_selected is None:
            return

        self.__liststore_videos.clear()
        self.__column_name.set_spacing(0)

        for video in self.__playlist_selected.get_videos():
            if not video.get_ignore() or not self.__checkbox_hidden_items.get_active():
                self.__liststore_videos.append([self.__get_video_color(video),
                                                video.get_id(),
                                                video.get_path(),
                                                video.get_name(),
                                                video.get_extension(),
                                                video.get_progress()])

    def __liststore_videos_select_current(self):
        """
            Select the current video from the videos liststore.
        """
        if not self.__current_media.is_playlist_name(self.__playlist_selected.get_name()):
            return

        video_id = self.__current_media.get_video_id()

        for i, row in enumerate(self.__liststore_videos):
            if row[VideosListstoreColumnsIndex.id] == video_id:
                self.__treeview_videos.set_cursor(i)
                break

    def __menu_playlist_display(self, event):

        menu = Gtk.Menu()

        menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemPlaylist.settings)
        menu.append(menuitem)
        menuitem.connect('activate', self.__on_menuitem_playlist_settings_activate)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

        return True

    def __on_thread_load_playlists(self):
        if os.path.exists(_SERIES_DIR):
            for file_name in sorted(os.listdir(_SERIES_DIR)):

                if not file_name.lower().endswith('.csv'):
                    continue

                new_playlist = factory_playlist.load_from_file(os.path.join(_SERIES_DIR, file_name))

                self.__playlists[new_playlist.get_name()] = new_playlist

                if os.path.exists(
                        new_playlist.get_data_path()) or not self.__checkbox_hide_missing_playlist.get_active():
                    pixbuf = Pixbuf.new_from_file_at_size(new_playlist.get_icon_path(), -1, 30)
                    GLib.idle_add(self.__liststore_playlist_append,
                                  (pixbuf,
                                   new_playlist.get_name(),
                                   new_playlist.get_progress()))

        #
        #   Select & Load the last playlist that was played
        #
        current_playlist_name = self.__configuration.get_str('current_playlist')

        try:
            playlist_data = self.__playlists[current_playlist_name]
        except KeyError:
            playlist_data = None
        else:
            factory_video.load(playlist_data)
            self.__current_media = CurrentMedia(playlist_data)

        playlist_found = False
        for i, row in enumerate(self.__liststore_playlist):
            if row[PlaylistListstoreColumnsIndex.name] == current_playlist_name:
                GLib.idle_add(self.__treeview_playlist.set_cursor, i)
                GLib.idle_add(self.__liststore_playlist_set_progress,
                              current_playlist_name,
                              playlist_data.get_progress())
                playlist_found = True
                break

        #
        #   Load the rest of the videos
        #
        for playlist in self.__playlists.values():
            if playlist_data is not None and playlist.get_name() == playlist_data.get_name():
                continue

            factory_video.load(playlist)

            GLib.idle_add(self.__liststore_playlist_set_progress,
                          playlist.get_name(),
                          playlist.get_progress())

        #
        #   Select a default playlist if none
        #
        if not playlist_found:
            GLib.idle_add(self.__treeview_playlist.set_cursor, 0)
            GLib.idle_add(self.__window_root.set_sensitive, True)

        #
        #   Enable the GUI
        #
        default_cursor = Gdk.Cursor.new_from_name(self.__window_root.get_display(), 'default')
        GLib.idle_add(self.__window_root.get_root_window().set_cursor, default_cursor)
        GLib.idle_add(self.__treeview_playlist.set_sensitive, True)
        GLib.idle_add(self.__menubar.set_sensitive, True)
        self.__playlists_loaded = True

    def __on_window_root_notify_event(self, *_):
        # Resize the VLC widget
        _, window_height = self.__window_root.get_size()
        self.__paned.set_position(window_height / 2)

    def __on_window_root_configure_event(self, *_):

        if Gdk.WindowState.FULLSCREEN & self.__window_root.get_window().get_state():
            fullscreen = True
        else:
            fullscreen = False

        if self.__is_full_screen != fullscreen:
            self.__is_full_screen = fullscreen

            if fullscreen:
                self.__menubar.hide()
                self.__main_paned.hide()
            else:
                self.__menubar.show()
                self.__main_paned.show()

    def __on_media_player_btn_random_toggled(self, _, state):
        self.__current_media.playlist.set_random(state)

    def __on_media_player_btn_keep_playing_toggled(self, _, state):
        self.__current_media.playlist.set_keep_playing(state)

    def __on_media_player_position_changed(self, _, position):
        """
            Only update the liststore if the progress is different
        """
        self.__current_media.set_video_position(position)
        selected_series_name = self.__playlist_selected.get_name()

        #
        # Update the GUI
        #
        if not self.__current_media.is_playlist_name(selected_series_name):
            return

        GLib.idle_add(self.__liststore_playlist_set_progress,
                      selected_series_name,
                      self.__current_media.playlist.get_progress())

        video_id = self.__current_media.get_video_id()
        for i, row in enumerate(self.__liststore_videos):
            if row[VideosListstoreColumnsIndex.id] == video_id:
                if row[VideosListstoreColumnsIndex.progress] != self.__current_media.get_video_progress():
                    self.__liststore_videos[i][
                        VideosListstoreColumnsIndex.progress] = self.__current_media.get_video_progress()
                break

    def __on_media_player_video_end(self, *_):
        if not self.__current_media.playlist.get_keep_playing():
            self.__media_player.pause()
            self.__window_root.unfullscreen()
            return

        self.__set_video()

    def __on_treeview_playlist_press_event(self, _, event, inside_treeview=True):
        """
            Important: this method is triggered before "selection_changes".
        """

        #
        # Select the current playlist
        #
        if self.__treeselection_playlist.count_selected_rows() <= 0:
            self.__playlist_selected = None
            return

        selected_playlist_name = gtk_utils.treeselection_get_first_cell(self.__treeselection_playlist, 1)
        self.__playlist_selected = self.__playlists[selected_playlist_name]

        #
        # Process the events
        #
        if event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == EventCodes.Cursor.left_click:

                if self.__media_player.is_nothing():
                    self.__set_video(play=False, ignore_none=True)

            elif event.button == EventCodes.Cursor.right_click:

                # Get the iter where the user is pointing
                path = self.__treeview_playlist.get_path_at_pos(event.x, event.y)

                if path is not None:
                    pointing_treepath = path[0]

                    # If the iter is not in the selected iters, remove the previous selection
                    model, treepaths = self.__treeselection_playlist.get_selected_rows()

                    if pointing_treepath not in treepaths and inside_treeview:
                        self.__treeselection_playlist.unselect_all()
                        self.__treeselection_playlist.select_path(pointing_treepath)

                    self.__menu_playlist_display(event)

        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == EventCodes.Cursor.left_click:

                # check if the liststore is empty
                if len(self.__liststore_videos) <= 0:
                    if not self.__checkbox_hide_warning_missing_playlist.get_active():
                        gtk_utils.dialog_info(self.__window_root, Texts.DialogPlaylist.is_missing)

                    return

                """
                    Check if the playlist is already selected and if a video is playing
                """
                if self.__current_media.is_playlist_name(selected_playlist_name):
                    if not self.__media_player.is_nothing():
                        if self.__media_player.is_paused():
                            self.__media_player.play()

                        return

                """
                    Play a video of the playlist
                """
                self.__configuration.write('current_playlist', selected_playlist_name)
                self.__current_media = CurrentMedia(self.__playlist_selected)
                self.__set_video()

    def __on_treeview_videos_drag_end(self, *_):

        # Get the new order
        new_order = [row[VideosListstoreColumnsIndex.id] for row in self.__liststore_videos]

        # Update the treeview
        for i, row in enumerate(self.__liststore_videos, 1):
            row[VideosListstoreColumnsIndex.id] = i

        # Update the CSV file
        self.__playlist_selected.reorder(new_order)
        self.__treeselection_videos.unselect_all()

    def __on_treeview_videos_press_event(self, _, event):
        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if len(treepaths) == 0:
            return

        selection_length = len(treepaths)

        if event.button == EventCodes.Cursor.left_click and \
                selection_length == 1 and \
                event.type == Gdk.EventType._2BUTTON_PRESS:

            """
                Play the video of the playlist
            """

            self.__configuration.write('current_playlist', self.__playlist_selected.get_name())
            video_id = self.__liststore_videos[treepaths[0]][VideosListstoreColumnsIndex.id]
            self.__current_media = CurrentMedia(self.__playlist_selected)
            self.__set_video(video_id)


        elif event.button == EventCodes.Cursor.right_click:

            # get the iter where the user is pointing
            try:
                pointing_treepath = self.__treeview_videos.get_path_at_pos(event.x, event.y)[0]
            except Exception:
                return

            # if the iter is not in the selected iters, remove the previous selection
            model, treepaths = self.__treeselection_videos.get_selected_rows()

            if pointing_treepath not in treepaths:
                self.__treeselection_videos.unselect_all()
                self.__treeselection_videos.select_path(pointing_treepath)

            menu = Gtk.Menu()

            # Fill progress
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.progress_fill)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_set_progress, 100)

            # Reset Progress
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.progress_reset)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_set_progress, 0)

            # Find videos
            selected_ids = [self.__liststore_videos[treepath][VideosListstoreColumnsIndex.id] for treepath in treepaths]
            if self.__playlist_selected.missing_videos(selected_ids):
                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.search)
                menuitem.connect('activate', self.__playlist_find_videos, selected_ids)
                menu.append(menuitem)

            # ignore videos
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.ignore)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_playlist_ignore_video)

            # don't ignore videos
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.dont_ignore)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_playlist_dont_ignore_video)

            # Open the containing folder (only if the user selected one video)
            if selection_length == 1:
                video_id = self.__liststore_videos[treepaths[0]][VideosListstoreColumnsIndex.id]
                video = self.__playlist_selected.get_video(video_id)

                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.open_dir)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_video_open_dir, video.get_path())

            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)

            return True

    def __on_treeselection_playlist_changed(self, treeselection):

        if treeselection.count_selected_rows() <= 0:
            self.__playlist_selected = None
            return

        selected_playlist_name = gtk_utils.treeselection_get_first_cell(treeselection, 1)

        # This is because "press event" is executed before, so it is not necessary to re-define this
        if self.__playlist_selected is None or selected_playlist_name != self.__playlist_selected.get_name():
            self.__playlist_selected = self.__playlists[selected_playlist_name]

        self.__liststore_videos_populate()
        self.__liststore_videos_select_current()

    def __on_menuitem_about_activate(self, *_):
        _ = self.__window_about.run()
        self.__window_about.hide()

    def __on_menuitem_playlist_activate(self, *_):
        model, treepaths = self.__treeselection_playlist.get_selected_rows()
        self.__menuitem_playlist_settings.set_sensitive(len(treepaths) > 0)

    def __on_menuitem_playlist_new_activate(self, *_):
        new_playlist = Playlist()
        response = self.__settings_dialog.run(new_playlist,
                                              is_new=True,
                                              playlist_names=self.__playlists.keys())

        if response == SettingsDialogResponse.close:
            # Delete the image (if saved)
            icon_path = new_playlist.get_icon_path(allow_default=False)
            if icon_path is not None and os.path.exists(icon_path):
                os.remove(icon_path)

        elif response == SettingsDialogResponse.add:
            playlist_name = new_playlist.get_name()
            self.__playlists[playlist_name] = new_playlist

            if os.path.exists(new_playlist.get_data_path()) or not self.__checkbox_hide_missing_playlist.get_active():
                pixbuf = Pixbuf.new_from_file_at_size(new_playlist.get_icon_path(), -1, 30)
                self.__liststore_playlist.append([pixbuf, playlist_name, new_playlist.get_progress()])

                for i, row in enumerate(self.__liststore_playlist):
                    if row[1] == playlist_name:
                        self.__treeview_playlist.set_cursor(i)
                        break

    def __on_menuitem_playlist_settings_activate(self, *_):

        response = self.__settings_dialog.run(self.__playlist_selected, is_new=False)
        playlist_name = self.__playlist_selected.get_name()

        if response == SettingsDialogResponse.delete:

            self.__playlists.pop(self.__playlist_selected.get_name())

            # Remove from the player (if necessary)
            if self.__current_media.is_playlist_name(playlist_name):
                self.__media_player.stop()
                self.__current_media = CurrentMedia()

            # Delete the image (if saved)
            icon_path = self.__playlist_selected.get_icon_path(allow_default=False)
            if icon_path is not None and os.path.exists(icon_path):
                os.remove(icon_path)

            if os.path.exists(self.__playlist_selected.get_save_path()):
                os.remove(self.__playlist_selected.get_save_path())

            gtk_utils.treeselection_remove_first_row(self.__treeselection_playlist)

            if len(self.__liststore_playlist) > 0:
                self.__treeview_playlist.set_cursor(0)
            else:
                self.__liststore_videos.clear()

            return

        #
        # In all the other cases
        #

        # Update the icon
        pixbuf = Pixbuf.new_from_file_at_size(self.__playlist_selected.get_icon_path(), -1, 30)
        gtk_utils.treeselection_set_first_cell(self.__treeselection_playlist,
                                               PlaylistListstoreColumnsIndex.icon,
                                               pixbuf)

        # Update the name
        old_name = gtk_utils.treeselection_get_first_cell(self.__treeselection_playlist,
                                                          PlaylistListstoreColumnsIndex.name)

        if self.__playlist_selected.get_name() != old_name:
            self.__playlists.pop(old_name)
            self.__playlists[self.__playlist_selected.get_name()] = self.__playlist_selected
            gtk_utils.treeselection_set_first_cell(self.__treeselection_playlist,
                                                   PlaylistListstoreColumnsIndex.name,
                                                   self.__playlist_selected.get_name())

        # Update the media player
        if self.__current_media.is_playlist_name(self.__playlist_selected.get_name()):
            self.__media_player.set_keep_playing(self.__playlist_selected.get_keep_playing())
            self.__media_player.set_random(self.__playlist_selected.get_random())

        if response == SettingsDialogResponse.restart:

            # This is done before to avoid updating the playlist data
            was_playing = False
            if self.__current_media.is_playlist_name(playlist_name):
                if self.__media_player.is_playing():
                    was_playing = True
                    self.__media_player.pause()

            self.__playlist_selected.restart()

            if was_playing:
                self.__set_video()

        self.__liststore_videos_populate()

    def __on_menuitem_set_progress(self, _, progress):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if len(treepaths) == 0:
            return

        for treepath in treepaths:
            self.__liststore_videos[treepath][VideosListstoreColumnsIndex.progress] = progress
            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex.id]
            video = self.__playlist_selected.get_video(video_id)
            if progress == 0:
                video.set_position(0)
            else:
                video.set_position(progress / 100)

        GLib.idle_add(self.__liststore_playlist_set_progress,
                      self.__playlist_selected.get_name(),
                      self.__playlist_selected.get_progress())

    def __on_menuitem_playlist_ignore_video(self, _):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        hide_row = self.__checkbox_hidden_items.get_active()

        for treepath in reversed(treepaths):
            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex.id]
            video = self.__playlist_selected.get_video(video_id)
            video.set_ignore(True)

            if hide_row:
                row_iter = model.get_iter(treepath)
                model.remove(row_iter)
            else:
                self.__liststore_videos[treepath][VideosListstoreColumnsIndex.color] = self.__font_hide_color

        self.__treeselection_videos.unselect_all()

    def __on_menuitem_playlist_dont_ignore_video(self, _):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        for treepath in treepaths:
            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex.id]
            video = self.__playlist_selected.get_video(video_id)
            video.set_ignore(False)
            self.__liststore_videos[treepath][VideosListstoreColumnsIndex.color] = self.__get_video_color(video)

        self.__treeselection_videos.unselect_all()

    @staticmethod
    def __on_menuitem_video_open_dir(_, path):
        if os.path.exists(path):
            open_directory(path)

    def __on_checkbox_hide_warning_missing_playlist_toggled(self, *_):
        self.__configuration.write(GlobalConfigTags.checkbox_missing_playlist_warning,
                                   self.__checkbox_hide_warning_missing_playlist.get_active())

    def __on_checkbox_hide_missing_playlist_toggled(self, checkbox, *_):
        self.__liststore_playlist_populate()
        self.__configuration.write(GlobalConfigTags.checkbox_hide_missing_playlist, checkbox.get_active())

    def __on_checkbox_hidden_items_toggled(self, *_):
        self.__configuration.write(GlobalConfigTags.checkbox_hidden_videos, self.__checkbox_hidden_items.get_active())
        self.__liststore_videos_populate()

    def __on_checkbox_hide_number_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_number.set_visible(not state)
        self.__configuration.write('hide_video_number', state)

    def __on_checkbox_hide_path_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_path.set_visible(not state)
        self.__configuration.write('hide_video_path', state)

    def __on_checkbox_hide_name_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_name.set_visible(not state)
        self.__configuration.write('hide_video_name', state)

    def __on_checkbox_hide_extension_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_extension.set_visible(not state)
        self.__configuration.write('hide_video_extension', state)

    def __on_checkbox_hide_progress_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_progress.set_visible(not state)
        self.__configuration.write('hide_video_progress', state)
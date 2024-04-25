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

import os
import gi
from time import sleep
from threading import Thread
from collections import OrderedDict

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository.GdkPixbuf import Pixbuf

import settings
from Texts import Texts
from view import gtk_utils
from Paths import _SERIES_DIR, _CONF_FILE
from system_utils import EventCodes, open_directory
from controller.CCParser import CCParser
from controller import video_factory
from controller import playlist_factory
from model.Playlist import Playlist
from model.CurrentMedia import CurrentMedia
from model.Video import VideoPosition, VideoProgress
from view.SettingsWindow import SettingsWindow
from view.MediaPlayerWidget import MediaPlayerWidget, VLC_INSTANCE, CustomSignals


class PlaylistListstoreColumnsIndex:
    _id = 0
    _icon = 1
    _name = 2
    _percent = 3


class VideosListstoreColumnsIndex:
    _color = 0
    _id = 1
    _path = 2
    _name = 3
    _ext = 4
    _progress = 5


class GlobalConfigTags:
    _main_section = "phantom-player"

    _checkbox_missing_playlist_warning = "missing-playlist-warning"
    _checkbox_hidden_videos = "hidden-videos"
    _checkbox_hide_missing_playlist = "hide-missing-playlist"
    _current_playlist = "current_playlist"
    _prefer_dark_theme = "prefer_dark_theme"

    _hide_video_number = 'hide_video_number'
    _hide_video_path = 'hide_video_path'
    _hide_video_name = 'hide_video_name'
    _hide_video_extension = 'hide_video_extension'
    _hide_video_progress = 'hide_video_progress'


class PhantomPlayer:

    def __init__(self, application):

        self.__playlist_new = None
        self.__playlists = OrderedDict()
        self.__playlists_loaded = False
        self.__current_playlist_loaded = False

        self.__current_media = CurrentMedia()
        self.__is_full_screen = None
        self.__threads = []

        self.__configuration = CCParser(_CONF_FILE, GlobalConfigTags._main_section)

        #
        #   GTK objects
        #
        self.__gtk_settings = Gtk.Settings.get_default()

        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), "main-window.glade"))

        self.__window_root = builder.get_object('window_root')
        self.__window_about = builder.get_object('window_about')
        self.__headerbar = builder.get_object('headerbar')
        self.__menubutton_main = builder.get_object('menubutton_main')
        self.__button_new_playlist = builder.get_object('button_new_playlist')
        self.__button_playlist_settings = builder.get_object('button_playlist_settings')
        self.__entry_search_playlists = builder.get_object('entry_search_playlists')
        self.__menubar = builder.get_object('menubar')
        self.__statusbar = builder.get_object('statusbar')
        self.__menuitem_about = builder.get_object('menuitem_about')
        self.__button_display_playlists = builder.get_object('button_display_playlists')
        self.__scrolledwindow_playlists = builder.get_object('scrolledwindow_playlists')
        self.__media_box = builder.get_object('media_box')
        self.__treeview_videos = builder.get_object('treeview_videos')
        self.__iconview_playlists = builder.get_object('iconview_playlists')
        self.__treeselection_playlist = builder.get_object('treeselection_playlist')
        self.__treeselection_videos = builder.get_object('treeselection_videos')
        self.__checkbox_prefer_dark_theme = builder.get_object('checkbox_prefer_dark_theme')
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
        self.__liststore_playlists = builder.get_object('liststore_playlists')
        self.__liststore_videos = builder.get_object('liststore_videos')
        box_window = builder.get_object('box_window')

        #
        # Header Bar
        #
        self.__headerbar.set_show_close_button(True)
        self.__window_root.set_titlebar(self.__headerbar)
        self.__menubutton_main.set_image(Gtk.Image.new_from_icon_name(settings.ThemeButtons._menu, Gtk.IconSize.BUTTON))

        #
        # GTK Binding
        #
        self.__window_root.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.__window_root.connect('delete-event', self.quit)
        self.__window_root.connect("configure-event", self.__on_window_root_configure_event)

        self.__entry_search_playlists.connect("changed", self.__on_entry_search_playlists_changed)
        self.__button_new_playlist.connect("clicked", self.__on_button_new_playlist_clicked)
        self.__button_playlist_settings.connect("clicked", self.__on_button_playlist_settings_clicked)

        self.__menuitem_about.connect("activate", self.__on_menuitem_about_activate)
        self.__checkbox_prefer_dark_theme.connect('toggled', self.__on__checkbox_prefer_dark_theme_toggled)
        self.__checkbox_hide_warning_missing_playlist.connect('toggled',
                                                              self.__on_checkbox_hide_warning_missing_playlist_toggled)
        self.__checkbox_hide_missing_playlist.connect('toggled', self.__on_checkbox_hide_missing_playlist_toggled)
        self.__checkbox_hidden_items.connect('toggled', self.__on_checkbox_hidden_items_toggled)
        self.__checkbox_hide_number.connect('toggled', self.__on_checkbox_hide_number_toggled)
        self.__checkbox_hide_path.connect('toggled', self.__on_checkbox_hide_path_toggled)
        self.__checkbox_hide_name.connect('toggled', self.__on_checkbox_hide_name_toggled)
        self.__checkbox_hide_extension.connect('toggled', self.__on_checkbox_hide_extension_toggled)
        self.__checkbox_hide_progress.connect('toggled', self.__on_checkbox_hide_progress_toggled)
        self.__iconview_playlists.connect('button-press-event', self.__on_iconview_playlists_press_event)
        self.__treeview_videos.connect('drag-end', self.__on_treeview_videos_drag_end)
        self.__treeview_videos.connect('button-press-event', self.__on_treeview_videos_press_event)
        self.__button_display_playlists.connect('clicked', self.__on_button_display_playlists_clicked)

        #
        #    Media Player
        #
        self.__mp_widget = MediaPlayerWidget(root_window=self.__window_root,
                                             random_button=True,
                                             keep_playing_button=True)

        self.__mp_widget.connect(CustomSignals._position_changed, self.__on_media_player_position_changed)
        self.__mp_widget.connect(CustomSignals._btn_keep_playing_toggled,
                                 self.__on_media_player_btn_keep_playing_toggled)
        self.__mp_widget.connect(CustomSignals._btn_random_toggled, self.__on_media_player_btn_random_toggled)
        self.__mp_widget.connect(CustomSignals._video_end, self.__on_media_player_video_end)

        self.__paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.__paned.add1(self.__mp_widget)
        box_window.remove(self.__media_box)
        self.__paned.add2(self.__media_box)
        box_window.pack_start(self.__paned, True, True, 0)

        #
        #    Configuration
        #
        if application is not None:
            self.__window_root.set_application(application)

        self.__settings_window = SettingsWindow(parent=self.__window_root,
                                                playlists=self.__playlists,
                                                add_function=self.__on_settings_playlist_add,
                                                delete_function=self.__on_settings_playlist_delete,
                                                restart_function=self.__on_settings_playlist_restart,
                                                close_function=self.__on_settings_playlist_close)

        self.__checkbox_prefer_dark_theme.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._prefer_dark_theme, True))
        self.__checkbox_hide_warning_missing_playlist.set_active(
            self.__configuration.get_bool(GlobalConfigTags._checkbox_missing_playlist_warning))
        self.__checkbox_hidden_items.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._checkbox_hidden_videos, False))
        self.__checkbox_hide_missing_playlist.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._checkbox_hide_missing_playlist, False))

        self.__checkbox_hide_number.set_active(self.__configuration.get_bool(GlobalConfigTags._hide_video_number))
        self.__checkbox_hide_path.set_active(self.__configuration.get_bool(GlobalConfigTags._hide_video_path))
        self.__checkbox_hide_name.set_active(self.__configuration.get_bool(GlobalConfigTags._hide_video_name))
        self.__checkbox_hide_extension.set_active(self.__configuration.get_bool(GlobalConfigTags._hide_video_extension))
        self.__checkbox_hide_progress.set_active(self.__configuration.get_bool(GlobalConfigTags._hide_video_progress))

        #
        #    Display the window
        #
        self.__load_fonts()
        self.__button_playlist_settings.set_sensitive(False)
        self.__button_new_playlist.set_sensitive(False)

        self.__window_root.maximize()
        self.__window_root.show_all()
        self.__mp_widget.hide_volume_label()
        self.__display_playlists(True)

        #
        #    Load the existent playlist
        #
        th = Thread(target=self.__playlists_load)
        th.start()
        self.__threads.append(th)

    def present(self):
        self.__window_root.present()

    def join(self):
        for th in self.__threads:
            th.join()

        self.__mp_widget.join()

    def save(self):
        if self.__playlists_loaded:
            for playlist in self.__playlists.values():
                playlist_factory.save(playlist)

    def quit(self, *_):
        self.__mp_widget.quit()
        VLC_INSTANCE.release()

    def __load_fonts(self):
        _, self.__fontcolor_default = gtk_utils.get_default_color(gtk_utils.FontColors._default,
                                                                  on_error=settings.FontColors._default)
        _, self.__fontcolor_success = gtk_utils.get_default_color(gtk_utils.FontColors._success,
                                                                  on_error=settings.FontColors._success)
        _, self.__fontcolor_warning = gtk_utils.get_default_color(gtk_utils.FontColors._warning,
                                                                  on_error=settings.FontColors._warning)
        _, self.__fontcolor_error = gtk_utils.get_default_color(gtk_utils.FontColors._error,
                                                                on_error=settings.FontColors._error)

    def __push_status(self, status):
        self.__statusbar.push(0, status)

    def __display_playlists(self, value):

        if value:
            self.__headerbar.props.title = Texts.GUI._title
            self.__current_media = CurrentMedia()
            self.__mp_widget.stop()
            self.__paned.hide()
            self.__scrolledwindow_playlists.show()
            self.__button_new_playlist.show()
            self.__entry_search_playlists.show()
            self.__menubutton_main.show()
            self.__button_playlist_settings.hide()
            self.__button_display_playlists.hide()
        else:
            self.__scrolledwindow_playlists.hide()
            self.__paned.show()
            self.__button_new_playlist.hide()
            self.__entry_search_playlists.hide()
            self.__menubutton_main.hide()
            self.__button_playlist_settings.show()
            self.__button_display_playlists.show()

            _, window_height = self.__window_root.get_size()
            self.__paned.set_position(window_height / 2)

    def __get_video_color(self, video):
        if video.get_ignore():
            return self.__fontcolor_warning

        elif video.get_is_new():
            return self.__fontcolor_success

        elif not video.exists():
            return self.__fontcolor_error

        return self.__fontcolor_default

    def __set_video(self,
                    video_id=None,
                    play=True,
                    replay=False,
                    ignore_none=False,
                    ignore_missing=False):

        if self.__current_media._playlist is None:
            return

        if video_id is None:
            video = self.__current_media.get_next_video()
        else:
            video = self.__current_media.get_video(video_id)

        if video is None:
            self.__window_root.unfullscreen()
            self.__mp_widget.stop()

            if not ignore_none:
                gtk_utils.dialog_info(self.__window_root, Texts.DialogPlaylist._all_videos_played)

            return

        elif not os.path.exists(video.get_path()):

            # If the player is reproducing another video, do not stop it.
            if not self.__mp_widget.is_playing():
                self.__mp_widget.stop()

            if not ignore_missing:
                gtk_utils.dialog_info(self.__window_root, Texts.DialogVideos._missing)

            return

        #
        # Update the playlist current video
        #
        self.__current_media._playlist.set_current_video_hash(video.get_hash())

        #
        # Update the configuration file
        #
        self.__configuration.write(GlobalConfigTags._current_playlist, self.__current_media._playlist.get_name())

        #
        # Play the video
        #
        self.__mp_widget.set_video(video.get_path(),
                                   position=video.get_position(),
                                   start_at=self.__current_media._playlist.get_start_at(),
                                   subtitles_track=self.__current_media._playlist.get_subtitles_track(),
                                   audio_track=self.__current_media._playlist.get_audio_track(),
                                   play=play,
                                   replay=replay)

        if self.__mp_widget.get_random() != self.__current_media._playlist.get_random():
            self.__mp_widget.set_random(self.__current_media._playlist.get_random())

        if self.__mp_widget.get_keep_playing() != self.__current_media._playlist.get_keep_playing():
            self.__mp_widget.set_keep_playing(self.__current_media._playlist.get_keep_playing())

        self.__liststore_videos_select_current()

    def __playlists_load(self):

        current_playlist_name = self.__configuration.get_str(GlobalConfigTags._current_playlist)
        current_playlist = None

        #
        # Load the playlists
        #

        GLib.idle_add(self.__push_status, Texts.StatusBar._load_playlist_headers)

        if os.path.exists(_SERIES_DIR):
            for file_name in sorted(os.listdir(_SERIES_DIR)):

                if not file_name.lower().endswith('.csv'):
                    continue

                new_playlist = playlist_factory.load_from_file(file_path=os.path.join(_SERIES_DIR, file_name),
                                                               pid=len(self.__playlists))

                if new_playlist.get_name() == current_playlist_name:
                    current_playlist = new_playlist

                self.__playlists[new_playlist.get_id()] = new_playlist

                if new_playlist.has_existent_paths() or not self.__checkbox_hide_missing_playlist.get_active():
                    GLib.idle_add(self.__liststore_playlists_append, new_playlist)

        #
        #    Start by loading the last playlist
        #
        if current_playlist is not None:
            GLib.idle_add(self.__push_status, Texts.StatusBar._load_playlist_cached.format(current_playlist.get_name()))

            current_playlist.set_waiting_load(True)
            self.__current_media = CurrentMedia(current_playlist)

            GLib.idle_add(self.__on_settings_playlist_close, current_playlist)

            # To ensure that the window is already maximized, and the pan will be correctly sized
            # probably .25 seconds may be enough, but 2 seconds is to avoid blinking the interface.
            sleep(2)
            GLib.idle_add(self.__display_playlists, False)

            video_factory.load(current_playlist, is_startup=True, add_func=self.__liststore_videos_add_glib)
            GLib.idle_add(self.__liststore_playlists_set_progress,
                          current_playlist.get_id(),
                          current_playlist.get_progress())

        #
        #   Load the rest of the videos
        #
        for playlist in self.__playlists.values():
            if current_playlist is not None and playlist.get_id() == current_playlist.get_id():
                continue

            playlist.set_waiting_load(True)
            GLib.idle_add(self.__push_status, Texts.StatusBar._load_playlist_cached.format(playlist.get_name()))
            GLib.idle_add(self.__on_settings_playlist_close, playlist)
            video_factory.load(playlist, is_startup=True)  # No add_func because the GUI is frozen on the first playlist

            GLib.idle_add(self.__liststore_playlists_set_progress,
                          playlist.get_id(),
                          playlist.get_progress())

        #
        #   Enable the GUI
        #
        GLib.idle_add(self.__button_playlist_settings.set_sensitive, True)
        GLib.idle_add(self.__button_new_playlist.set_sensitive, True)
        GLib.idle_add(self.__window_root.set_sensitive, True)
        GLib.idle_add(self.__push_status, Texts.StatusBar._load_playlists_ended)
        self.__playlists_loaded = True
        print("Load playlist ended.")

    def __playlist_find_videos(self, _, videos_id):

        if len(videos_id) == 1:  # if the user only selected one video to find...

            path = gtk_utils.dialog_select_file(self.__window_root)

            if path is None:
                return

            found_videos = self.__current_media._playlist.find_video(videos_id[0], path)
            gtk_utils.dialog_info(self.__window_root, Texts.DialogVideos._other_found.format(found_videos), None)

        else:

            path = gtk_utils.dialog_select_directory(self.__window_root)

            if path is None:
                return

            found_videos = self.__current_media._playlist.find_videos(path)
            gtk_utils.dialog_info(self.__window_root, Texts.DialogVideos._found_x.format(found_videos), None)

        if found_videos > 0:
            self.__liststore_videos_populate()

    def __liststore_playlists_set_progress(self, playlist_id, value):
        for i, row in enumerate(self.__liststore_playlists):
            if row[PlaylistListstoreColumnsIndex._id] == playlist_id:
                if row[PlaylistListstoreColumnsIndex._percent] != value:
                    self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._percent] = value
                return

    def __liststore_playlists_append(self, playlist):
        """
            I do not understand why this must be a separate method.
            It is not possible to call directly: GLib.idle_add(self.__liststore_playlists.append, data)
        """
        pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(),
                                              settings._DEFAULT_IMG_WIDTH,
                                              settings._DEFAULT_IMG_HEIGHT)
        self.__liststore_playlists.append([playlist.get_id(),
                                           pixbuf,
                                           playlist.get_name(),
                                           playlist.get_progress()])

    def __liststore_playlists_populate(self):

        #
        # Filter
        #
        text_filter = self.__entry_search_playlists.get_text().lower().strip()
        if text_filter == "":
            filtered_playlists = self.__playlists.values()
        else:
            filtered_playlists = []
            for playlist in self.__playlists.values():
                if text_filter in playlist.get_name().lower():
                    filtered_playlists.append(playlist)

        #
        # Populate
        #
        self.__liststore_playlists.clear()
        for playlist in sorted(filtered_playlists, key=lambda x: x.get_name()):
            if playlist.has_existent_paths() or not self.__checkbox_hide_missing_playlist.get_active():
                self.__liststore_playlists_append(playlist)

    def __liststore_videos_populate(self):

        self.__liststore_videos.clear()
        self.__column_name.set_spacing(0)

        if self.__current_media._playlist is None:
            return

        for video in self.__current_media._playlist.get_videos():
            self.__liststore_videos_add(video)

    def __liststore_videos_add_glib(self, playlist, video):
        """To be called from a thread"""

        if not self.__current_media.is_playlist(playlist):
            return

        GLib.idle_add(self.__liststore_videos_add, video)

        if video.get_hash() == playlist.get_current_video_hash() and not self.__mp_widget.has_media():
            GLib.idle_add(self.__set_video, video.get_id(), False, False, True, True)

    def __liststore_videos_add(self, video):
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

        video_id = self.__current_media.get_video_id()

        for i, row in enumerate(self.__liststore_videos):
            if row[VideosListstoreColumnsIndex._id] == video_id:
                self.__treeview_videos.set_cursor(i)
                break

    def __on_window_root_configure_event(self, *_):

        if Gdk.WindowState.FULLSCREEN & self.__window_root.get_window().get_state():
            fullscreen = True
        else:
            fullscreen = False

        if self.__is_full_screen != fullscreen:
            self.__is_full_screen = fullscreen

            if fullscreen:
                self.__scrolledwindow_playlists.hide()
                self.__media_box.hide()
                self.__statusbar.hide()
            else:
                self.__scrolledwindow_playlists.show()
                self.__media_box.show()
                self.__statusbar.show()

    def __on_media_player_btn_random_toggled(self, _, state):
        self.__current_media._playlist.set_random(state)

    def __on_media_player_btn_keep_playing_toggled(self, _, state):
        self.__current_media._playlist.set_keep_playing(state)

    def __on_media_player_position_changed(self, _, position):

        if self.__current_media.get_video_progress() == VideoProgress._end:
            # This is to avoid updating the progress on videos that was
            # already played.
            return

        self.__current_media.set_video_position(position)
        #
        # Update the GUI
        #
        if self.__current_media._playlist is None:
            return

        GLib.idle_add(self.__liststore_playlists_set_progress,
                      self.__current_media._playlist.get_id(),
                      self.__current_media._playlist.get_progress())

        video_id = self.__current_media.get_video_id()
        for i, row in enumerate(self.__liststore_videos):
            if row[VideosListstoreColumnsIndex._id] == video_id:
                self.__liststore_videos[i][
                    VideosListstoreColumnsIndex._progress] = self.__current_media.get_video_progress()
                break

    def __on_button_display_playlists_clicked(self, *_):
        self.__display_playlists(True)

    def __on_media_player_video_end(self, *_):

        self.__on_media_player_position_changed(None, VideoPosition._end)

        if not self.__current_media._playlist.get_keep_playing():
            self.__mp_widget.pause()
            self.__window_root.unfullscreen()
            return

        self.__set_video()

    def __on_iconview_playlists_press_event(self, iconview, event):

        if event.type != Gdk.EventType.BUTTON_PRESS or event.button != EventCodes.Cursor.left_click:
            return

        #
        # General
        #

        path = iconview.get_path_at_pos(event.x, event.y)
        if path is None:
            return

        playlist_id = self.__liststore_playlists[path][PlaylistListstoreColumnsIndex._id]
        playlist = self.__playlists[playlist_id]

        if not playlist.get_waiting_load():
            return

        self.__current_media = CurrentMedia(playlist)
        self.__liststore_videos_populate()
        self.__liststore_videos_select_current()
        self.__set_video(video_id=self.__current_media._playlist.get_last_played_video_id(),
                         play=False,
                         ignore_none=True,
                         ignore_missing=True)

        self.__display_playlists(False)

    def __on_treeview_videos_drag_end(self, *_):

        # Get the new order
        new_order = [row[VideosListstoreColumnsIndex._id] for row in self.__liststore_videos]

        # Update the treeview
        for i, row in enumerate(self.__liststore_videos, 1):
            row[VideosListstoreColumnsIndex._id] = i

        # Update the CSV file
        self.__current_media._playlist.reorder(new_order)
        self.__treeselection_videos.unselect_all()

    def __on_treeview_videos_press_event(self, _, event):
        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        selection_length = len(treepaths)

        if event.button == EventCodes.Cursor.left_click and \
                selection_length == 1 and \
                event.type == Gdk.EventType._2BUTTON_PRESS:

            video_id = self.__liststore_videos[treepaths[0]][VideosListstoreColumnsIndex._id]
            self.__configuration.write(GlobalConfigTags._current_playlist, self.__current_media._playlist.get_name())
            self.__set_video(video_id, replay=True)

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

            selected_ids = [self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id] for treepath in
                            treepaths]

            # If only 1 video is selected, and it is loaded in the player.
            # the progress buttons shall not be displayed.
            can_fill_progress = True
            can_reset_progress = True
            if len(selected_ids) == 1:
                if self.__current_media.get_video_id() == selected_ids[0]:
                    can_fill_progress = False
                    can_reset_progress = self.__current_media.get_video_progress() == VideoProgress._end

            if can_reset_progress:
                # Reset Progress
                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos._progress_reset)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_set_progress, VideoProgress._start)

            if can_fill_progress:
                # Fill progress
                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos._progress_fill)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_set_progress, VideoProgress._end)

            # Find videos
            if self.__current_media._playlist.missing_videos(selected_ids):
                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos._search)
                menuitem.connect('activate', self.__playlist_find_videos, selected_ids)
                menu.append(menuitem)

            # ignore videos
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos._ignore)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_playlist_ignore_video)

            # don't ignore videos
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos._dont_ignore)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_playlist_dont_ignore_video)

            # Open the containing folder (only if the user selected one video)
            if selection_length == 1:
                video_id = self.__liststore_videos[treepaths[0]][VideosListstoreColumnsIndex._id]
                video = self.__current_media._playlist.get_video(video_id)

                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos._open_dir)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_video_open_dir, video.get_path())

            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)

            return True

    def __on_menuitem_about_activate(self, *_):
        _ = self.__window_about.run()
        self.__window_about.hide()

    def __on_settings_playlist_add(self, playlist):

        self.__playlists[playlist.get_id()] = playlist

        if playlist.has_existent_paths() or not self.__checkbox_hide_missing_playlist.get_active():
            self.__liststore_playlists_append(playlist)

    def __on_settings_playlist_restart(self, playlist):
        # This is done before to avoid updating the playlist data
        was_playing = False
        if self.__current_media.is_playlist(playlist):
            if self.__mp_widget.is_playing():
                was_playing = True
                self.__mp_widget.pause()

        playlist.restart()

        if was_playing:
            self.__set_video()

        self.__liststore_playlists_set_progress(playlist.get_id(),
                                                playlist.get_progress())

        if self.__current_media.is_playlist(playlist):
            self.__liststore_videos_populate()

    def __on_settings_playlist_delete(self, playlist):

        self.__playlists.pop(playlist.get_id())

        # Remove from the player (if necessary)
        if self.__current_media.is_playlist(playlist):
            self.__mp_widget.stop()
            self.__current_media = CurrentMedia()

        # Delete the image (if saved)
        icon_path = playlist.get_icon_path(allow_default=False)
        if icon_path is not None and os.path.exists(icon_path):
            os.remove(icon_path)

        if os.path.exists(playlist.get_save_path()):
            os.remove(playlist.get_save_path())

        # remove the item from the playlist store
        for row in self.__liststore_playlists:
            if row[PlaylistListstoreColumnsIndex._id] == playlist.get_id():
                self.__liststore_playlists.remove(row.iter)
                break

        if self.__current_media.is_playlist(playlist):
            self.__display_playlists(True)

    def __on_settings_playlist_close(self, closed_playlist):

        # Update the playlists liststore
        for i, row in enumerate(self.__liststore_playlists):
            if row[PlaylistListstoreColumnsIndex._id] == closed_playlist.get_id():
                # Update the icon
                pixbuf = Pixbuf.new_from_file_at_size(closed_playlist.get_icon_path(),
                                                      settings._DEFAULT_IMG_WIDTH,
                                                      settings._DEFAULT_IMG_HEIGHT)
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._icon] = pixbuf

                # Update the name
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._name] = closed_playlist.get_name()
                break

        if self.__current_media.is_playlist(closed_playlist):
            # Update the videos liststore
            self.__liststore_videos_populate()

            # Update the media player
            self.__mp_widget.set_keep_playing(closed_playlist.get_keep_playing())
            self.__mp_widget.set_random(closed_playlist.get_random())

    def __on_entry_search_playlists_changed(self, *_):
        self.__liststore_playlists_populate()

    def __on_button_new_playlist_clicked(self, *_):
        new_playlist = Playlist(pid=len(self.__playlists))
        new_playlist.set_waiting_load(True)
        self.__settings_window.show(new_playlist, is_new=True)

    def __on_button_playlist_settings_clicked(self, *_):
        self.__settings_window.show(self.__current_media._playlist, is_new=False)

    def __on_menuitem_set_progress(self, _, progress):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        id_to_skip = None
        if progress == VideoProgress._start and self.__current_media.get_video_progress() == VideoProgress._end:
            pass
        else:
            id_to_skip = self.__current_media.get_video_id()

        for treepath in treepaths:

            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id]
            if video_id == id_to_skip:
                continue

            self.__liststore_videos[treepath][VideosListstoreColumnsIndex._progress] = progress
            video = self.__current_media._playlist.get_video(video_id)
            if progress == VideoProgress._start:
                video.set_position(VideoPosition._start)
            else:
                video.set_position(progress / VideoProgress._end)

        self.__liststore_playlists_set_progress(self.__current_media._playlist.get_id(),
                                                self.__current_media._playlist.get_progress())

    def __on_menuitem_playlist_ignore_video(self, _):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        hide_row = self.__checkbox_hidden_items.get_active()

        for treepath in reversed(treepaths):
            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id]
            video = self.__current_media._playlist.get_video(video_id)
            video.set_ignore(True)

            if hide_row:
                row_iter = model.get_iter(treepath)
                model.remove(row_iter)
            else:
                self.__liststore_videos[treepath][VideosListstoreColumnsIndex._color] = self.__fontcolor_warning

        self.__treeselection_videos.unselect_all()

    def __on_menuitem_playlist_dont_ignore_video(self, _):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        for treepath in treepaths:
            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id]
            video = self.__current_media._playlist.get_video(video_id)
            video.set_ignore(False)
            self.__liststore_videos[treepath][VideosListstoreColumnsIndex._color] = self.__get_video_color(video)

        self.__treeselection_videos.unselect_all()

    @staticmethod
    def __on_menuitem_video_open_dir(_, path):
        if os.path.exists(path):
            open_directory(path)

    def __on__checkbox_prefer_dark_theme_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__configuration.write(GlobalConfigTags._prefer_dark_theme, state)
        self.__gtk_settings.set_property("gtk-application-prefer-dark-theme", state)

        self.__load_fonts()
        self.__liststore_videos_populate()

    def __on_checkbox_hide_warning_missing_playlist_toggled(self, checkbox, *_):
        self.__configuration.write(GlobalConfigTags._checkbox_missing_playlist_warning, checkbox.get_active())

    def __on_checkbox_hide_missing_playlist_toggled(self, checkbox, *_):
        self.__liststore_playlists_populate()
        self.__configuration.write(GlobalConfigTags._checkbox_hide_missing_playlist, checkbox.get_active())

    def __on_checkbox_hidden_items_toggled(self, checkbox, *_):
        self.__configuration.write(GlobalConfigTags._checkbox_hidden_videos, checkbox.get_active())
        self.__liststore_videos_populate()

    def __on_checkbox_hide_number_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_number.set_visible(not state)
        self.__configuration.write(GlobalConfigTags._hide_video_number, state)

    def __on_checkbox_hide_path_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_path.set_visible(not state)
        self.__configuration.write(GlobalConfigTags._hide_video_path, state)

    def __on_checkbox_hide_name_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_name.set_visible(not state)
        self.__configuration.write(GlobalConfigTags._hide_video_name, state)

    def __on_checkbox_hide_extension_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_extension.set_visible(not state)
        self.__configuration.write(GlobalConfigTags._hide_video_extension, state)

    def __on_checkbox_hide_progress_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__column_progress.set_visible(not state)
        self.__configuration.write(GlobalConfigTags._hide_video_progress, state)

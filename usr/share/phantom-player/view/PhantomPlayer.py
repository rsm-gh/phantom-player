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
import sys
from threading import Thread
from collections import OrderedDict

os.environ["GDK_BACKEND"] = "x11"

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GLib
from gi.repository.GdkPixbuf import Pixbuf

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.dirname(_SCRIPT_DIR))

from controller.CCParser import CCParser
from controller import video_factory
from controller import playlist_factory
from model.Playlist import Playlist
from model.Video import VideoPosition, VideoProgress
from model.CurrentMedia import CurrentMedia
from view.SettingsWindow import SettingsWindow
from view.MediaPlayerWidget import MediaPlayerWidget, VLC_INSTANCE, CustomSignals
from view.common import _FONT_NEW_COLOR, _FONT_ERROR_COLOR, _FONT_DEFAULT_COLOR, _FONT_HIDE_COLOR
from Texts import Texts
from view import gtk_utils
from Paths import _SERIES_DIR, _CONF_FILE
from system_utils import EventCodes, open_directory

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
    _checkbox_missing_playlist_warning = "missing-playlist-warning"
    _checkbox_hidden_videos = "hidden-videos"
    _checkbox_hide_missing_playlist = "hide-missing-playlist"


class PhantomPlayer:

    def __init__(self, application, dark_mode=False):

        self.__playlist_new = None
        self.__playlist_selected = None
        self.__playlists = OrderedDict()
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

        #
        #   GTK objects
        #
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "main-window.glade"))

        self.__window_root = builder.get_object('window_root')
        self.__window_about = builder.get_object('window_about')
        self.__menubar = builder.get_object('menubar')
        self.__statusbar = builder.get_object('statusbar')
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
        self.__liststore_playlists = builder.get_object('liststore_playlists')
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
        self.__mp_widget = MediaPlayerWidget(root_window=self.__window_root,
                                             random_button=True,
                                             keep_playing_button=True,
                                             css_style=css_style)

        self.__mp_widget.connect(CustomSignals._position_changed, self.__on_media_player_position_changed)
        self.__mp_widget.connect(CustomSignals._btn_keep_playing_toggled,
                                 self.__on_media_player_btn_keep_playing_toggled)
        self.__mp_widget.connect(CustomSignals._btn_random_toggled, self.__on_media_player_btn_random_toggled)
        self.__mp_widget.connect(CustomSignals._video_end, self.__on_media_player_video_end)

        self.__paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.__paned.add1(self.__mp_widget)
        box_window.remove(self.__main_paned)
        self.__paned.add2(self.__main_paned)
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

        self.__checkbox_hide_warning_missing_playlist.set_active(
            self.__configuration.get_bool(GlobalConfigTags._checkbox_missing_playlist_warning))
        self.__checkbox_hidden_items.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._checkbox_hidden_videos, False))
        self.__checkbox_hide_missing_playlist.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._checkbox_hide_missing_playlist, False))

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
        self.__mp_widget.hide_volume_label()

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

        self.__mp_widget.join()

    def save(self):
        if self.__playlists_loaded:
            for playlist in self.__playlists.values():
                playlist_factory.save(playlist)

    def quit(self, *_):
        self.__mp_widget.quit()
        VLC_INSTANCE.release()

    def __push_status(self, status):
        self.__statusbar.push(0, status)

    @staticmethod
    def __get_video_color(video):
        if video.get_ignore():
            return _FONT_HIDE_COLOR

        elif video.get_is_new():
            return _FONT_NEW_COLOR

        elif not video.exists():
            return _FONT_ERROR_COLOR

        return _FONT_DEFAULT_COLOR

    def __set_video(self, video_id=None, play=True, replay=False, ignore_none=False):

        if self.__current_media._playlist is None:
            return

        if video_id is None:
            video = self.__current_media.get_next_video()
        else:
            video = self.__current_media.get_video(video_id)

        if video is None:
            if not ignore_none:
                gtk_utils.dialog_info(self.__window_root, Texts.DialogPlaylist.all_videos_played)

            self.__window_root.unfullscreen()
            self.__mp_widget.stop()
            return

        elif not os.path.exists(video.get_path()):
            gtk_utils.dialog_info(self.__window_root, Texts.DialogVideos.missing)

            # If the player is reproducing another video, do not stop it.
            if not self.__mp_widget.is_playing():
                self.__mp_widget.stop()

            return

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

    def __liststore_playlists_set_progress(self, playlist_id, value):
        for i, row in enumerate(self.__liststore_playlists):
            if row[PlaylistListstoreColumnsIndex._id] == playlist_id:
                if row[PlaylistListstoreColumnsIndex._percent] != value:
                    self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._percent] = value
                return

    def __liststore_playlists_append(self, pixbuf, playlist):
        """
            I do not understand why this must be a separate method.
            It is not possible to call directly: GLib.idle_add(self.__liststore_playlists.append, data)
        """
        self.__liststore_playlists.append([playlist.get_id(),
                                           pixbuf,
                                           playlist.get_name(),
                                           playlist.get_progress()])

    def __liststore_playlists_populate(self):

        current_playlist_name = self.__configuration.get_str('current_playlist')
        current_playlist = None

        self.__liststore_playlists.clear()

        for playlist in sorted(self.__playlists.values(), key=lambda x: x.get_name()):

            if playlist.get_name() == current_playlist_name:
                current_playlist = playlist

            if playlist.has_existent_paths() or not self.__checkbox_hide_missing_playlist.get_active():
                pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(), -1, 30)
                self.__liststore_playlists_append(pixbuf, playlist)

        if current_playlist is not None:
            for i, row in enumerate(self.__liststore_playlists):
                if row[PlaylistListstoreColumnsIndex._id] == current_playlist.get_id():
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
        if not self.__current_media.is_playlist(self.__playlist_selected):
            return

        video_id = self.__current_media.get_video_id()

        for i, row in enumerate(self.__liststore_videos):
            if row[VideosListstoreColumnsIndex._id] == video_id:
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

        current_playlist_name = self.__configuration.get_str('current_playlist')
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
                    pixbuf = Pixbuf.new_from_file_at_size(new_playlist.get_icon_path(), -1, 30)
                    GLib.idle_add(self.__liststore_playlists_append, pixbuf, new_playlist)

        #
        #   Select & Load the last playlist that was played
        #
        playlist_found = False
        if current_playlist is not None:
            GLib.idle_add(self.__push_status, Texts.StatusBar._load_playlist_cached.format(current_playlist.get_name()))
            video_factory.load(current_playlist, is_startup=True)
            self.__current_media = CurrentMedia(current_playlist)

            for i, row in enumerate(self.__liststore_playlists):
                if row[PlaylistListstoreColumnsIndex._id] == current_playlist.get_id():
                    GLib.idle_add(self.__treeview_playlist.set_cursor, i)
                    GLib.idle_add(self.__liststore_playlists_set_progress,
                                  current_playlist.get_id(),
                                  current_playlist.get_progress())
                    playlist_found = True
                    break

            if playlist_found:
                self.__set_video(play=False)

        #
        #   Load the rest of the videos
        #
        for playlist in self.__playlists.values():
            if current_playlist is not None and playlist.get_id() == current_playlist.get_id():
                continue

            GLib.idle_add(self.__push_status, Texts.StatusBar._load_playlist_cached.format(playlist.get_name()))
            video_factory.load(playlist, is_startup=True)

            GLib.idle_add(self.__liststore_playlists_set_progress,
                          playlist.get_id(),
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
        GLib.idle_add(self.__push_status, Texts.StatusBar._load_playlists_ended)
        print("Load playlist ended.")

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
        if not self.__current_media.is_playlist(self.__playlist_selected):
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

    def __on_media_player_video_end(self, *_):

        self.__on_media_player_position_changed(None, VideoPosition._end)

        if not self.__current_media._playlist.get_keep_playing():
            self.__mp_widget.pause()
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

        selected_playlist_id = gtk_utils.treeselection_get_first_cell(self.__treeselection_playlist,
                                                                      PlaylistListstoreColumnsIndex._id)
        self.__playlist_selected = self.__playlists[selected_playlist_id]

        #
        # Process the events
        #
        if event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == EventCodes.Cursor.left_click:

                if self.__mp_widget.is_nothing():
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
                if self.__current_media.is_playlist(self.__playlist_selected):
                    if not self.__mp_widget.is_nothing():
                        if self.__mp_widget.is_paused():
                            self.__mp_widget.play()

                        return

                """
                    Play a video of the playlist
                """
                self.__configuration.write('current_playlist', self.__playlist_selected.get_name())
                self.__current_media = CurrentMedia(self.__playlist_selected)
                self.__set_video()

    def __on_treeview_videos_drag_end(self, *_):

        # Get the new order
        new_order = [row[VideosListstoreColumnsIndex._id] for row in self.__liststore_videos]

        # Update the treeview
        for i, row in enumerate(self.__liststore_videos, 1):
            row[VideosListstoreColumnsIndex._id] = i

        # Update the CSV file
        self.__playlist_selected.reorder(new_order)
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

            #
            #   Quit if the video is already playing
            #
            same_video = False
            if self.__current_media.is_playlist(self.__playlist_selected):
                if video_id == self.__current_media.get_video_id():
                    same_video = True
                    if self.__mp_widget.is_playing():
                        return

            #
            #   Update
            #
            if not same_video:
                self.__configuration.write('current_playlist', self.__playlist_selected.get_name())
                self.__current_media = CurrentMedia(self.__playlist_selected)

            #
            #    Play the video
            #
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
                if self.__current_media.is_playlist(self.__playlist_selected):
                    if self.__current_media.get_video_id() == selected_ids[0]:
                        can_fill_progress = False
                        can_reset_progress = self.__current_media.get_video_progress() == VideoProgress._end

            if can_reset_progress:
                # Reset Progress
                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.progress_reset)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_set_progress, VideoProgress._start)

            if can_fill_progress:
                # Fill progress
                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.progress_fill)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_set_progress, VideoProgress._end)

            # Find videos
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
                video_id = self.__liststore_videos[treepaths[0]][VideosListstoreColumnsIndex._id]
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

        selected_playlist_id = gtk_utils.treeselection_get_first_cell(treeselection, PlaylistListstoreColumnsIndex._id)

        # This is because "press event" is executed before, so it is not necessary to re-define this
        if self.__playlist_selected is None or selected_playlist_id != self.__playlist_selected.get_id():
            self.__playlist_selected = self.__playlists[selected_playlist_id]

        self.__liststore_videos_populate()
        self.__liststore_videos_select_current()

    def __on_menuitem_about_activate(self, *_):
        _ = self.__window_about.run()
        self.__window_about.hide()

    def __on_menuitem_playlist_activate(self, *_):
        model, treepaths = self.__treeselection_playlist.get_selected_rows()
        self.__menuitem_playlist_settings.set_sensitive(len(treepaths) > 0)

    def __on_settings_playlist_add(self, new_playlist):

        self.__playlists[new_playlist.get_id()] = new_playlist

        if new_playlist.has_existent_paths() or not self.__checkbox_hide_missing_playlist.get_active():
            pixbuf = Pixbuf.new_from_file_at_size(new_playlist.get_icon_path(), -1, 30)
            self.__liststore_playlists_append(pixbuf, new_playlist)

            for i, row in enumerate(self.__liststore_playlists):
                if row[PlaylistListstoreColumnsIndex._id] == new_playlist.get_id():
                    self.__treeview_playlist.set_cursor(i)
                    break

    def __on_settings_playlist_restart(self, playlist):
        # This is done before to avoid updating the playlist data
        was_playing = False
        if self.__current_media.is_playlist(playlist):
            if self.__mp_widget.is_playing():
                was_playing = True
                self.__mp_widget.pause()

        self.__playlist_selected.restart()

        if was_playing:
            self.__set_video()

        # Update the liststores
        self.__liststore_playlists_set_progress(self.__playlist_selected.get_id(),
                                                self.__playlist_selected.get_progress())

        if self.__playlist_selected.get_id() == playlist.get_id():
            self.__liststore_videos_populate()

    def __on_settings_playlist_delete(self, playlist):

        self.__playlists.pop(playlist.get_id())

        # Remove from the player (if necessary)
        if self.__current_media.is_playlist(playlist):
            self.__mp_widget.stop()
            self.__current_media = CurrentMedia()

        # Delete the image (if saved)
        icon_path = self.__playlist_selected.get_icon_path(allow_default=False)
        if icon_path is not None and os.path.exists(icon_path):
            os.remove(icon_path)

        if os.path.exists(self.__playlist_selected.get_save_path()):
            os.remove(self.__playlist_selected.get_save_path())

        gtk_utils.treeselection_remove_first_row(self.__treeselection_playlist)

        if len(self.__liststore_playlists) > 0:
            self.__treeview_playlist.set_cursor(0)
        else:
            self.__liststore_videos.clear()

    def __on_settings_playlist_close(self, closed_playlist):

        # Update the playlists liststore
        for i, row in enumerate(self.__liststore_playlists):
            if row[PlaylistListstoreColumnsIndex._id] == closed_playlist.get_id():

                # Update the icon
                pixbuf = Pixbuf.new_from_file_at_size(closed_playlist.get_icon_path(), -1, 30)
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._icon] = pixbuf

                # Update the name
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._name] = closed_playlist.get_name()
                break


        # Update the media player
        if self.__current_media.is_playlist(closed_playlist):
            self.__mp_widget.set_keep_playing(closed_playlist.get_keep_playing())
            self.__mp_widget.set_random(closed_playlist.get_random())

        if self.__playlist_selected.get_id() == closed_playlist.get_id():
            self.__liststore_videos_populate()

    def __on_menuitem_playlist_new_activate(self, *_):
        self.__settings_window.show(Playlist(pid=len(self.__playlists)), is_new=True)

    def __on_menuitem_playlist_settings_activate(self, *_):
        self.__settings_window.show(self.__playlist_selected, is_new=False)

    def __on_menuitem_set_progress(self, _, progress):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        id_to_skip = None
        if self.__current_media.is_playlist(self.__playlist_selected):
            if progress == VideoProgress._start and self.__current_media.get_video_progress() == VideoProgress._end:
                pass
            else:
                id_to_skip = self.__current_media.get_video_id()

        for treepath in treepaths:

            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id]
            if video_id == id_to_skip:
                continue

            self.__liststore_videos[treepath][VideosListstoreColumnsIndex._progress] = progress
            video = self.__playlist_selected.get_video(video_id)
            if progress == VideoProgress._start:
                video.set_position(VideoPosition._start)
            else:
                video.set_position(progress / VideoProgress._end)

        self.__liststore_playlists_set_progress(self.__playlist_selected.get_id(),
                                                self.__playlist_selected.get_progress())

    def __on_menuitem_playlist_ignore_video(self, _):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        hide_row = self.__checkbox_hidden_items.get_active()

        for treepath in reversed(treepaths):
            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id]
            video = self.__playlist_selected.get_video(video_id)
            video.set_ignore(True)

            if hide_row:
                row_iter = model.get_iter(treepath)
                model.remove(row_iter)
            else:
                self.__liststore_videos[treepath][VideosListstoreColumnsIndex._color] = _FONT_HIDE_COLOR

        self.__treeselection_videos.unselect_all()

    def __on_menuitem_playlist_dont_ignore_video(self, _):

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        if not treepaths:
            return

        for treepath in treepaths:
            video_id = self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id]
            video = self.__playlist_selected.get_video(video_id)
            video.set_ignore(False)
            self.__liststore_videos[treepath][VideosListstoreColumnsIndex._color] = self.__get_video_color(video)

        self.__treeselection_videos.unselect_all()

    @staticmethod
    def __on_menuitem_video_open_dir(_, path):
        if os.path.exists(path):
            open_directory(path)

    def __on_checkbox_hide_warning_missing_playlist_toggled(self, *_):
        self.__configuration.write(GlobalConfigTags._checkbox_missing_playlist_warning,
                                   self.__checkbox_hide_warning_missing_playlist.get_active())

    def __on_checkbox_hide_missing_playlist_toggled(self, checkbox, *_):
        self.__liststore_playlists_populate()
        self.__configuration.write(GlobalConfigTags._checkbox_hide_missing_playlist, checkbox.get_active())

    def __on_checkbox_hidden_items_toggled(self, *_):
        self.__configuration.write(GlobalConfigTags._checkbox_hidden_videos, self.__checkbox_hidden_items.get_active())
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

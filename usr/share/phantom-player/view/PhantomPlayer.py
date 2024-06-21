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
    Bugs:
        + When selecting multiple videos to re-order with drag-and-drop, only the fist one is moved.
        + Fix dialog, paths, display how may valid videos, how many missing videos in the liststore.
        + Fix: right click of videos header

    To do:
        + Display the duplicated (excluded videos) at startup.
        + Finish the option "end at"
        + Improve user messages. Example: if path not added, or video not added, explain why.
        + Create the "delete video" option (instead of clean)
        + Create a dialog to rename multiple videos.
        + Add a 'still there?' dialog, based on time? episodes nb? activity? time of the day?
        + Add video size, video rating

    Patches:
        + self.__window_root_accel is to store the current window root accel group and be able to
          remove it.
            > I did not find how to properly check if an accel group belongs to a window.
            > calling window.remove_accel_group(accel_group) with a non-attached accel group throws critical warnings.
"""

import os
from time import sleep
from threading import Thread
from collections import OrderedDict

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
from model.Playlist import _SAVE_EXTENSION as _PLAYLIST_EXTENSION
from model.Playlist import LoadStatus as PlaylistLoadStatus
from model.CurrentMedia import CurrentMedia
from model.Video import VideoPosition, VideoProgress
from view.SettingsWindow import SettingsWindow
from view.DialogRenameSingle import DialogRenameSingle
from view.MediaPlayerWidget import MediaPlayerWidget, VLC_INSTANCE, CustomSignals
from view.cellrenderers.CellRendererPlaylist import CellRendererPlaylist


class PlaylistListstoreColumnsIndex:
    _id = 0
    _icon = 1
    _color = 2
    _name = 3
    _percent = 4


class VideosListstoreColumnsIndex:
    _color = 0
    _id = 1
    _path = 2
    _name = 3
    _ext = 4
    _progress = 5


class GlobalConfigTags:
    _main_section = "phantom-player"

    _dark_theme = "dark-theme"

    _playlist_missing = "playlist-missing"
    _playlist_current = "playlist-current"

    _video_cnumb = 'video-column-number'
    _video_cpath = 'video-column-path'
    _video_cname = 'video-column-name'
    _video_cext = 'video-column-extension'
    _video_cprog = 'video-column-progress'
    _video_rhidden = "videos-hidden"

    class IconSize:
        _label = "icon-size"
        _value_small = 'small'
        _value_medium = 'medium'
        _value_big = 'big'


class GUIView:
    _none = -1
    _playlists = 0
    _videos = 1
    _single_video = 2


class PhantomPlayer:

    def __init__(self, application):

        self.__application = application
        self.__playlist_new = None
        self.__playlists = OrderedDict()
        self.__current_playlist_loaded = False
        self.__playlist_headers_are_loaded = False

        self.__current_media = CurrentMedia()
        self.__is_full_screen = None
        self.__quit_requested = False

        self.__view_status = GUIView._none

        self.__icons_size = (settings.IconSize.Medium._width, settings.IconSize.Medium._height)

        self.__window_root_accel = None  # to store the window accel group and be able to remove it.

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
        self.__menuitem_new_playlist = builder.get_object('menuitem_new_playlist')
        self.__button_playlist_settings = builder.get_object('button_playlist_settings')

        self.__radio_icon_small = builder.get_object('radio_icon_small')
        self.__radio_icon_medium = builder.get_object('radio_icon_medium')
        self.__radio_icon_big = builder.get_object('radio_icon_big')

        self.__entry_playlist_search = builder.get_object('entry_playlist_search')
        self.__menubar = builder.get_object('menubar')
        self.__statusbar = builder.get_object('statusbar')
        self.__menuitem_open_file = builder.get_object('menuitem_open_file')
        self.__menuitem_about = builder.get_object('menuitem_about')
        self.__button_display_playlists = builder.get_object('button_display_playlists')
        self.__scrolledwindow_playlists = builder.get_object('scrolledwindow_playlists')
        self.__media_box = builder.get_object('media_box')
        self.__treeview_videos = builder.get_object('treeview_videos')
        self.__iconview_playlists = builder.get_object('iconview_playlists')
        self.__treeselection_playlist = builder.get_object('treeselection_playlist')
        self.__treeselection_videos = builder.get_object('treeselection_videos')
        self.__checkbox_dark_theme = builder.get_object('checkbox_dark_theme')
        self.__checkbox_playlist_missing = builder.get_object('checkbox_playlist_missing')

        self.__menu_videos_header = builder.get_object('menu_videos_header')
        self.__checkbox_video_cext = builder.get_object('checkbox_video_cext')
        self.__checkbox_video_cnumber = builder.get_object('checkbox_video_cnumber')
        self.__checkbox_video_cpath = builder.get_object('checkbox_video_cpath')
        self.__checkbox_video_cname = builder.get_object('checkbox_video_cname')
        self.__checkbox_video_cextension = builder.get_object('checkbox_video_cextension')
        self.__checkbox_video_cprogress = builder.get_object('checkbox_video_cprogress')
        self.__checkbox_video_rhidden = builder.get_object('checkbox_video_rhidden')

        self.__column_number = builder.get_object('column_number')
        self.__column_path = builder.get_object('column_path')
        self.__column_name = builder.get_object('column_name')
        self.__column_extension = builder.get_object('column_extension')
        self.__column_progress = builder.get_object('column_progress')
        self.__liststore_playlists = builder.get_object('liststore_playlists')
        self.__liststore_videos = builder.get_object('liststore_videos')
        self.__box_window = builder.get_object('box_window')
        self.__paned = None

        self.__menu_videos = builder.get_object('menu_videos')
        self.__menuitem_videos_restart_prg = builder.get_object('menuitem_videos_restart_prg')
        self.__menuitem_videos_fill_prg = builder.get_object('menuitem_videos_fill_prg')
        self.__menuitem_videos_ignore = builder.get_object('menuitem_videos_ignore')
        self.__menuitem_videos_unignore = builder.get_object('menuitem_videos_unignore')
        self.__menuitem_videos_rename = builder.get_object('menuitem_videos_rename')
        self.__menuitem_videos_open = builder.get_object('menuitem_videos_open')
        self.__menuitem_videos_delete = builder.get_object('menuitem_videos_delete')

        self.__box_window.remove(self.__media_box)

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
        self.__window_root.connect('key-press-event', self.__on_window_root_key_pressed)

        self.__window_root.connect('delete-event', self.quit)
        self.__window_root.connect("configure-event", self.__on_window_root_configure_event)

        self.__entry_playlist_search.connect("changed", self.__on_entry_playlist_search_changed)
        self.__button_playlist_settings.connect("clicked", self.__on_button_playlist_settings_clicked)

        self.__menuitem_new_playlist.connect("activate", self.__on_menuitem_new_playlist_activate)
        self.__menuitem_open_file.connect("activate", self.__on_menuitem_open_file)
        self.__menuitem_about.connect("activate", self.__on_menuitem_about_activate)
        self.__checkbox_dark_theme.connect('toggled', self.__on_checkbox_dark_theme_toggled)
        self.__checkbox_playlist_missing.connect('toggled', self.__on_checkbox_playlist_missing_toggled)
        self.__iconview_playlists.connect('item-activated', self.__on_iconview_playlists_item_activated)

        self.__radio_icon_small.connect('toggled', self.__on_radio_icon_size_toggled,
                                        GlobalConfigTags.IconSize._value_small)
        self.__radio_icon_medium.connect('toggled', self.__on_radio_icon_size_toggled,
                                         GlobalConfigTags.IconSize._value_medium)
        self.__radio_icon_big.connect('toggled', self.__on_radio_icon_size_toggled,
                                      GlobalConfigTags.IconSize._value_big)

        self.__checkbox_video_cnumber.connect('toggled',
                                              self.__on_checkbox_video_column_toggled,
                                              self.__column_number,
                                              GlobalConfigTags._video_cnumb)

        self.__checkbox_video_cpath.connect('toggled',
                                            self.__on_checkbox_video_column_toggled,
                                            self.__column_path,
                                            GlobalConfigTags._video_cpath)

        self.__checkbox_video_cname.connect('toggled',
                                            self.__on_checkbox_video_column_toggled,
                                            self.__column_name,
                                            GlobalConfigTags._video_cname)

        self.__checkbox_video_cextension.connect('toggled',
                                                 self.__on_checkbox_video_column_toggled,
                                                 self.__column_extension,
                                                 GlobalConfigTags._video_cext)

        self.__checkbox_video_cprogress.connect('toggled',
                                                self.__on_checkbox_video_column_toggled,
                                                self.__column_progress,
                                                GlobalConfigTags._video_cprog)

        self.__checkbox_video_rhidden.connect('toggled', self.__on_checkbox_video_rhidden_toggled)

        self.__treeview_videos.connect('drag-end', self.__on_treeview_videos_drag_end)
        self.__treeview_videos.connect("row-activated", self.__on_treeview_videos_row_activated)
        self.__treeview_videos.connect('button-press-event', self.__on_treeview_videos_press_event)
        self.__treeselection_videos.connect('changed', self.__on_treeselection_videos_changed)

        self.__button_display_playlists.connect('clicked', self.__on_button_display_playlists_clicked)

        for widget in (self.__column_number,
                       self.__column_path,
                       self.__column_name,
                       self.__column_extension,
                       self.__column_progress):
            gtk_utils.bind_header_click(widget, self.__on_treeview_videos_header_clicked)

        self.__menuitem_videos_restart_prg.connect('activate',
                                                   self.__on_menuitem_videos_set_progress,
                                                   VideoProgress._start)

        self.__menuitem_videos_fill_prg.connect('activate',
                                                self.__on_menuitem_videos_set_progress,
                                                VideoProgress._end)

        self.__menuitem_videos_ignore.connect('activate', self.__on_menuitem_videos_ignore_changed, True)
        self.__menuitem_videos_unignore.connect('activate', self.__on_menuitem_videos_ignore_changed, False)
        self.__menuitem_videos_rename.connect('activate', self.__on_menuitem_videos_rename_single)
        self.__menuitem_videos_open.connect('activate', self.__on_menuitem_videos_open)
        self.__menuitem_videos_delete.connect('activate', self.__on_menuitem_videos_delete)

        #
        # Playlist Accelerators
        #
        self.__accelgroup_playlists = Gtk.AccelGroup()

        self.__menuitem_open_file.add_accelerator('activate',
                                                  self.__accelgroup_playlists,
                                                  ord("o"),
                                                  Gdk.ModifierType.CONTROL_MASK,
                                                  Gtk.AccelFlags.VISIBLE)

        self.__menuitem_new_playlist.add_accelerator('activate',
                                                     self.__accelgroup_playlists,
                                                     ord("n"),
                                                     Gdk.ModifierType.CONTROL_MASK,
                                                     Gtk.AccelFlags.VISIBLE)

        self.__checkbox_playlist_missing.add_accelerator('activate',
                                                         self.__accelgroup_playlists,
                                                         ord("h"),
                                                         Gdk.ModifierType.CONTROL_MASK,
                                                         Gtk.AccelFlags.VISIBLE)

        #
        # Videos Accelerators
        #

        self.__accelgroup_videos = Gtk.AccelGroup()
        self.__checkbox_video_rhidden.add_accelerator('activate',
                                                      self.__accelgroup_videos,
                                                      ord("h"),
                                                      Gdk.ModifierType.CONTROL_MASK,
                                                      Gtk.AccelFlags.VISIBLE)

        self.__menuitem_videos_restart_prg.add_accelerator('activate',
                                                           self.__accelgroup_videos,
                                                           ord("u"),
                                                           Gdk.ModifierType.CONTROL_MASK,
                                                           Gtk.AccelFlags.VISIBLE)

        self.__menuitem_videos_fill_prg.add_accelerator('activate',
                                                        self.__accelgroup_videos,
                                                        ord("v"),
                                                        Gdk.ModifierType.CONTROL_MASK,
                                                        Gtk.AccelFlags.VISIBLE)

        self.__menuitem_videos_ignore.add_accelerator('activate',
                                                      self.__accelgroup_videos,
                                                      ord("i"),
                                                      Gdk.ModifierType.CONTROL_MASK,
                                                      Gtk.AccelFlags.VISIBLE)

        self.__menuitem_videos_unignore.add_accelerator('activate',
                                                        self.__accelgroup_videos,
                                                        ord("j"),
                                                        Gdk.ModifierType.CONTROL_MASK,
                                                        Gtk.AccelFlags.VISIBLE)

        self.__menuitem_videos_rename.add_accelerator('activate',
                                                      self.__accelgroup_videos,
                                                      ord("r"),
                                                      Gdk.ModifierType.CONTROL_MASK,
                                                      Gtk.AccelFlags.VISIBLE)

        self.__menuitem_videos_open.add_accelerator('activate',
                                                    self.__accelgroup_videos,
                                                    ord("o"),
                                                    Gdk.ModifierType.CONTROL_MASK,
                                                    Gtk.AccelFlags.VISIBLE)

        self.__menuitem_videos_delete.add_accelerator('activate',
                                                      self.__accelgroup_videos,
                                                      ord("d"),
                                                      Gdk.ModifierType.CONTROL_MASK,
                                                      Gtk.AccelFlags.VISIBLE)

        #
        # Iconview Cellrender
        #
        self.__cellrenderer_playlist = CellRendererPlaylist()
        self.__cellrenderer_playlist.set_icon_size(self.__icons_size[0], self.__icons_size[1])

        self.__iconview_playlists.pack_start(self.__cellrenderer_playlist, True)
        self.__iconview_playlists.add_attribute(self.__cellrenderer_playlist, 'pixbuf',
                                                PlaylistListstoreColumnsIndex._icon)
        self.__iconview_playlists.add_attribute(self.__cellrenderer_playlist, 'color',
                                                PlaylistListstoreColumnsIndex._color)
        self.__iconview_playlists.add_attribute(self.__cellrenderer_playlist, 'name',
                                                PlaylistListstoreColumnsIndex._name)
        self.__iconview_playlists.add_attribute(self.__cellrenderer_playlist, 'progress',
                                                PlaylistListstoreColumnsIndex._percent)

        #
        # Extra dialogs
        #
        self.__dialog_rename_single = DialogRenameSingle(self.__window_root, self.__liststore_videos_update)

        #
        #    Media Player
        #
        self.__mp_widget = MediaPlayerWidget(root_window=self.__window_root,
                                             random_button=True,
                                             keep_playing_button=True)

        # important or VLC will not be attached to the window when the player directly plays
        # a file video instead of a playlist.
        self.__box_window.pack_start(self.__mp_widget, True, True, 0)

        self.__mp_widget.connect(CustomSignals._position_changed, self.__on_media_player_position_changed)
        self.__mp_widget.connect(CustomSignals._btn_keep_playing_toggled,
                                 self.__on_media_player_btn_keep_playing_toggled)
        self.__mp_widget.connect(CustomSignals._btn_random_toggled, self.__on_media_player_btn_random_toggled)
        self.__mp_widget.connect(CustomSignals._video_end, self.__on_media_player_video_end)
        self.__mp_widget.connect(CustomSignals._video_restart, self.__on_media_player_video_restart)

        #
        #    Configuration
        #
        if application is not None:
            self.__window_root.set_application(application)

        self.__window_playlist_settings = SettingsWindow(parent=self.__window_root,
                                                         playlists=self.__playlists,
                                                         add_playlist_func=self.__on_window_psettings_playlist_add,
                                                         delete_playlist_func=self.__on_window_psettings_playlist_delete,
                                                         restart_playlist_func=self.__on_window_psettings_playlist_restart,
                                                         close_playlist_func=self.__on_window_psettings_playlist_close,
                                                         change_playlist_func=self.__on_window_psettings_playlist_change,
                                                         add_video_glib_func=self.__liststore_videos_add_glib,
                                                         update_video_glib_func=self.__liststore_videos_update_glib,
                                                         remove_video_glib_func=self.__liststore_videos_remove_glib,
                                                         reload_all_videos_func=self.__liststore_videos_populate)

        self.__checkbox_dark_theme.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._dark_theme, True))

        self.__checkbox_playlist_missing.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._playlist_missing, True))
        self.__checkbox_video_cnumber.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._video_cnumb, True))
        self.__checkbox_video_cpath.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._video_cpath, True))
        self.__checkbox_video_cname.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._video_cname, True))
        self.__checkbox_video_cextension.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._video_cext, True))
        self.__checkbox_video_cprogress.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._video_cprog, True))
        self.__checkbox_video_rhidden.set_active(
            self.__configuration.get_bool_defval(GlobalConfigTags._video_rhidden, True))

        match self.__configuration.get_str(GlobalConfigTags.IconSize._label):
            case GlobalConfigTags.IconSize._value_big:
                radio = builder.get_object('radio_icon_big')
            case GlobalConfigTags.IconSize._value_small:
                radio = builder.get_object('radio_icon_small')
            case _:
                radio = builder.get_object('radio_icon_medium')
        radio.set_active(True)

        # Fix: GUI initialization
        # I was expecting that connecting the checkbox.toggled before calling set_active() would activate the
        # signal, but it is not happening. This seems to be an easy fix:
        for checkbox in [self.__checkbox_video_cnumber,
                         self.__checkbox_video_cpath,
                         self.__checkbox_video_cname,
                         self.__checkbox_video_cextension,
                         self.__checkbox_video_cprogress,
                         # self.__checkbox_dark_theme,
                         # self.__checkbox_playlist_missing
                         # __checkbox_video_rhidden are not necessary
                         ]:
            checkbox.toggled()

        #
        #    Display the window
        #
        self.__fonts_reload()
        self.__menuitem_new_playlist.set_sensitive(False)
        self.__button_playlist_settings.set_sensitive(False)
        self.__window_root.maximize()
        self.__window_root.show_all()
        self.__mp_widget.hide_volume_label()
        self.__set_view(playlists_menu=True)

        #
        # Set the default cursor. This is important because if the software crashed with another cursor,
        # it will remain when restarting.
        #
        display = self.__window_root.get_display()
        window = self.__window_root.get_root_window()
        self.__default_cursor = Gdk.Cursor.new_from_name(display, 'default')
        window.set_cursor(self.__default_cursor)

        #
        #    Load the existent playlist
        #
        self.__thread_load_playlists = Thread(target=self.__on_thread_playlists_load)
        self.__thread_load_playlists.start()

    def present(self):
        self.__window_root.present()

    def wait_ready(self):
        while self.__playlist_headers_are_loaded is False:
            sleep(.2)

    def open_file(self, file_path):
        if self.__mp_widget.is_playing():
            self.__mp_widget.pause()

        #
        # Check if the settings window is busy
        #
        if self.__window_playlist_settings.get_visible():
            return False

        #
        # Play the video from a playlist (if it exists)
        #
        for playlist in self.__playlists.values():
            video = playlist.get_video_by_path(file_path)
            if video is not None:
                self.__playlist_open(playlist, video)
                return True

        #
        # Play the video without a playlist
        #
        self.__current_media = CurrentMedia()
        self.__set_view(False, only_player=True)
        self.__mp_widget.set_video(file_path)
        return True

    def get_quit(self):
        return self.__quit_requested

    def quit(self, *_):

        self.__mp_widget.pause()  # faster than quit

        if self.__current_media._playlist is not None:
            playlist_factory.save(self.__current_media._playlist)

        self.__quit_requested = True
        self.__mp_widget.quit()
        self.__thread_load_playlists.join()
        VLC_INSTANCE.release()

        if self.__application is None:
            Gtk.main_quit()
        else:
            self.__application.quit()

    def __get_video_color(self, video):

        if not video.exists():
            return self.__fontcolor_error

        elif video.get_ignore():
            return self.__fontcolor_warning

        elif video.get_is_new():
            return self.__fontcolor_success

        return self.__fontcolor_default

    def __set_video(self,
                    video_guid=None,
                    play=True,
                    replay=False,
                    ignore_none=False,
                    ignore_missing=False):

        if self.__current_media._playlist is None:
            return

        if video_guid is None:
            video = self.__current_media.get_next_video()
        else:
            video = self.__current_media.get_video_by_guid(video_guid)

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
        self.__configuration.write(GlobalConfigTags._playlist_current, self.__current_media._playlist.get_name())

        #
        # Play the video
        #
        if video.get_position() == VideoPosition._end and replay:
            video_position = VideoPosition._start
        else:
            video_position = video.get_position()

        self.__mp_widget.set_video(video.get_path(),
                                   position=video_position,
                                   start_at=self.__current_media._playlist.get_start_at(),
                                   subtitles_track=self.__current_media._playlist.get_subtitles_track(),
                                   audio_track=self.__current_media._playlist.get_audio_track(),
                                   play=play)

        if self.__mp_widget.get_random() != self.__current_media._playlist.get_random():
            self.__mp_widget.set_random(self.__current_media._playlist.get_random())

        if self.__mp_widget.get_keep_playing() != self.__current_media._playlist.get_keep_playing():
            self.__mp_widget.set_keep_playing(self.__current_media._playlist.get_keep_playing())

        self.__liststore_videos_select_current()

    def __set_view(self, playlists_menu, only_player=False):

        if self.__window_root_accel is not None:
            self.__window_root.remove_accel_group(self.__window_root_accel)
            self.__window_root_accel = None

        if playlists_menu:

            self.__view_status = GUIView._playlists

            self.__window_root_accel = self.__accelgroup_playlists

            self.__mp_widget.stop()
            if self.__current_media._playlist is not None:  # This can happen on single file mode
                playlist_factory.save(self.__current_media._playlist)

            self.__current_media = CurrentMedia()

            self.__headerbar.props.title = Texts.GUI._title
            if self.__paned is None:
                self.__box_window.remove(self.__mp_widget)
            else:
                self.__paned.hide()

            self.__button_playlist_settings.hide()
            self.__button_display_playlists.hide()

            self.__scrolledwindow_playlists.show()
            self.__entry_playlist_search.show()
            self.__menubutton_main.show()
            self.__statusbar.show()
        else:
            self.__entry_playlist_search.hide()
            self.__menubutton_main.hide()
            self.__scrolledwindow_playlists.hide()

            self.__button_playlist_settings.show()
            self.__button_display_playlists.show()

            if only_player:
                self.__view_status = GUIView._single_video
                self.__button_playlist_settings.set_sensitive(False)
                self.__statusbar.hide()
                self.__button_playlist_settings.hide()

                if self.__paned is not None:
                    self.__paned.remove(self.__mp_widget)
                    self.__paned.remove(self.__media_box)
                    self.__paned.destroy()
                    self.__paned = None

                self.__mp_widget.display_playlist_controls(False)
                self.__box_window.pack_start(self.__mp_widget, True, True, 0)

            else:
                self.__view_status = GUIView._videos
                self.__window_root_accel = self.__accelgroup_videos

                self.__statusbar.hide()
                self.__treeview_videos.show()
                self.__button_playlist_settings.show()
                self.__button_playlist_settings.set_sensitive(
                    self.__current_media._playlist.get_load_status() == PlaylistLoadStatus._loaded)

                self.__mp_widget.display_playlist_controls(True)

                if self.__paned is None:
                    self.__box_window.remove(self.__mp_widget)
                    self.__paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
                    self.__paned.add1(self.__mp_widget)
                    self.__paned.add2(self.__media_box)
                    self.__box_window.pack_start(self.__paned, True, True, 0)

                self.__paned.show_all()
                _, window_height = self.__window_root.get_size()
                self.__paned.set_position(window_height / 2)

        if self.__window_root_accel is not None:
            self.__window_root.add_accel_group(self.__window_root_accel)

    def __fonts_reload(self):
        _, self.__fontcolor_default = gtk_utils.get_default_color(gtk_utils.FontColors._default,
                                                                  on_error=settings.FontColors._default)
        _, self.__fontcolor_success = gtk_utils.get_default_color(gtk_utils.FontColors._success,
                                                                  on_error=settings.FontColors._success)
        _, self.__fontcolor_warning = gtk_utils.get_default_color(gtk_utils.FontColors._warning,
                                                                  on_error=settings.FontColors._warning)
        _, self.__fontcolor_error = gtk_utils.get_default_color(gtk_utils.FontColors._error,
                                                                on_error=settings.FontColors._error)

    def __playlist_open(self, playlist, video=None):
        self.__current_media = CurrentMedia(playlist)
        self.__set_view(playlists_menu=False)
        self.__liststore_videos_populate()
        self.__liststore_videos_select_current()

        if video is None:
            video_guid = self.__current_media._playlist.get_last_played_video_guid()
            play = False
            replay = False
        else:
            video_guid = video.get_guid()
            play = True
            replay = True

        self.__set_video(video_guid=video_guid,
                         play=play,
                         replay=replay,
                         ignore_none=True,
                         ignore_missing=True)

    def __playlist_update_gui(self, playlist, liststore_videos=True):
        self.__headerbar.props.title = playlist.get_name()
        self.__liststore_playlists_update(playlist)
        if self.__current_media.is_playlist(playlist):
            if liststore_videos:
                self.__liststore_videos_populate()
            self.__mp_widget.set_keep_playing(playlist.get_keep_playing())
            self.__mp_widget.set_random(playlist.get_random())

    def __statusbar_push(self, status):
        self.__statusbar.push(0, status)

    def __liststore_playlists_update_progress(self, playlist):
        if playlist is None:
            return

        for i, row in enumerate(self.__liststore_playlists):
            if row[PlaylistListstoreColumnsIndex._id] == playlist.get_guid():
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._percent] = playlist.get_progress()
                return

    def __liststore_playlists_update(self, playlist):
        for i, row in enumerate(self.__liststore_playlists):
            if row[PlaylistListstoreColumnsIndex._id] == playlist.get_guid():
                # Update the icon
                pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(),
                                                      self.__icons_size[0],
                                                      self.__icons_size[1])

                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._icon] = pixbuf
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._color] = self.__fontcolor_default
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._name] = playlist.get_name()
                self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._percent] = playlist.get_progress()
                break

    def __liststore_playlists_append(self, playlist):
        """
            I do not understand why this must be a separate method.
            It is not possible to call directly: GLib.idle_add(self.__liststore_playlists.append, data)
        """
        pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(),
                                              self.__icons_size[0],
                                              self.__icons_size[1])

        self.__liststore_playlists.append([playlist.get_guid(),
                                           pixbuf,
                                           self.__fontcolor_default,
                                           playlist.get_name(),
                                           playlist.get_progress()])

    def __liststore_playlists_populate(self):

        #
        # Filter
        #
        text_filter = self.__entry_playlist_search.get_text().lower().strip()
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
            if not playlist.is_missing() or self.__checkbox_playlist_missing.get_active():
                self.__liststore_playlists_append(playlist)

    def __liststore_videos_populate(self, *_):

        self.__liststore_videos.clear()
        self.__column_name.set_spacing(0)

        if self.__current_media._playlist is None:
            return

        for video in self.__current_media._playlist.get_videos():
            if not video.get_ignore() or self.__checkbox_video_rhidden.get_active():
                self.__liststore_videos_add(video)

    def __liststore_videos_add(self, video):
        if not video.get_ignore() or self.__checkbox_video_rhidden.get_active():
            self.__liststore_videos.append([self.__get_video_color(video),
                                            video.get_guid(),
                                            video.get_path(),
                                            video.get_name(),
                                            video.get_extension(),
                                            video.get_progress()])

    def __liststore_videos_update(self, video, progress=True, color=True, path=True):

        if video is None:
            return

        video_guid = video.get_guid()
        for i, row in enumerate(self.__liststore_videos):
            if row[VideosListstoreColumnsIndex._id] == video_guid:
                if color:
                    self.__liststore_videos[i][VideosListstoreColumnsIndex._color] = self.__get_video_color(video)

                if path:
                    self.__liststore_videos[i][VideosListstoreColumnsIndex._path] = video.get_path()
                    self.__liststore_videos[i][VideosListstoreColumnsIndex._name] = video.get_name()

                if progress:
                    self.__liststore_videos[i][VideosListstoreColumnsIndex._progress] = video.get_progress()
                return

    def __liststore_videos_select_current(self):
        """
            Select the current video from the videos liststore.
        """

        video_guid = self.__current_media.get_video_guid()

        for i, row in enumerate(self.__liststore_videos):
            if row[VideosListstoreColumnsIndex._id] == video_guid:
                self.__treeview_videos.set_cursor(i)
                break

    def __liststore_videos_remove(self, video):
        video_guid = video.get_guid()
        for row in self.__liststore_videos:
            if row[VideosListstoreColumnsIndex._id] == video_guid:
                self.__liststore_videos.remove(row.iter)
                break


    def __liststore_videos_add_glib(self, playlist, video):
        """To be called from a thread"""

        if not self.__current_media.is_playlist(playlist):
            return

        GLib.idle_add(self.__liststore_videos_add, video)

    def __liststore_videos_update_glib(self, playlist, video):
        """To be called from a thread"""

        if not self.__current_media.is_playlist(playlist):
            return

        GLib.idle_add(self.__liststore_videos_update, video)

    def __liststore_videos_remove_glib(self, playlist, video):
        """To be called from a thread"""

        if not self.__current_media.is_playlist(playlist):
            return

        elif self.__current_media.get_video_guid() == video.get_guid():
            self.__mp_widget.stop()

        GLib.idle_add(self.__liststore_videos_remove, video)

    def __treeselection_videos_get_selected(self):

        # Get the selected videos
        model, treepaths = self.__treeselection_videos.get_selected_rows()
        if not treepaths:
            return []

        selected_ids = [self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id] for treepath in
                        treepaths]

        return self.__current_media._playlist.get_videos_by_guid(selected_ids)

    def __on_thread_playlists_load(self):

        killed = False
        current_playlist_name = self.__configuration.get_str(GlobalConfigTags._playlist_current)
        current_playlist = None

        #
        # Load the playlist's files
        #
        if os.path.exists(_SERIES_DIR):
            for file_name in sorted(os.listdir(_SERIES_DIR)):

                if self.get_quit():
                    killed = True
                    break

                elif not file_name.lower().endswith(_PLAYLIST_EXTENSION):
                    continue

                full_path = os.path.join(_SERIES_DIR, file_name)

                GLib.idle_add(self.__statusbar_push, Texts.StatusBar._load_playlist_cached.format(file_name))

                playlist = playlist_factory.load(file_path=full_path)
                playlist.set_guid(len(self.__playlists))
                playlist.set_load_status(PlaylistLoadStatus._loading)

                if playlist.get_name() == current_playlist_name:
                    current_playlist = playlist

                self.__playlists[playlist.get_guid()] = playlist

                if not playlist.is_missing() or self.__checkbox_playlist_missing.get_active():
                    GLib.idle_add(self.__liststore_playlists_append, playlist)

        #
        # Once the playlist's files are loaded, it is possible to create new playlists.
        #
        GLib.idle_add(self.__menuitem_new_playlist.set_sensitive, True)
        self.__playlist_headers_are_loaded = True

        #
        #    Discover new videos of the playlists (starting by the saved playlist)
        #
        playlists = list(self.__playlists.values())
        if current_playlist is not None:
            playlists.remove(current_playlist)
            playlists.insert(0, current_playlist)

        for playlist in playlists:

            if self.get_quit():
                killed = True
                break

            # Do not call here:
            #     GLib.idle_add(self.__playlist_update_gui, playlist)
            # The GUI shall be updated only if the user selects the playlist, and for that
            # there is a different trigger.

            if playlist.requires_discover(is_startup=True):
                GLib.idle_add(self.__statusbar_push,
                              Texts.StatusBar._load_playlist_discover.format(playlist.get_name()))
                video_factory.discover(playlist,
                                       add_func=self.__liststore_videos_add_glib,
                                       update_func=self.__liststore_videos_update_glib,
                                       quit_func=self.get_quit)

                GLib.idle_add(self.__liststore_playlists_update_progress, playlist)

            GLib.idle_add(playlist.set_load_status, PlaylistLoadStatus._loaded)
            if self.__current_media.is_playlist(playlist) and playlist.get_load_status() == PlaylistLoadStatus._loaded:
                GLib.idle_add(self.__button_playlist_settings.set_sensitive, True)

        #
        #   Enable the GUI
        #
        GLib.idle_add(self.__window_root.set_sensitive, True)
        GLib.idle_add(self.__button_playlist_settings.set_sensitive, True)
        GLib.idle_add(self.__statusbar_push, Texts.StatusBar._load_playlists_ended)

        if killed:
            print("Load playlist killed.")
        else:
            print("Load playlist ended.")

    def __on_media_player_btn_random_toggled(self, _, state):
        self.__current_media._playlist.set_random(state)

    def __on_media_player_btn_keep_playing_toggled(self, _, state):
        self.__current_media._playlist.set_keep_playing(state)

    def __on_media_player_position_changed(self, _, position):

        if self.__current_media.get_video_position() == VideoPosition._end:
            # To avoid updating progress on videos that went already played.
            return

        self.__current_media.set_video_position(position)
        self.__liststore_playlists_update_progress(self.__current_media._playlist)
        self.__liststore_videos_update(self.__current_media._video, color=False, path=False)

    def __on_media_player_video_restart(self, *_):
        self.__on_media_player_position_changed(None, VideoPosition._start)

    def __on_media_player_video_end(self, _widget, _forced, was_playing):

        if self.__current_media._playlist is None:
            return

        self.__current_media.set_video_position(VideoPosition._end)
        playlist_factory.save(self.__current_media._playlist)  # Important in case of a crash

        self.__liststore_playlists_update_progress(self.__current_media._playlist)
        self.__liststore_videos_update(self.__current_media._video, color=False, path=False)

        if self.__current_media._playlist.get_keep_playing():
            self.__set_video(play=was_playing)
        else:
            self.__window_root.unfullscreen()

    def __on_window_root_key_pressed(self, _, event):
        """
            Keyboard shortcuts not in accel paths.
        """
        if self.__scrolledwindow_playlists.is_visible():

            if not (Gdk.ModifierType.CONTROL_MASK & event.state):
                return False

            match event.keyval:
                case EventCodes.Keyboard._letter_f:
                    self.__entry_playlist_search.grab_focus()
                    return True

        elif not gtk_utils.window_is_fullscreen(self.__window_root):

            if event.keyval == EventCodes.Keyboard._back:
                self.__set_view(playlists_menu=True)
                return True

            elif event.keyval in (EventCodes.Keyboard._enter, EventCodes.Keyboard._space_bar) and \
                    self.__view_status == GUIView._single_video:
                self.__mp_widget.play_pause()
                return True

            elif Gdk.ModifierType.CONTROL_MASK & event.state:
                if event.keyval == EventCodes.Keyboard._letter_s:  # display the settings
                    if self.__button_playlist_settings.get_sensitive():
                        self.__on_button_playlist_settings_clicked()
                    return True

            return False

    def __on_window_root_configure_event(self, *_):

        if Gdk.WindowState.FULLSCREEN & self.__window_root.get_window().get_state():
            fullscreen = True
        else:
            fullscreen = False

        if self.__is_full_screen != fullscreen:
            self.__is_full_screen = fullscreen

            if fullscreen:
                self.__media_box.hide()
                self.__statusbar.hide()
            else:
                self.__media_box.show()

    def __on_window_psettings_playlist_add(self, playlist):

        self.__playlists[playlist.get_guid()] = playlist

        if not playlist.is_missing() or self.__checkbox_playlist_missing.get_active():
            self.__liststore_playlists_append(playlist)

    def __on_window_psettings_playlist_restart(self, playlist):
        # This is done before to avoid updating the playlist data
        was_playing = False
        if self.__current_media.is_playlist(playlist):
            if self.__mp_widget.is_playing():
                was_playing = True
                self.__mp_widget.pause()

        playlist.restart()

        if was_playing:
            self.__set_video()

        self.__liststore_playlists_update_progress(playlist)

        if self.__current_media.is_playlist(playlist):
            self.__liststore_videos_populate()

    def __on_window_psettings_playlist_delete(self, playlist):

        self.__playlists.pop(playlist.get_guid())

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
            if row[PlaylistListstoreColumnsIndex._id] == playlist.get_guid():
                self.__liststore_playlists.remove(row.iter)
                break

        self.__set_view(playlists_menu=True)

    def __on_window_psettings_playlist_close(self, closed_playlist):
        self.__playlist_update_gui(closed_playlist, liststore_videos=False)

    def __on_window_psettings_playlist_change(self, new_playlist):
        self.__mp_widget.stop()
        if self.__current_media._playlist is not None:
            playlist_factory.save(self.__current_media._playlist)

        self.__current_media = CurrentMedia(new_playlist)
        self.__playlist_update_gui(new_playlist)

    def __on_entry_playlist_search_changed(self, *_):
        self.__liststore_playlists_populate()

    def __on_menuitem_new_playlist_activate(self, *_):
        new_playlist = Playlist()
        new_playlist.set_guid(len(self.__playlists))
        new_playlist.set_load_status(PlaylistLoadStatus._loaded)
        self.__window_playlist_settings.show(new_playlist, is_new=True)

    def __on_button_playlist_settings_clicked(self, *_):
        self.__window_playlist_settings.show(self.__current_media._playlist, is_new=False)

    def __on_button_display_playlists_clicked(self, *_):
        self.__set_view(playlists_menu=True)

    def __on_iconview_playlists_item_activated(self, _, path):

        playlist_id = self.__liststore_playlists[path][PlaylistListstoreColumnsIndex._id]
        playlist = self.__playlists[playlist_id]

        if playlist.get_load_status() == PlaylistLoadStatus._waiting_load:
            return

        self.__playlist_open(playlist)

    def __on_treeview_videos_drag_end(self, *_):

        # Get the new order
        new_order = [row[VideosListstoreColumnsIndex._id] for row in self.__liststore_videos]

        # Update the treeview
        for i, row in enumerate(self.__liststore_videos, 1):
            row[VideosListstoreColumnsIndex._id] = i

        # Update the CSV file
        self.__current_media._playlist.reorder(new_order)
        playlist_factory.save(self.__current_media._playlist)  # Important in case of a crash

    def __on_treeview_videos_row_activated(self, _treeview, treepath, _column):
        video_guid = self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id]
        self.__set_video(video_guid, replay=True)

    def __on_treeselection_videos_changed(self, *_):
        """
            Update the menuitems sensitive property because it will have an impact
            in the accel groups (keyboard shortcuts).
        """
        model, treepaths = self.__treeselection_videos.get_selected_rows()
        if not treepaths:
            self.__menuitem_videos_restart_prg.set_sensitive(False)
            self.__menuitem_videos_fill_prg.set_sensitive(False)
            self.__menuitem_videos_ignore.set_sensitive(False)
            self.__menuitem_videos_unignore.set_sensitive(False)
            self.__menuitem_videos_rename.set_sensitive(False)
            self.__menuitem_videos_open.set_sensitive(False)
            self.__menuitem_videos_delete.set_sensitive(False)
            return

        selected_ids = [self.__liststore_videos[treepath][VideosListstoreColumnsIndex._id] for treepath in
                        treepaths]
        selected_videos = self.__current_media._playlist.get_videos_by_guid(selected_ids)

        #
        # Enable/Disable the menuitems
        #

        # If only 1 video is selected, and it is loaded in the player.
        # the progress buttons shall not be displayed.
        can_fill_progress = True
        can_reset_progress = True
        if len(selected_videos) == 1:
            if self.__current_media.get_video_guid() == selected_ids[0]:
                can_fill_progress = False
                can_reset_progress = self.__current_media.get_video_progress() == VideoProgress._end

        self.__menuitem_videos_restart_prg.set_sensitive(
            any(video.get_position() > VideoPosition._start for video in selected_videos) and can_reset_progress)
        self.__menuitem_videos_fill_prg.set_sensitive(
            any(video.get_position() < VideoPosition._end for video in selected_videos) and can_fill_progress)
        self.__menuitem_videos_ignore.set_sensitive(any(not video.get_ignore() for video in selected_videos))
        self.__menuitem_videos_unignore.set_sensitive(any(video.get_ignore() for video in selected_videos))

        rename_and_open_video = False
        if len(selected_videos) == 1:
            video = selected_videos[0]
            if os.path.exists(video.get_path()):
                rename_and_open_video = True

        self.__menuitem_videos_rename.set_sensitive(rename_and_open_video)
        self.__menuitem_videos_open.set_sensitive(rename_and_open_video)

        self.__menuitem_videos_delete.set_sensitive(not any(video.exists() for video in selected_videos))

    def __on_treeview_videos_header_clicked(self, _widget, event):
        """
            The event button must be different from __on_treeview_videos_press_event,
            or this signal will be overridden.
        """

        if event.button != EventCodes.Cursor._right_click:
            return False

        #
        # Prevent that the users deactivate all the columns
        #
        column_checkboxes = (self.__checkbox_video_cnumber,
                             self.__checkbox_video_cpath,
                             self.__checkbox_video_cname,
                             self.__checkbox_video_cextension,
                             self.__checkbox_video_cprogress)
        active_checks = []
        for checkbox in column_checkboxes:
            checkbox.set_sensitive(True)

            if checkbox.get_active():
                active_checks.append(checkbox)

        if len(active_checks) == 1:
            active_checks[0].set_sensitive(False)

        # Show the menu
        self.__menu_videos_header.show_all()
        self.__menu_videos_header.popup(None, None, None, None, event.button, event.time)
        return True

    def __on_treeview_videos_press_event(self, _widget, event):

        if event.button != EventCodes.Cursor._right_click:
            return False

        model, treepaths = self.__treeselection_videos.get_selected_rows()

        # get the iter where the user is pointing
        # if the iter is not in the selected iters, remove the previous selection
        try:
            pointing_treepath = self.__treeview_videos.get_path_at_pos(event.x, event.y)[0]
        except Exception:
            return False

        if pointing_treepath not in treepaths:
            if not (Gdk.ModifierType.CONTROL_MASK & event.state):
                self.__treeselection_videos.unselect_all()

            self.__treeselection_videos.select_path(pointing_treepath)
            self.__on_treeselection_videos_changed()  # to ensure that it is applied before the menu pops-up

        self.__menu_videos.popup(None, None, None, None, event.button, event.time)
        return True

    def __on_radio_icon_size_toggled(self, _, config_value):

        if config_value == GlobalConfigTags.IconSize._value_small:
            self.__icons_size = (settings.IconSize.Small._width, settings.IconSize.Small._height)

        elif config_value == GlobalConfigTags.IconSize._value_medium:
            self.__icons_size = (settings.IconSize.Medium._width, settings.IconSize.Medium._height)

        elif config_value == GlobalConfigTags.IconSize._value_big:
            self.__icons_size = (settings.IconSize.Big._width, settings.IconSize.Big._height)

        else:
            raise ValueError("WRONG size", config_value)

        for i, row in enumerate(self.__liststore_playlists):
            guid = row[PlaylistListstoreColumnsIndex._id]
            playlist = self.__playlists[guid]
            pixbuf = Pixbuf.new_from_file_at_size(playlist.get_icon_path(),
                                                  self.__icons_size[0],
                                                  self.__icons_size[1])
            self.__liststore_playlists[i][PlaylistListstoreColumnsIndex._icon] = pixbuf

        self.__cellrenderer_playlist.set_icon_size(self.__icons_size[0], self.__icons_size[1])
        self.__configuration.write(GlobalConfigTags.IconSize._label, config_value)

    def __on_checkbox_dark_theme_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.__configuration.write(GlobalConfigTags._dark_theme, state)
        self.__gtk_settings.set_property("gtk-application-prefer-dark-theme", state)

        self.__fonts_reload()
        self.__liststore_videos_populate()

        for row in self.__liststore_playlists:
            row[PlaylistListstoreColumnsIndex._color] = self.__fontcolor_default

    def __on_checkbox_playlist_missing_toggled(self, checkbox, *_):
        self.__liststore_playlists_populate()
        self.__configuration.write(GlobalConfigTags._playlist_missing, checkbox.get_active())

    def __on_checkbox_video_column_toggled(self, checkbox, column, config_name):
        state = checkbox.get_active()
        column.set_visible(state)
        self.__configuration.write(config_name, state)

    def __on_checkbox_video_rhidden_toggled(self, checkbox, *_):
        self.__configuration.write(GlobalConfigTags._video_rhidden, checkbox.get_active())
        self.__liststore_videos_populate()

    def __on_menuitem_open_file(self, *_):
        file_path = gtk_utils.dialog_select_file(self.__window_root)
        if file_path is not None:
            self.open_file(file_path)

    def __on_menuitem_about_activate(self, *_):
        _ = self.__window_about.run()
        self.__window_about.hide()

    def __on_menuitem_videos_set_progress(self, _, progress):

        videos = self.__treeselection_videos_get_selected()
        if not videos:
            return

        id_to_skip = None
        if progress == VideoProgress._start and self.__current_media.get_video_progress() == VideoProgress._end:
            pass
        else:
            id_to_skip = self.__current_media.get_video_guid()

        for video in videos:
            if video.get_guid() == id_to_skip:
                continue

            if progress == VideoProgress._start:
                video.set_position(VideoPosition._start)
            else:
                video.set_position(progress / VideoProgress._end)

            self.__liststore_videos_update(video, color=False, path=False)

        self.__liststore_playlists_update_progress(self.__current_media._playlist)
        playlist_factory.save(self.__current_media._playlist)  # Important in case of a crash
        self.__on_treeselection_videos_changed()  # To reload the shortcuts

    def __on_menuitem_videos_ignore_changed(self, _, ignore):

        rhidden = self.__checkbox_video_rhidden.get_active()
        for video in self.__treeselection_videos_get_selected():
            video.set_ignore(ignore)
            if rhidden:
                self.__liststore_videos_update(video, progress=False, path=False)
            elif ignore:
                self.__liststore_videos_remove(video)

        playlist_factory.save(self.__current_media._playlist)  # Important in case of a crash
        self.__on_treeselection_videos_changed()  # To reload the shortcuts

    def __on_menuitem_videos_delete(self, *_):
        valid_videos = [video for video in self.__treeselection_videos_get_selected() if not video.exists()]
        self.__current_media._playlist.remove_videos(valid_videos)
        for video in valid_videos:
            self.__liststore_videos_remove(video)
        playlist_factory.save(self.__current_media._playlist)  # Important in case of a crash
        self.__on_treeselection_videos_changed()  # To reload the shortcuts

    def __on_menuitem_videos_rename_single(self, *_):
        selected_videos = self.__treeselection_videos_get_selected()

        if len(selected_videos) != 1:
            return

        self.__dialog_rename_single.show(selected_videos[0], self.__current_media._playlist)

    def __on_menuitem_videos_open(self, *_):

        selected_videos = self.__treeselection_videos_get_selected()

        if len(selected_videos) != 1:
            return

        dir_path = os.path.dirname(selected_videos[0].get_path())
        if os.path.exists(dir_path):
            open_directory(dir_path)

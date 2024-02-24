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
    + Fix: save the series status when the player changes random/keep plating.
    + Fix: when searching in the playlist liststore, the videos shall be emptied.
    + Move the series icon to the .local phantom dir
    + Select & focus the video on the liststore when start playing a series
    + Manage multiple paths into the playlist settings menu.
    + Apply the "load video" methods into a thread.
    + Fix start at
    + Add option: end at
    + Create a dialog to rename videos.
"""

import os
import gi
import sys
from threading import Thread

os.environ["GDK_BACKEND"] = "x11"

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
from controller.CCParser import CCParser
from controller.factory import str_to_boolean
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

    @staticmethod
    def convert_conf_to_gui(name):
        return name.replace("hide_video_", "checkbox_hide_")


class MainWindow:

    def __init__(self, dark_mode=False):

        self.__populating_settings = False
        self.__selected_playlist = None
        self.__new_playlist = None
        self.__current_media = CurrentMedia()
        self.__is_full_screen = None
        self.__playlist_dict = {}
        self.__threads = []

        self.__ccp = CCParser(CONFIGURATION_FILE, 'phantom-player')

        #
        #    load items from glade
        #
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "main-window.glade"))
        builder.connect_signals(self)

        glade_ids = (
            'window_root',
            'menubar',
            'menuitem_playlist_settings',
            'box_window',
            'main_paned',
            'treeview_videos',
            'treeview_playlist',
            'treeview_selection_playlist',
            'treeview_selection_videos',
            'liststore_playlist',
            'liststore_videos',
            'column_number',
            'column_path',
            'column_name',
            'column_extension',
            'column_progress',
            'checkbox_hidden_items',
            'checkbox_hide_extensions',
            'checkbox_hide_number',
            'checkbox_hide_path',
            'checkbox_hide_name',
            'checkbox_hide_extension',
            'checkbox_hide_progress',
            'checkbox_hide_warning_missing_playlist',
            'checkbox_hide_missing_playlist',
            'window_about',
        )

        for glade_id in glade_ids:
            setattr(self, glade_id, builder.get_object(glade_id))

        if dark_mode:
            css_style = _DARK_CSS
        else:
            css_style = None

        self.menubar.set_sensitive(False)
        self.treeview_playlist.set_sensitive(False)
        self.window_root.get_root_window().set_cursor(Gdk.Cursor.new_from_name(self.window_root.get_display(), 'wait'))

        self.__settings_dialog = SettingsDialog(self.window_root)

        #
        #    Media Player
        #
        self.__media_player = MediaPlayerWidget(self.window_root,
                                                random_button=True,
                                                keep_playing_button=True,
                                                css_style=css_style)

        self.__media_player.connect(CustomSignals.position_changed, self.__on_media_player_position_changed)
        self.__media_player.connect(CustomSignals.btn_keep_playing_toggled, self.__on_media_player_btn_keep_playing_toggled)
        self.__media_player.connect(CustomSignals.btn_random_toggled, self.__on_media_player_btn_random_toggled)
        self.__media_player.connect(CustomSignals.video_end, self.__on_media_player_video_end)

        self.__paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.__paned.add1(self.__media_player)
        self.box_window.remove(self.main_paned)
        self.__paned.add2(self.main_paned)
        self.box_window.pack_start(self.__paned, True, True, 0)

        #
        #    Configuration
        #

        # extra
        self.window_root.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.window_root.connect('delete-event', self.quit)
        self.window_root.connect("configure-event", self.__on_window_root_configure_event)
        self.window_root.connect("visibility_notify_event", self.__on_window_root_notify_event)

        # checkboxes
        self.checkbox_hide_warning_missing_playlist.set_active(
            self.__ccp.get_bool(GlobalConfigTags.checkbox_missing_playlist_warning))
        self.checkbox_hidden_items.set_active(
            self.__ccp.get_bool_defval(GlobalConfigTags.checkbox_hidden_videos, False))
        self.checkbox_hide_missing_playlist.set_active(
            self.__ccp.get_bool_defval(GlobalConfigTags.checkbox_hide_missing_playlist, False))

        for item_name in ("hide_video_number",
                          "hide_video_path",
                          "hide_video_name",
                          "hide_video_extension",
                          "hide_video_progress"):

            if self.__ccp.get_bool(item_name):
                checkbox = getattr(self, GlobalConfigTags.convert_conf_to_gui(item_name))
                checkbox.set_active(True)

        #
        # Font colors
        #
        _, self.__font_default_color = gtk_utils.get_default_color('theme_text_color',
                                                                   widget=self.treeview_videos,
                                                                   on_error="#000000")

        _, self.__font_hide_color = gtk_utils.get_default_color('warning_color',
                                                                widget=self.treeview_videos,
                                                                on_error="#ff9900")

        _, self.__font_error_color = gtk_utils.get_default_color('error_color',
                                                                 widget=self.treeview_videos,
                                                                 on_error="#ff0000")

        _, self.__font_new_color = gtk_utils.get_default_color('success_color',
                                                               widget=self.treeview_videos,
                                                               on_error="#009933")

        #
        #    Display the window
        #
        self.menuitem_playlist_settings.set_sensitive(False)

        if dark_mode:
            gtk_utils.set_css(self.window_root, css_style)
            gtk_utils.set_css(self.treeview_videos, css_style)

        self.window_root.maximize()
        self.window_root.show_all()
        self.__media_player.hide_volume_label()

        #
        #    Load the existent playlist
        #
        th = Thread(target=self.__on_thread_load_playlist)
        th.start()
        self.__threads.append(th)

    def join(self):
        for th in self.__threads:
            th.join()

        self.__media_player.join()

    def quit(self, *_):

        for playlist in self.__playlist_dict.values():
            playlist.save()

        self.__media_player.quit()
        Gtk.main_quit()

    def on_treeview_playlist_press_event(self, _, event, inside_treeview=True):
        """
            Important: this method is triggered before "selection_changes".
        """

        #
        # Select the current playlist
        #
        if self.treeview_selection_playlist.count_selected_rows() <= 0:
            self.__selected_playlist = None
            return

        selected_playlist_name = gtk_utils.treeview_selection_get_first_cell(self.treeview_selection_playlist, 1)
        self.__selected_playlist = self.__playlist_dict[selected_playlist_name]

        #
        # Process the events
        #
        if event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == EventCodes.Cursor.left_click:

                if self.__media_player.is_nothing():
                    self.__set_video(play=False, ignore_none=True)

            elif event.button == EventCodes.Cursor.right_click:

                # Get the iter where the user is pointing
                path = self.treeview_playlist.get_path_at_pos(event.x, event.y)

                if path is not None:
                    pointing_treepath = path[0]

                    # If the iter is not in the selected iters, remove the previous selection
                    model, treepaths = self.treeview_selection_playlist.get_selected_rows()

                    if pointing_treepath not in treepaths and inside_treeview:
                        self.treeview_selection_playlist.unselect_all()
                        self.treeview_selection_playlist.select_path(pointing_treepath)

                    self.__menu_playlist_display(event)

        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == EventCodes.Cursor.left_click:

                # check if the liststore is empty
                if len(self.liststore_videos) <= 0:
                    if not self.checkbox_hide_warning_missing_playlist.get_active():
                        gtk_utils.dialog_info(self.window_root, Texts.DialogPlaylist.is_missing)

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
                self.__ccp.write('current_playlist', selected_playlist_name)
                self.__current_media = CurrentMedia(self.__selected_playlist)
                self.__set_video()

    def on_treeview_videos_drag_end(self, *_):

        # Get the new order
        new_order = [row[VideosListstoreColumnsIndex.id] for row in self.liststore_videos]

        # Update the treeview
        for i, row in enumerate(self.liststore_videos, 1):
            row[VideosListstoreColumnsIndex.id] = i

        # Update the CSV file
        self.__selected_playlist.reorder(new_order)
        self.treeview_selection_videos.unselect_all()

    def on_treeview_videos_press_event(self, _, event):
        model, treepaths = self.treeview_selection_videos.get_selected_rows()

        if len(treepaths) == 0:
            return

        selection_length = len(treepaths)

        if event.button == EventCodes.Cursor.left_click and \
                selection_length == 1 and \
                event.type == Gdk.EventType._2BUTTON_PRESS:

            """
                Play the video of the playlist
            """

            self.__ccp.write('current_playlist', self.__selected_playlist.get_name())
            video_id = self.liststore_videos[treepaths[0]][VideosListstoreColumnsIndex.id]
            self.__current_media = CurrentMedia(self.__selected_playlist)
            self.__set_video(video_id)


        elif event.button == EventCodes.Cursor.right_click:

            # get the iter where the user is pointing
            try:
                pointing_treepath = self.treeview_videos.get_path_at_pos(event.x, event.y)[0]
            except Exception:
                return

            # if the iter is not in the selected iters, remove the previous selection
            model, treepaths = self.treeview_selection_videos.get_selected_rows()

            if pointing_treepath not in treepaths:
                self.treeview_selection_videos.unselect_all()
                self.treeview_selection_videos.select_path(pointing_treepath)

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
            selected_ids = [self.liststore_videos[treepath][VideosListstoreColumnsIndex.id] for treepath in treepaths]
            if self.__selected_playlist.missing_videos(selected_ids):
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
                video_id = self.liststore_videos[treepaths[0]][VideosListstoreColumnsIndex.id]
                video = self.__selected_playlist.get_video(video_id)

                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemVideos.open_dir)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_video_open_dir, video.get_path())

            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)

            return True

    def on_treeview_selection_playlist_changed(self, treeselection):

        if treeselection.count_selected_rows() <= 0:
            self.__selected_playlist = None
            return

        selected_playlist_name = gtk_utils.treeview_selection_get_first_cell(treeselection, 1)

        # This is because "press event" is executed before, so it is not necessary to re-define this
        if self.__selected_playlist is None or selected_playlist_name != self.__selected_playlist.get_name():
            self.__selected_playlist = self.__playlist_dict[selected_playlist_name]

        self.__liststore_videos_populate()
        self.__liststore_videos_select_current()

    def on_checkbox_hide_missing_playlist_toggled(self, checkbox, *_):
        self.__liststore_playlist_populate()
        self.__ccp.write(GlobalConfigTags.checkbox_hide_missing_playlist, checkbox.get_active())

    def on_checkbox_hide_number_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.column_number.set_visible(not state)
        self.__ccp.write('hide_video_number', state)

    def on_checkbox_hide_path_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.column_path.set_visible(not state)
        self.__ccp.write('hide_video_path', state)

    def on_checkbox_hide_name_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.column_name.set_visible(not state)
        self.__ccp.write('hide_video_name', state)

    def on_checkbox_hide_extension_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.column_extension.set_visible(not state)
        self.__ccp.write('hide_video_extension', state)

    def on_checkbox_hide_progress_toggled(self, checkbox, *_):
        state = checkbox.get_active()
        self.column_progress.set_visible(not state)
        self.__ccp.write('hide_video_progress', state)

    def on_checkbox_hide_warning_missing_playlist_toggled(self, *_):
        self.__ccp.write(GlobalConfigTags.checkbox_missing_playlist_warning,
                         self.checkbox_hide_warning_missing_playlist.get_active())

    def on_checkbox_hidden_items_toggled(self, *_):
        self.__ccp.write(GlobalConfigTags.checkbox_hidden_videos, self.checkbox_hidden_items.get_active())
        self.__liststore_videos_populate()

    def on_menuitem_about_activate(self, *_):
        _ = self.window_about.run()
        self.window_about.hide()

    def on_menuitem_playlist_activate(self, *_):
        model, treepaths = self.treeview_selection_playlist.get_selected_rows()
        self.menuitem_playlist_settings.set_sensitive(len(treepaths) > 0)

    def on_menuitem_playlist_new_activate(self, *_):
        new_playlist = Playlist()
        response = self.__settings_dialog.run(new_playlist,
                                              is_new=True,
                                              playlist_names=self.__playlist_dict.keys())

        if response == SettingsDialogResponse.close:
            # Delete the image (if saved)
            icon_path = new_playlist.get_image_path(allow_default=False)
            if icon_path is not None and os.path.exists(icon_path):
                os.remove(icon_path)

        elif response == SettingsDialogResponse.add:
            playlist_name = new_playlist.get_name()
            self.__playlist_dict[playlist_name] = new_playlist
            new_playlist.save()

            if os.path.exists(new_playlist.get_data_path()) or not self.checkbox_hide_missing_playlist.get_active():
                pixbuf = Pixbuf.new_from_file_at_size(new_playlist.get_image_path(), -1, 30)
                self.__liststore_playlist_append([pixbuf, playlist_name, 0])

                for i, row in enumerate(self.liststore_playlist):
                    if row[1] == playlist_name:
                        self.treeview_playlist.set_cursor(i)
                        break

    def on_menuitem_playlist_settings_activate(self, *_):

        response = self.__settings_dialog.run(self.__selected_playlist, is_new=False)
        playlist_name = self.__selected_playlist.get_name()

        if response == SettingsDialogResponse.delete:

            self.__playlist_dict.pop(self.__selected_playlist.get_name())

            # Remove from the player (if necessary)
            if self.__current_media.is_playlist_name(playlist_name):
                self.__media_player.stop()
                self.__current_media = CurrentMedia()

            # Delete the image (if saved)
            icon_path = self.__selected_playlist.get_image_path(allow_default=False)
            if icon_path is not None and os.path.exists(icon_path):
                os.remove(icon_path)

            if os.path.exists(self.__selected_playlist.get_save_path()):
                os.remove(self.__selected_playlist.get_save_path())

            gtk_utils.treeview_selection_remove_first_row(self.treeview_selection_playlist)

            if len(self.liststore_playlist) > 0:
                self.treeview_playlist.set_cursor(0)
            else:
                self.liststore_videos.clear()

            return

        #
        # In all the other cases
        #

        self.__selected_playlist.save()

        # Update the icon
        pixbuf = Pixbuf.new_from_file_at_size(self.__selected_playlist.get_image_path(), -1, 30)
        gtk_utils.treeview_selection_set_first_cell(self.treeview_selection_playlist,
                                                    PlaylistListstoreColumnsIndex.icon,
                                                    pixbuf)

        # Update the name
        old_name = gtk_utils.treeview_selection_get_first_cell(self.treeview_selection_playlist,
                                                               PlaylistListstoreColumnsIndex.name)

        if self.__selected_playlist.get_name() != old_name:
            self.__playlist_dict.pop(old_name)
            self.__playlist_dict[self.__selected_playlist.get_name()] = self.__selected_playlist
            gtk_utils.treeview_selection_set_first_cell(self.treeview_selection_playlist,
                                                        PlaylistListstoreColumnsIndex.name,
                                                        self.__selected_playlist.get_name())

        # Update the media player
        if self.__current_media.is_playlist_name(self.__selected_playlist.get_name()):
            self.__media_player.set_keep_playing(self.__selected_playlist.get_keep_playing())
            self.__media_player.set_random(self.__selected_playlist.get_random())

        if response == SettingsDialogResponse.restart:

            # This is done before to avoid updating the playlist data
            was_playing = False
            if self.__current_media.is_playlist_name(playlist_name):
                if self.__media_player.is_playing():
                    was_playing = True
                    self.__media_player.pause()

            self.__selected_playlist.restart()

            if was_playing:
                self.__set_video()

        self.__liststore_videos_populate()

    def on_button_playlist_path_add_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.window_root)
        if path is None:
            return

        playlist = self.__get_setting_playlist()
        playlist.set_path(path)
        playlist.save()

        self.liststore_paths.clear()
        self.liststore_paths.append([path, False])

        factory.load_videos(playlist)

        self.button_playlist_path_add.set_sensitive(False)
        self.button_playlist_path_edit.set_sensitive(True)
        self.button_playlist_path_reload_all.set_sensitive(True)

    def on_button_playlist_path_edit_clicked(self, *_):

        path = gtk_utils.dialog_select_directory(self.window_root)
        if path is None:
            return

        self.liststore_paths.clear()
        self.liststore_paths.append([path, False])

        playlist = self.__get_setting_playlist()
        playlist.set_path(path)
        factory.load_videos(playlist)
        playlist.save()

        if self.__new_playlist is None:
            self.__liststore_videos_populate()

    def on_button_playlist_path_reload_all_clicked(self, *_):
        playlist = self.__get_setting_playlist()
        factory.load_videos(playlist)

        if self.__new_playlist is None:
            self.__liststore_videos_populate()

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
                gtk_utils.dialog_info(self.window_root, Texts.DialogPlaylist.all_videos_played)

            self.window_root.unfullscreen()
            return

        elif not os.path.exists(video.get_path()):
            gtk_utils.dialog_info(self.window_root, Texts.DialogVideos.missing)
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

    def __playlist_load_from_path(self,
                                  name,
                                  data_path,
                                  recursive,
                                  random,
                                  keep_playing,
                                  start_at=0.0,
                                  audio_track=-2,
                                  subtitles_track=-2,
                                  select=True):

        new_playlist = Playlist(name,
                                data_path,
                                recursive,
                                random,
                                keep_playing,
                                start_at,
                                audio_track,
                                subtitles_track)

        self.__playlist_dict[new_playlist.get_name()] = new_playlist

        if os.path.exists(new_playlist.get_data_path()) or not self.checkbox_hide_missing_playlist.get_active():
            pixbuf = Pixbuf.new_from_file_at_size(new_playlist.get_image_path(), -1, 30)
            GLib.idle_add(self.__liststore_playlist_append, [pixbuf, new_playlist.get_name(), 0])

        if select:  # select the row once the playlist has been added

            factory.load_videos(new_playlist)

            for i, row in enumerate(self.liststore_playlist):
                if row[1] == new_playlist.get_name():
                    GLib.idle_add(self.treeview_playlist.set_cursor, i)
                    break

    def __playlist_find_videos(self, _, videos_id):

        if len(videos_id) == 1:  # if the user only selected one video to find...

            path = gtk_utils.dialog_select_file(self.window_root)

            if path is None:
                return

            found_videos = self.__selected_playlist.find_video(videos_id[0], path)
            gtk_utils.dialog_info(self.window_root, Texts.DialogVideos.other_found.format(found_videos), None)

        else:

            path = gtk_utils.dialog_select_directory(self.window_root)

            if path is None:
                return

            found_videos = self.__selected_playlist.find_videos(path)
            gtk_utils.dialog_info(self.window_root, Texts.DialogVideos.found_x.format(found_videos), None)

        if found_videos > 0:
            self.__liststore_videos_populate()

    def __liststore_playlist_append(self, data):
        """
            I do not understand why this must be a separate method.
            It is not possible to call directly: GLib.idle_add(self.liststore_playlist.append, data)
        """
        self.liststore_playlist.append(data)

    def __liststore_playlist_populate(self):

        # Populate
        #
        self.liststore_playlist.clear()

        for name in sorted(self.__playlist_dict.keys()):
            playlist = self.__playlist_dict[name]

            if os.path.exists(playlist.get_data_path()) or not self.checkbox_hide_missing_playlist.get_active():
                pixbuf = Pixbuf.new_from_file_at_size(playlist.get_image_path(), -1, 30)
                self.liststore_playlist.append([pixbuf, playlist.get_name(), playlist.get_progress()])

        # Select the current playlist
        #
        current_playlist_name = self.__ccp.get_str('current_playlist')

        for i, row in enumerate(self.liststore_playlist):
            if row[1] == current_playlist_name:
                self.treeview_playlist.set_cursor(i)
                return

        self.treeview_playlist.set_cursor(0)

    def __liststore_videos_populate(self):

        if self.__selected_playlist is None:
            return

        self.liststore_videos.clear()
        self.column_name.set_spacing(0)

        for video in self.__selected_playlist.get_videos():
            if not video.get_ignore() or not self.checkbox_hidden_items.get_active():
                self.liststore_videos.append([self.__get_video_color(video),
                                              video.get_id(),
                                              video.get_path(),
                                              video.get_name(),
                                              video.get_extension(),
                                              video.get_progress()])

    def __liststore_videos_select_current(self):
        """
            Select the current video from the videos liststore.
        """
        if not self.__current_media.is_playlist_name(self.__selected_playlist.get_name()):
            return

        video_id = self.__current_media.get_video_id()

        for i, row in enumerate(self.liststore_videos):
            if row[VideosListstoreColumnsIndex.id] == video_id:
                self.treeview_videos.set_cursor(i)
                break

    def __menu_playlist_display(self, event):

        menu = Gtk.Menu()

        menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemPlaylist.settings)
        menu.append(menuitem)
        menuitem.connect('activate', self.on_menuitem_playlist_settings_activate)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

        return True

    def __on_thread_load_playlist(self):

        #
        # Load the files header
        #
        if os.path.exists(FOLDER_LIST_PATH):
            for file_name in sorted(os.listdir(FOLDER_LIST_PATH)):

                if not file_name.lower().endswith('.csv'):
                    continue

                file_path = os.path.join(FOLDER_LIST_PATH, file_name)

                with open(file_path, mode='rt', encoding='utf-8') as f:
                    playlist_header = f.readline().split('|')
                    playlist_path = f.readline().split('|')

                if len(playlist_header) != 5 or len(playlist_path) != 2:
                    print("Error, Wrong format for playlist file = ", file_path)  # todo: show user message
                    continue

                data_path = playlist_path[0].strip()
                recursive = str_to_boolean(playlist_path[1])

                random = str_to_boolean(playlist_header[0])
                keep_playing = str_to_boolean(playlist_header[1])
                start_at = float(playlist_header[2])
                audio_track = int(playlist_header[3])
                subtitles_track = int(playlist_header[4])

                self.__playlist_load_from_path(file_name,
                                               data_path,
                                               recursive,
                                               random,
                                               keep_playing,
                                               start_at,
                                               audio_track,
                                               subtitles_track,
                                               select=False)

        #
        #   Select & Load the last playlist that was played
        #
        current_playlist_name = self.__ccp.get_str('current_playlist')

        try:
            playlist_data = self.__playlist_dict[current_playlist_name]
        except KeyError:
            playlist_data = None
        else:
            factory.load_videos(playlist_data)
            self.__current_media = CurrentMedia(playlist_data)

        playlist_found = False
        for i, row in enumerate(self.liststore_playlist):
            if row[1] == current_playlist_name:
                GLib.idle_add(self.treeview_playlist.set_cursor, i)
                playlist_found = True

        #
        #   Load the rest of the videos
        #
        for playlist in self.__playlist_dict.values():
            if playlist != playlist_data:
                factory.load_videos(playlist)

        #
        #   Select a default playlist if none
        #
        if not playlist_found:
            GLib.idle_add(self.treeview_playlist.set_cursor, 0)
            GLib.idle_add(self.window_root.set_sensitive, True)

        #
        #   Enable the GUI
        #
        default_cursor = Gdk.Cursor.new_from_name(self.window_root.get_display(), 'default')
        GLib.idle_add(self.window_root.get_root_window().set_cursor, default_cursor)
        GLib.idle_add(self.treeview_playlist.set_sensitive, True)
        GLib.idle_add(self.menubar.set_sensitive, True)

    def __on_media_player_btn_random_toggled(self, _, state):
        self.__current_media.playlist.set_random(state)

    def __on_media_player_btn_keep_playing_toggled(self, _, state):
        self.__current_media.playlist.set_keep_playing(state)

    def __on_media_player_position_changed(self, _, position):
        """
            Only update the liststore if the progress is different
        """

        update_progress = self.__current_media.is_playlist_name(self.__selected_playlist.get_name())
        if update_progress:
            current_progress = self.__current_media.get_video_progress()

        self.__current_media.set_video_position(position)

        if update_progress:
            new_progress = self.__current_media.get_video_progress()

            if current_progress == new_progress:
                return

            video_id = self.__current_media.get_video_id()
            for i, row_video in enumerate(self.liststore_videos):
                if row_video[VideosListstoreColumnsIndex.id] == video_id:
                    self.liststore_videos[i][VideosListstoreColumnsIndex.progress] = new_progress
                    return



    def __on_media_player_video_end(self, *_):
        if not self.__current_media.playlist.get_keep_playing():
            self.__media_player.pause()
            self.window_root.unfullscreen()
            return

        self.__set_video()


    def __on_window_root_notify_event(self, *_):
        # Resize the VLC widget
        _, window_height = self.window_root.get_size()
        self.__paned.set_position(window_height / 2)

    def __on_window_root_configure_event(self, *_):

        if Gdk.WindowState.FULLSCREEN & self.window_root.get_window().get_state():
            fullscreen = True
        else:
            fullscreen = False

        if self.__is_full_screen != fullscreen:
            self.__is_full_screen = fullscreen

            if fullscreen:
                self.menubar.hide()
                self.main_paned.hide()
            else:
                self.menubar.show()
                self.main_paned.show()

    def __on_menuitem_set_progress(self, _, progress):

        model, treepaths = self.treeview_selection_videos.get_selected_rows()

        if len(treepaths) == 0:
            return

        for treepath in treepaths:
            self.liststore_videos[treepath][VideosListstoreColumnsIndex.progress] = progress
            video_id = self.liststore_videos[treepath][VideosListstoreColumnsIndex.id]
            video = self.__selected_playlist.get_video(video_id)
            if progress == 0:
                video.set_position(0)
            else:
                video.set_position(progress / 100)

        self.__selected_playlist.save()

    def __on_menuitem_playlist_ignore_video(self, _):

        model, treepaths = self.treeview_selection_videos.get_selected_rows()

        if not treepaths:
            return

        hide_row = self.checkbox_hidden_items.get_active()

        for treepath in reversed(treepaths):
            video_id = self.liststore_videos[treepath][VideosListstoreColumnsIndex.id]
            video = self.__selected_playlist.get_video(video_id)
            video.set_ignore(True)

            if hide_row:
                row_iter = model.get_iter(treepath)
                model.remove(row_iter)
            else:
                self.liststore_videos[treepath][VideosListstoreColumnsIndex.color] = self.__font_hide_color

        self.treeview_selection_videos.unselect_all()
        self.__selected_playlist.save()

    def __on_menuitem_playlist_dont_ignore_video(self, _):

        model, treepaths = self.treeview_selection_videos.get_selected_rows()

        if not treepaths:
            return

        for treepath in treepaths:
            video_id = self.liststore_videos[treepath][VideosListstoreColumnsIndex.id]
            video = self.__selected_playlist.get_video(video_id)
            video.set_ignore(False)
            self.liststore_videos[treepath][VideosListstoreColumnsIndex.color] = self.__get_video_color(video)

        self.treeview_selection_videos.unselect_all()
        self.__selected_playlist.save()

    @staticmethod
    def __on_menuitem_video_open_dir(_, path):
        if os.path.exists(path):
            open_directory(path)


def run():
    vlist_player = MainWindow()
    Gtk.main()
    vlist_player.join()
    VLC_INSTANCE.release()

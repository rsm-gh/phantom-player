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
    + Remove the thread scan_media_player and replace it by signals from the media player.
    + Fix: save the series status when the player changes random/keep plating.
    + Move the series icon to the .local phantom dir
    + Select & focus the video on the liststore when start playing a series
    + Fix: when searching in the playlist liststore, the videos shall be emptied.
    + Add: accelerators to the playlist menu.
    + Manage multiple paths into the playlist settings menu.
    + Apply the "load video" methods into a thread.
    + Add option: end at
    + Create a dialog to rename videos.
"""

import os
import gi
import sys
import time
from threading import Thread, current_thread

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
from view.MediaPlayer import MediaPlayerWidget, VLC_INSTANCE

_DARK_CSS = """
@define-color theme_text_color white;
@define-color warning_color orange;
@define-color error_color red;
@define-color success_color green;

window, treeview, box, menu {
    background: #262626;
    color: white;
}"""

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

            'window_playlist_settings',
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

            'window_about',
        )

        if dark_mode:
            css_style = _DARK_CSS
        else:
            css_style = None

        for glade_id in glade_ids:
            setattr(self, glade_id, builder.get_object(glade_id))

        self.menubar.set_sensitive(False)
        self.treeview_playlist.set_sensitive(False)
        self.window_root.get_root_window().set_cursor(Gdk.Cursor.new_from_name(self.window_root.get_display(), 'wait'))

        """
            Media Player
        """
        self.__media_player = MediaPlayerWidget(self.window_root,
                                                random_button=True,
                                                keep_playing_button=True,
                                                css_style=css_style)

        self.__paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        self.__paned.add1(self.__media_player)
        self.box_window.remove(self.main_paned)
        self.__paned.add2(self.main_paned)
        self.box_window.pack_start(self.__paned, True, True, 0)

        self.__thread_scan_media_player = Thread(target=self.__on_thread_scan_media_player)
        self.__thread_scan_media_player.start()

        #
        #    configuration
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
        _, self.__font_default_color = gtk_utils.gtk_default_font_color('theme_text_color',
                                                                        widget=self.treeview_videos,
                                                                        on_error="#000000")

        _, self.__font_hide_color = gtk_utils.gtk_default_font_color('warning_color',
                                                                     widget=self.treeview_videos,
                                                                     on_error="#ff9900")

        _, self.__font_error_color = gtk_utils.gtk_default_font_color('error_color',
                                                                      widget=self.treeview_videos,
                                                                      on_error="#ff0000")

        _, self.__font_new_color = gtk_utils.gtk_default_font_color('success_color',
                                                                    widget=self.treeview_videos,
                                                                    on_error="#009933")

        #
        #    Display the window
        #
        self.menuitem_playlist_settings.set_sensitive(False)

        if dark_mode:
            gtk_utils.gtk_set_css(self.window_root, css_style)
            gtk_utils.gtk_set_css(self.treeview_videos, css_style)

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

        self.__thread_scan_media_player.join()
        self.__media_player.join()

    def quit(self, *_):
        self.__save_current_video_position()
        self.__media_player.quit()
        self.__thread_scan_media_player.do_run = False
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

        selected_playlist_name = gtk_utils.gtk_selection_get_first_selected_cell(self.treeview_selection_playlist, 1)
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
                        gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogPlaylist.is_missing)

                    return

                """
                    Check if the playlist is already selected and if a video is playing
                """
                if self.__current_media.is_playlist_name(selected_playlist_name):
                    if not self.__media_player.is_nothing():
                        if self.__media_player.is_paused():
                            self.__media_player.play()

                        return
                    else:
                        self.__save_current_video_position()

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
            self.__save_current_video_position()
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

        selected_playlist_name = gtk_utils.gtk_selection_get_first_selected_cell(treeselection, 1)

        # This is because "press event" is executed before, so it is not necessary to re-define this
        if self.__selected_playlist is None or selected_playlist_name != self.__selected_playlist.get_name():
            self.__selected_playlist = self.__playlist_dict[selected_playlist_name]

        self.__liststore_videos_populate()

    def on_cellrenderertoggle_playlist_recursive_toggled(self, _, row):
        state = not self.liststore_paths[row][1]
        self.liststore_paths[row][1] = state
        playlist = self.__get_setting_playlist()
        playlist.set_recursive(state)
        if self.__new_playlist is None:
            playlist.save()

    def on_switch_setting_keep_playing_button_press_event(self, widget, *_):
        status = not widget.get_active()
        playlist = self.__get_setting_playlist()
        playlist.set_keep_playing(status)

        if self.__current_media.is_playlist_name(playlist.get_name()):
            self.__media_player.set_keep_playing(status)

    def on_switch_setting_random_playing_button_press_event(self, widget, *_):
        status = not widget.get_active()
        playlist = self.__get_setting_playlist()
        playlist.set_random(status)

        if self.__current_media.is_playlist_name(playlist.get_name()):
            self.__media_player.set_random(status)

    def on_spinbutton_audio_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__selected_playlist.set_audio_track(value)

    def on_spinbutton_subtitles_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__selected_playlist.set_subtitles_track(value)

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

        self.__selected_playlist.set_start_at(value)

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
        self.__display_playlist_dialog(new_playlist=True)

    def on_menuitem_playlist_settings_activate(self, *_):
        self.__display_playlist_dialog()

    def on_button_playlist_delete_clicked(self, *_):

        playlist_name = self.__selected_playlist.get_name()

        if not gtk_utils.gtk_dialog_question(self.window_playlist_settings,
                                             Texts.DialogPlaylist.confirm_delete.format(playlist_name)):
            return

        gtk_utils.gtk_liststore_remove_first_selected_row(self.treeview_selection_playlist)

        if len(self.liststore_playlist) > 0:
            self.treeview_playlist.set_cursor(0)
        else:
            self.liststore_videos.clear()

        self.window_playlist_settings.hide()

        if self.__current_media.is_playlist_name(playlist_name):
            self.__media_player.stop()
            self.__current_media = CurrentMedia()

        playlist = self.__playlist_dict[playlist_name]
        self.__playlist_dict.pop(playlist_name)

        if os.path.exists(playlist.get_save_path()):
            os.remove(playlist.get_save_path())

    def on_button_playlist_add_clicked(self, *_):

        playlist_name = self.entry_playlist_name.get_text().strip()

        if playlist_name == "":
            gtk_utils.gtk_dialog_info(self.window_playlist_settings, Texts.WindowSettings.playlist_name_empty)
            return

        elif playlist_name in self.__playlist_dict.keys():
            gtk_utils.gtk_dialog_info(self.window_playlist_settings,
                                      Texts.DialogPlaylist.name_exist.format(playlist_name))
            return

        self.__new_playlist.rename(playlist_name)
        self.__new_playlist.save()
        self.__playlist_dict[playlist_name] = self.__new_playlist

        if os.path.exists(self.__new_playlist.get_path()) or not self.checkbox_hide_missing_playlist.get_active():
            pixbuf = Pixbuf.new_from_file_at_size(self.__new_playlist.get_image_path(), -1, 30)
            self.__liststore_playlist_append([pixbuf, self.__new_playlist.get_name()])

            for i, row in enumerate(self.liststore_playlist):
                if row[1] == playlist_name:
                    self.treeview_playlist.set_cursor(i)
                    break

        self.__new_playlist = None
        self.window_playlist_settings.hide()

    def on_button_playlist_close(self, *_):

        if self.__new_playlist is not None:
            self.__new_playlist = None

        else:
            new_name = self.entry_playlist_name.get_text().strip()

            if self.__selected_playlist.get_name() == new_name:
                pass

            elif new_name == "":
                gtk_utils.gtk_dialog_info(self.window_playlist_settings, Texts.WindowSettings.playlist_name_empty)
                return

            elif new_name in self.__playlist_dict.keys():
                gtk_utils.gtk_dialog_info(self.window_playlist_settings,
                                          Texts.DialogPlaylist.name_exist.format(new_name))
                return

            else:
                self.__playlist_dict.pop(self.__selected_playlist.get_name())
                self.__selected_playlist.rename(new_name)
                self.__playlist_dict[new_name] = self.__selected_playlist
                gtk_utils.gtk_selection_set_first_selected_cell(self.treeview_selection_playlist, 1, new_name)

        self.window_playlist_settings.hide()

    def on_button_playlist_restart_clicked(self, *_):

        selected_playlist_name = self.__selected_playlist.get_name()

        if not gtk_utils.gtk_dialog_question(self.window_playlist_settings,
                                             Texts.DialogPlaylist.confirm_reset.format(selected_playlist_name)):
            return

        self.window_playlist_settings.hide()

        # This is done before to avoid updating the playlist data
        was_playing = False
        if self.__current_media.is_playlist_name(selected_playlist_name):
            if self.__media_player.is_playing():
                was_playing = True
                self.__media_player.pause()

        playlist = self.__playlist_dict[selected_playlist_name]
        playlist.restart()
        self.__liststore_videos_populate()

        if was_playing:
            self.__set_video()

    def on_button_playlist_set_image_clicked(self, *_):
        """
            Add a picture to a playlist
        """
        file_filter = Gtk.FileFilter()
        file_filter.set_name('Image')
        file_filter.add_pattern('*.jpeg')
        file_filter.add_pattern('*.jpg')
        file_filter.add_pattern('*.png')

        file = gtk_utils.gtk_dialog_select_file(self.window_playlist_settings, file_filter)
        if file is not None:

            setting_playlist = self.__get_setting_playlist()
            setting_playlist.set_image_path(file)

            pixbuf = Pixbuf.new_from_file_at_size(file, -1, 30)
            self.image_playlist.set_from_pixbuf(pixbuf)

            if self.__new_playlist is None:
                gtk_utils.gtk_selection_set_first_selected_cell(self.treeview_selection_playlist,
                                                                0,
                                                                pixbuf)

    def on_button_playlist_path_add_clicked(self, *_):

        path = gtk_utils.gtk_dialog_select_directory(self.window_root)
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

    def on_button_playlist_path_remove_clicked(self, *_):
        pass

    def on_button_playlist_path_edit_clicked(self, *_):

        path = gtk_utils.gtk_dialog_select_directory(self.window_root)
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
                gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogPlaylist.all_videos_played)

        elif not os.path.exists(video.get_path()):
            gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogVideos.missing)

        else:

            position = video.get_position()
            if position >= 1 and replay:
                position = 0

            self.__media_player.set_video(video.get_path(),
                                          position,
                                          self.__current_media.playlist.get_subtitles_track(),
                                          self.__current_media.playlist.get_audio_track(),
                                          self.__current_media.playlist.get_start_at(),
                                          play)

            self.__media_player.set_random(self.__current_media.playlist.get_random())
            self.__media_player.set_keep_playing(self.__current_media.playlist.get_keep_playing())

    def __get_setting_playlist(self):
        if self.__new_playlist is not None:
            return self.__new_playlist

        return self.__selected_playlist

    def __save_current_video_position(self):
        if self.__current_media.playlist is not None:
            video = self.__current_media.current_video()
            if video is not None:
                position = self.__media_player.get_position()
                if position > 0:
                    video.set_position(position)

            self.__current_media.playlist.save()

    def __display_playlist_dialog(self, new_playlist=False):

        self.liststore_paths.clear()

        if new_playlist:
            playlist = Playlist()
            self.__new_playlist = playlist
            self.window_playlist_settings.set_title(Texts.WindowSettings.new_title)
            self.button_playlist_add.show()

        else:
            playlist = self.__selected_playlist
            self.__new_playlist = None
            self.window_playlist_settings.set_title(playlist.get_name() + " " + Texts.WindowSettings.edit_title)
            self.button_playlist_add.hide()
            self.liststore_paths.append([playlist.get_path(), playlist.get_recursive()])

        self.button_playlist_path_add.set_sensitive(new_playlist)
        self.button_playlist_path_remove.set_sensitive(False)
        self.button_playlist_path_edit.set_sensitive(not new_playlist)
        self.button_playlist_path_reload_all.set_sensitive(not new_playlist)

        self.entry_playlist_name.set_text(playlist.get_name())
        self.switch_setting_keep_playing.set_active(playlist.get_keep_playing())
        self.switch_setting_random_playing.set_active(playlist.get_random())

        pixbuf = Pixbuf.new_from_file_at_size(playlist.get_image_path(), -1, 30)
        self.image_playlist.set_from_pixbuf(pixbuf)
        self.button_playlist_delete.set_sensitive(not new_playlist)
        self.button_playlist_restart.set_sensitive(not new_playlist)

        self.__populating_settings = True
        self.spinbutton_audio.set_value(playlist.get_audio_track())
        self.spinbutton_subtitles.set_value(playlist.get_subtitles_track())
        self.spinbutton_start_at.set_value(playlist.get_start_at())
        self.__populating_settings = False

        self.window_playlist_settings.show()

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

        if os.path.exists(new_playlist.get_path()) or not self.checkbox_hide_missing_playlist.get_active():
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

            path = gtk_utils.gtk_dialog_select_file(self.window_root)

            if path is None:
                return

            found_videos = self.__selected_playlist.find_video(videos_id[0], path)
            gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogVideos.other_found.format(found_videos), None)

        else:

            path = gtk_utils.gtk_dialog_select_directory(self.window_root)

            if path is None:
                return

            found_videos = self.__selected_playlist.find_videos(path)
            gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogVideos.found_x.format(found_videos), None)

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

            if os.path.exists(playlist.get_path()) or not self.checkbox_hide_missing_playlist.get_active():
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


    def __menu_playlist_display(self, event):

        menu = Gtk.Menu()

        menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemPlaylist.settings)
        menu.append(menuitem)
        menuitem.connect('activate', self.__on_menuitem_playlist_settings)

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

    def __on_thread_scan_media_player(self):

        this_thread = current_thread()

        cached_video = None
        cached_position = 0

        while getattr(this_thread, "do_run", True):

            if self.__current_media.playlist is None:
                continue

            position = self.__media_player.get_position()
            current_video = self.__current_media.current_video()

            if current_video != cached_video:
                cached_video = current_video
                cached_position = 0

            if cached_video is None:
                continue

            if self.__media_player.is_paused() and position != cached_position:
                cached_position = position
                self.__current_media.playlist.set_video_position(cached_video, cached_position)

            if self.__media_player.get_random() != self.__current_media.playlist.get_random():
                self.__current_media.playlist.set_random(self.__media_player.get_random())
                self.__current_media.playlist.save()

            if self.__media_player.get_keep_playing() != self.__current_media.playlist.get_keep_playing():
                self.__current_media.playlist.set_keep_playing(self.__media_player.get_keep_playing())
                self.__current_media.playlist.save()

            # If the current video got to the end...
            if round(position, 3) >= 1:
                self.__current_media.set_video_position(1)

                # Update the treeview if the playlist is selected
                # if self.__selected_playlist.get_name() == self.__current_media.playlist.get_name():
                #    video_id = cached_video.get_id()
                #    for i in len(self.liststore_videos):
                #        if self.liststore_videos[i][VideosListstoreColumnsIndex.id] == video_id:
                #            self.liststore_videos[i][VideosListstoreColumnsIndex.progress] = 100
                #            break

                # Play the next video
                if not self.__current_media.playlist.get_keep_playing():
                    GLib.idle_add(self.__media_player.pause)
                    GLib.idle_add(self.window_root.unfullscreen)

                else:
                    next_video = self.__current_media.get_next_video()

                    if next_video is None:
                        GLib.idle_add(self.window_root.unfullscreen)
                        GLib.idle_add(gtk_utils.gtk_dialog_info, self.window_root,
                                      Texts.DialogPlaylist.all_videos_played)

                    else:
                        self.__media_player.set_video(next_video.get_path(),
                                                      next_video.get_position(),
                                                      self.__current_media.playlist.get_subtitles_track(),
                                                      self.__current_media.playlist.get_audio_track(),
                                                      self.__current_media.playlist.get_start_at(),
                                                      True)

            time.sleep(0.5)

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
                video.set_position(progress/100)

        self.__selected_playlist.save()

    def __on_menuitem_playlist_settings(self, *_):
        self.__display_playlist_dialog()

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

    def __on_menuitem_video_open_dir(self, _, path):
        if os.path.exists(path):
            open_directory(path)


def run():
    vlist_player = MainWindow()
    Gtk.main()
    vlist_player.join()
    VLC_INSTANCE.release()

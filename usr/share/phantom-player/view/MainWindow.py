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
from controller.CCParser import CCParser
from controller.factory import str_to_boolean
from model.CurrentMedia import CurrentMedia
from model.Series import Series, SeriesListStoreColumns
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

class MainWindow:

    def __init__(self, dark_mode=False):

        self.__populating_settings = False
        self.__selected_series = None
        self.__new_series = None
        self.__current_media = CurrentMedia()
        self.__is_full_screen = None
        self.__series_dict = {}
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
            'menuitem_series_settings',
            'box_window',
            'main_paned',
            'treeview_episodes',
            'treeview_series',
            'treeview_selection_series',
            'treeview_selection_episodes',
            'liststore_series',
            'liststore_episodes',
            'column_number',
            'column_name',
            'column_extension',
            'column_play',
            'column_oplayed',
            'column_rplayed',
            'checkbox_hidden_items',
            'checkbox_hide_extensions',
            'checkbox_hide_number',
            'checkbox_hide_name',
            'checkbox_hide_extension',
            'checkbox_hide_play',
            'checkbox_hide_oplayed',
            'checkbox_hide_rplayed',
            'checkbox_hide_warning_missing_series',
            'checkbox_hide_missing_series',

            'window_series_settings',
            'entry_series_name',
            'image_series',
            'spinbutton_subtitles',
            'spinbutton_start_at',
            'spinbutton_audio',
            'button_series_delete',
            'button_series_restart',
            'button_series_add',
            'liststore_paths',
            'button_series_path_add',
            'button_series_path_remove',
            'button_series_path_edit',
            'button_series_path_reload_all',

            'window_about',
        )

        if dark_mode:
            css_style = _DARK_CSS
        else:
            css_style = None


        for glade_id in glade_ids:
            setattr(self, glade_id, builder.get_object(glade_id))

        self.menubar.set_sensitive(False)
        self.treeview_series.set_sensitive(False)
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
        self.checkbox_hide_warning_missing_series.set_active(self.__ccp.get_bool('warningMissingSeries'))
        self.checkbox_hidden_items.set_active(self.__ccp.get_bool_defval('hidden', False))
        self.checkbox_hide_missing_series.set_active(self.__ccp.get_bool_defval('hide-missing-series', False))

        for item_name in ("hide_ep_number",
                          "hide_ep_name",
                          "hide_ep_extension",
                          "hide_ep_play",
                          "hide_ep_oplayed",
                          "hide_ep_rplayed"):

            if self.__ccp.get_bool(item_name):
                checkbox = getattr(self, item_name.replace("hide_ep_", "checkbox_hide_"))
                checkbox.set_active(True)

        #
        #    Display the window
        #
        self.menuitem_series_settings.set_sensitive(False)

        if dark_mode:
            gtk_utils.gtk_set_css(self.window_root, css_style)
            gtk_utils.gtk_set_css(self.treeview_episodes, css_style)
        

        self.window_root.maximize()
        self.window_root.show_all()
        self.__media_player.hide_volume_label()

        #
        #    Load the existent series
        #
        th = Thread(target=self.__on_thread_load_series)
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

    def on_treeview_series_press_event(self, _, event, inside_treeview=True):
        """
            Important: this method is triggered before "selection_changes".
        """

        #
        # Select the current series
        #
        if self.treeview_selection_series.count_selected_rows() <= 0:
            self.__selected_series = None
            return

        selected_series_name = gtk_utils.gtk_selection_get_first_selected_cell(self.treeview_selection_series, 1)
        self.__selected_series = self.__series_dict[selected_series_name]

        #
        # Process the events
        #
        if event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == EventCodes.Cursor.left_click:

                if self.__media_player.is_nothing():
                    self.__set_video(play=False, ignore_none=True)

            elif event.button == EventCodes.Cursor.right_click:

                # Get the iter where the user is pointing
                path = self.treeview_series.get_path_at_pos(event.x, event.y)

                if path is not None:
                    pointing_treepath = path[0]

                    # If the iter is not in the selected iters, remove the previous selection
                    model, treepaths = self.treeview_selection_series.get_selected_rows()

                    if pointing_treepath not in treepaths and inside_treeview:
                        self.treeview_selection_series.unselect_all()
                        self.treeview_selection_series.select_path(pointing_treepath)

                    self.__menu_series_display(event)

        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == EventCodes.Cursor.left_click:

                # check if the liststore is empty
                if len(self.liststore_episodes) <= 0:
                    if not self.checkbox_hide_warning_missing_series.get_active():
                        gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogSeries.is_missing)

                    return

                """
                    Check if the series is already selected and if a video is playing
                """
                if self.__current_media.is_series_name(selected_series_name):
                    if not self.__media_player.is_nothing():
                        if self.__media_player.is_paused():
                            self.__media_player.play()

                        return
                    else:
                        self.__save_current_video_position()

                """
                    Play a video of the series
                """
                self.__ccp.write('current_series', selected_series_name)
                self.__current_media = CurrentMedia(self.__selected_series)
                self.__set_video()

    def on_treeview_episodes_drag_end(self, *_):

        # Get the new order
        new_order = [row[0] for row in self.liststore_episodes]

        # Update the treeview
        for i, row in enumerate(self.liststore_episodes, 1):
            row[0] = i

        # Update the CSV file
        self.__selected_series.reorder(new_order)

    def on_treeview_episodes_press_event(self, _, event):
        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if len(treepaths) == 0:
            return

        selection_length = len(treepaths)

        if event.button == EventCodes.Cursor.left_click and \
                selection_length == 1 and \
                event.type == Gdk.EventType._2BUTTON_PRESS:

            """
                Play the video of the series
            """

            self.__ccp.write('current_series', self.__selected_series.get_name())

            self.__save_current_video_position()

            episode_name = gtk_utils.gtk_treepath_get_merged_cells(self.liststore_episodes, treepaths[0], 1, 2)

            self.__current_media = CurrentMedia(self.__selected_series)
            self.__set_video(episode_name)


        elif event.button == EventCodes.Cursor.right_click:

            # get the iter where the user is pointing
            try:
                pointing_treepath = self.treeview_episodes.get_path_at_pos(event.x, event.y)[0]
            except Exception:
                return

            # if the iter is not in the selected iters, remove the previous selection
            model, treepaths = self.treeview_selection_episodes.get_selected_rows()

            if pointing_treepath not in treepaths:
                self.treeview_selection_episodes.unselect_all()
                self.treeview_selection_episodes.select_path(pointing_treepath)

            menu = Gtk.Menu()

            """
                Open the containing folder (only if the user selected one video)
            """
            if selection_length == 1:

                selected_episode_name = gtk_utils.gtk_treepath_get_merged_cells(self.liststore_episodes,
                                                                                treepaths[0],
                                                                                SeriesListStoreColumns.name,
                                                                                SeriesListStoreColumns.ext)

                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemEpisodes.open_dir)
                menu.append(menuitem)
                menuitem.connect('activate', self.__on_menuitem_episode_open_dir, selected_episode_name)


            elif selection_length > 1:

                for column, label in ((SeriesListStoreColumns.play, Texts.MenuItemEpisodes.reproduce),
                                      (SeriesListStoreColumns.o_played, Texts.MenuItemEpisodes.o_played),
                                      (SeriesListStoreColumns.r_played, Texts.MenuItemEpisodes.r_played)):
                    # mark to check
                    menuitem = Gtk.ImageMenuItem(label=label + " - Check")
                    menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, column, True)

                    # mark to uncheck
                    menuitem = Gtk.ImageMenuItem(label=label + " - Un-check")
                    menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, column, False)

            """
                Menu "Fin videos"
            """
            list_of_names = [gtk_utils.gtk_treepath_get_merged_cells(self.liststore_episodes, treepath, 1, 2) for
                             treepath in
                             treepaths]

            if self.__selected_series.missing_videos(list_of_names):
                menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemEpisodes.search)
                menuitem.connect('activate', self.__series_find_videos, list_of_names)
                menu.append(menuitem)

            # ignore videos
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemEpisodes.ignore)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_ignore_episode)

            # don't ignore videos
            menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemEpisodes.dont_ignore)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_dont_ignore_episode)

            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)

            return True

    def on_treeview_selection_series_changed(self, treeselection):

        if treeselection.count_selected_rows() <= 0:
            self.__selected_series = None
            return

        selected_series_name = gtk_utils.gtk_selection_get_first_selected_cell(treeselection, 1)

        # This is because "press event" is executed before, so it is not necessary to re-define this
        if self.__selected_series is None or selected_series_name != self.__selected_series.get_name():
            self.__selected_series = self.__series_dict[selected_series_name]

        self.__liststore_episodes_populate()

    def on_cellrenderertoggle_play_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), SeriesListStoreColumns.play)

    def on_cellrenderertoggle_oplayed_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), SeriesListStoreColumns.o_played)

    def on_cellrenderertoggle_rplayed_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), SeriesListStoreColumns.r_played)

    def on_cellrenderertoggle_series_recursive_toggled(self, _, row):
        state = not self.liststore_paths[row][1]
        self.liststore_paths[row][1] = state
        series = self.__get_setting_series()
        series.set_recursive(state)
        if self.__new_series is None:
            series.save()

    def on_spinbutton_audio_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__selected_series.set_audio_track(value)

    def on_spinbutton_subtitles_value_changed(self, spinbutton):

        if self.__populating_settings:
            return

        value = spinbutton.get_value_as_int()
        self.__selected_series.set_subtitles_track(value)

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

        self.__selected_series.set_start_at(value)

    def on_checkbox_episodes_toggled(self, row, column):
        state = not self.liststore_episodes[row][column]
        self.liststore_episodes[row][column] = state
        episode_name = '{}{}'.format(self.liststore_episodes[row][1], self.liststore_episodes[row][2])
        self.__selected_series.change_checkbox_state(episode_name, column, state)

    def on_checkbox_hide_missing_series_toggled(self, *_):
        self.__ccp.write('hide-missing-series', self.checkbox_hide_missing_series.get_active())
        self.__liststore_series_populate()

    def on_checkbox_hide_number_toggled(self, *_):
        state = self.checkbox_hide_number.get_active()
        self.column_number.set_visible(not state)
        self.__ccp.write('hide_ep_number', state)

    def on_checkbox_hide_name_toggled(self, *_):
        state = self.checkbox_hide_name.get_active()
        self.column_name.set_visible(not state)
        self.__ccp.write('hide_ep_name', state)

    def on_checkbox_hide_extension_toggled(self, *_):
        state = self.checkbox_hide_extension.get_active()
        self.column_extension.set_visible(not state)
        self.__ccp.write('hide_ep_extension', state)

    def on_checkbox_hide_play_toggled(self, *_):
        state = self.checkbox_hide_play.get_active()
        self.column_play.set_visible(not state)
        self.__ccp.write('hide_ep_play', state)

    def on_checkbox_hide_oplayed_toggled(self, *_):
        state = self.checkbox_hide_oplayed.get_active()
        self.column_oplayed.set_visible(not state)
        self.__ccp.write('hide_ep_oplayed', state)

    def on_checkbox_hide_rplayed_toggled(self, *_):
        state = self.checkbox_hide_rplayed.get_active()
        self.column_rplayed.set_visible(not state)
        self.__ccp.write('hide_ep_rplayed', state)

    def on_checkbox_hide_warning_missing_series_toggled(self, *_):
        self.__ccp.write('warningMissingSeries', self.checkbox_hide_warning_missing_series.get_active())

    def on_checkbox_hidden_items_toggled(self, *_):
        self.__ccp.write('hide-items', self.checkbox_hidden_items.get_active())
        self.__liststore_episodes_populate()

    def on_menuitem_about_activate(self, *_):
        _ = self.window_about.run()
        self.window_about.hide()

    def on_menuitem_series_activate(self, *_):
        model, treepaths = self.treeview_selection_series.get_selected_rows()
        self.menuitem_series_settings.set_sensitive(len(treepaths) > 0)

    def on_menuitem_series_new_activate(self, *_):
        self.__display_settings_window(new_series=True)

    def on_menuitem_series_settings_activate(self, *_):
        self.__display_settings_window()

    def on_menuitem_checkbox_activated(self, _, column, state):

        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if len(treepaths) == 0:
            return

        episode_names = []
        for treepath in treepaths:
            episode_name = gtk_utils.gtk_treepath_get_merged_cells(self.liststore_episodes, treepath, 1, 2)
            self.liststore_episodes[treepath][column] = state
            episode_names.append(episode_name)

        self.__selected_series.change_checkbox_state(episode_names, column, state)

        self.__liststore_episodes_populate()

    def on_button_series_delete_clicked(self, *_):

        series_name = self.__selected_series.get_name()

        if not gtk_utils.gtk_dialog_question(self.window_series_settings,
                                             Texts.DialogSeries.confirm_delete.format(series_name)):
            return

        gtk_utils.gtk_liststore_remove_first_selected_row(self.treeview_selection_series)

        if len(self.liststore_series) > 0:
            self.treeview_series.set_cursor(0)
        else:
            self.liststore_episodes.clear()

        self.window_series_settings.hide()

        if self.__current_media.is_series_name(series_name):
            self.__media_player.stop()
            self.__current_media = CurrentMedia()

        series = self.__series_dict[series_name]
        self.__series_dict.pop(series_name)

        if os.path.exists(series.get_save_path()):
            os.remove(series.get_save_path())

    def on_button_series_add_clicked(self, *_):

        series_name = self.entry_series_name.get_text().strip()

        if series_name == "":
            gtk_utils.gtk_dialog_info(self.window_series_settings, Texts.WindowSettings.series_name_empty)
            return

        elif series_name in self.__series_dict.keys():
            gtk_utils.gtk_dialog_info(self.window_series_settings,
                                      Texts.DialogSeries.name_exist.format(series_name))
            return

        self.__new_series.rename(series_name)
        self.__new_series.save()
        self.__series_dict[series_name] = self.__new_series

        if os.path.exists(self.__new_series.get_path()) or not self.checkbox_hide_missing_series.get_active():
            pixbuf = Pixbuf.new_from_file_at_size(self.__new_series.get_image_path(), -1, 30)
            self.__liststore_series_append([pixbuf, self.__new_series.get_name()])

            for i, row in enumerate(self.liststore_series):
                if row[1] == series_name:
                    self.treeview_series.set_cursor(i)
                    break

        self.__new_series = None
        self.window_series_settings.hide()

    def on_button_series_close(self, *_):

        if self.__new_series is not None:
            self.__new_series = None

        else:
            new_name = self.entry_series_name.get_text().strip()

            if self.__selected_series.get_name() == new_name:
                pass

            elif new_name == "":
                gtk_utils.gtk_dialog_info(self.window_series_settings, Texts.WindowSettings.series_name_empty)
                return

            elif new_name in self.__series_dict.keys():
                gtk_utils.gtk_dialog_info(self.window_series_settings, Texts.DialogSeries.name_exist.format(new_name))
                return

            else:
                self.__series_dict.pop(self.__selected_series.get_name())
                self.__selected_series.rename(new_name)
                self.__series_dict[new_name] = self.__selected_series
                gtk_utils.gtk_selection_set_first_selected_cell(self.treeview_selection_series, 1, new_name)

        self.window_series_settings.hide()

    def on_button_series_restart_clicked(self, *_):

        selected_series_name = self.__selected_series.get_name()

        if not gtk_utils.gtk_dialog_question(self.window_series_settings,
                                             Texts.DialogSeries.confirm_reset.format(selected_series_name)):
            return

        self.window_series_settings.hide()

        # This is done before to avoid updating the series data
        was_playing = False
        if self.__current_media.is_series_name(selected_series_name):
            if self.__media_player.is_playing():
                was_playing = True
                self.__media_player.pause()

        series = self.__series_dict[selected_series_name]
        series.restart()
        self.__liststore_episodes_populate()

        if was_playing:
            self.__set_video()

    def on_button_series_set_image_clicked(self, *_):
        """
            Add a picture to a series
        """
        file_filter = Gtk.FileFilter()
        file_filter.set_name('Image')
        file_filter.add_pattern('*.jpeg')
        file_filter.add_pattern('*.jpg')
        file_filter.add_pattern('*.png')

        file = gtk_utils.gtk_dialog_folder(self.window_series_settings, file_filter)
        if file is not None:

            setting_series = self.__get_setting_series()
            setting_series.set_image_path(file)

            pixbuf = Pixbuf.new_from_file_at_size(file, -1, 30)
            self.image_series.set_from_pixbuf(pixbuf)

            if self.__new_series is None:
                gtk_utils.gtk_selection_set_first_selected_cell(self.treeview_selection_series,
                                                                0,
                                                                pixbuf)

    def on_button_series_path_add_clicked(self, *_):

        path = gtk_utils.gtk_dialog_file(self.window_root)
        if path is None:
            return

        series = self.__get_setting_series()
        series.set_path(path)
        series.save()

        self.liststore_paths.clear()
        self.liststore_paths.append([path, False])

        series.load_videos()

        self.button_series_path_add.set_sensitive(False)
        self.button_series_path_edit.set_sensitive(True)
        self.button_series_path_reload_all.set_sensitive(True)

    def on_button_series_path_remove_clicked(self, *_):
        pass

    def on_button_series_path_edit_clicked(self, *_):

        path = gtk_utils.gtk_dialog_file(self.window_root)
        if path is None:
            return

        self.liststore_paths.clear()
        self.liststore_paths.append([path, False])

        series = self.__get_setting_series()
        series.set_path(path)
        series.save()
        series.load_videos()

        if self.__new_series is None:
            self.__liststore_episodes_populate()

    def on_button_series_path_reload_all_clicked(self, *_):
        series = self.__get_setting_series()
        series.load_videos()

        if self.__new_series is None:
            self.__liststore_episodes_populate()

    def __set_video(self, video_name=None, play=True, replay=False, ignore_none=False):

        if self.__current_media.series is None:
            return

        if video_name is None:
            video = self.__current_media.get_next_episode()
        else:
            video = self.__current_media.get_episode(video_name)

        if video is None:
            if not ignore_none:
                gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogSeries.all_episodes_played)

        elif not os.path.exists(video.get_path()):
            gtk_utils.gtk_dialog_info(self.window_root, Texts.DialogEpisodes.missing)

        else:

            position = video.get_position()
            if position >= .999 and replay:
                position = 0

            self.__media_player.set_video(video.get_path(),
                                          position,
                                          self.__current_media.series.get_subtitles_track(),
                                          self.__current_media.series.get_audio_track(),
                                          self.__current_media.series.get_start_at(),
                                          play)

            self.__media_player.set_random(self.__current_media.series.get_random())
            self.__media_player.set_keep_playing(self.__current_media.series.get_keep_playing())

    def __get_setting_series(self):
        if self.__new_series is not None:
            return self.__new_series

        return self.__selected_series

    def __save_current_video_position(self):
        if self.__current_media.series is not None:
            episode = self.__current_media.current_episode()
            if episode is not None:
                position = self.__media_player.get_position()
                if position > 0:
                    episode.set_position(position)

            self.__current_media.series.save()

    def __display_settings_window(self, new_series=False):

        self.liststore_paths.clear()

        if new_series:
            series = Series()
            self.__new_series = series
            self.window_series_settings.set_title(Texts.WindowSettings.new_title)
            self.button_series_add.show()

        else:
            series = self.__selected_series
            self.__new_series = None
            self.window_series_settings.set_title(series.get_name() + " " + Texts.WindowSettings.edit_title)
            self.button_series_add.hide()
            self.liststore_paths.append([series.get_path(), series.get_recursive()])

        self.button_series_path_add.set_sensitive(new_series)
        self.button_series_path_remove.set_sensitive(False)
        self.button_series_path_edit.set_sensitive(not new_series)
        self.button_series_path_reload_all.set_sensitive(not new_series)

        self.entry_series_name.set_text(series.get_name())

        pixbuf = Pixbuf.new_from_file_at_size(series.get_image_path(), -1, 30)
        self.image_series.set_from_pixbuf(pixbuf)
        self.button_series_delete.set_sensitive(not new_series)
        self.button_series_restart.set_sensitive(not new_series)

        self.__populating_settings = True
        self.spinbutton_audio.set_value(series.get_audio_track())
        self.spinbutton_subtitles.set_value(series.get_subtitles_track())
        self.spinbutton_start_at.set_value(series.get_start_at())
        self.__populating_settings = False

        self.window_series_settings.show()

    def __series_load_from_path(self,
                                name,
                                data_path,
                                recursive,
                                random,
                                keep_playing,
                                start_at=0.0,
                                audio_track=-2,
                                subtitles_track=-2,
                                select=True):

        new_series = Series(name,
                            data_path,
                            recursive,
                            random,
                            keep_playing,
                            start_at,
                            audio_track,
                            subtitles_track)

        self.__series_dict[new_series.get_name()] = new_series

        if os.path.exists(new_series.get_path()) or not self.checkbox_hide_missing_series.get_active():
            pixbuf = Pixbuf.new_from_file_at_size(new_series.get_image_path(), -1, 30)
            GLib.idle_add(self.__liststore_series_append, (pixbuf, new_series.get_name()))

        if select:  # select the row once the series has been added

            new_series.load_videos()

            for i, row in enumerate(self.liststore_series):
                if row[1] == new_series.get_name():
                    GLib.idle_add(self.treeview_series.set_cursor, i)
                    break

    """
    def __series_find_videos(self, _, video_names):

        path = gtk_dialog_folder(self.window_root)

        if path is None:
            return

        if len(video_names) == 1:  # if the user only selected one video to find...
            found_videos = series_data.find_video(video_names[0], path)
            if found_videos:
                gtk_dialog_info(self.window_root, Texts.DialogEpisodes.other_found.format(found_videos), None)

        elif len(video_names) > 1:
            found_videos = self.__selected_series.find_videos(path)

            if found_videos:
                gtk_dialog_info(self.window_root, Texts.DialogEpisodes.found_x.format(found_videos), None)

        self.__liststore_episodes_populate()
    """

    def __liststore_series_append(self, data):
        """
            I do not understand why this must be a separate method.
            It is not possible to call directly: GLib.idle_add(self.liststore_series.append, data)
        """
        self.liststore_series.append(data)

    def __liststore_series_populate(self):

        # Populate
        #
        self.liststore_series.clear()

        for name in sorted(self.__series_dict.keys()):
            series = self.__series_dict[name]

            if os.path.exists(series.get_path()) or not self.checkbox_hide_missing_series.get_active():
                self.liststore_series.append([series.get_image(), series.get_name()])

        # Select the current series
        #
        current_series_name = self.__ccp.get_str('current_series')

        for i, row in enumerate(self.liststore_series):
            if row[1] == current_series_name:
                self.treeview_series.set_cursor(i)
                return

        self.treeview_series.set_cursor(0)

    def __liststore_episodes_mark(self, episode_name, random):

        if random:
            column = 6
        else:
            column = 5

        for i, (_, e_name, *_) in enumerate(self.liststore_episodes):
            if episode_name == e_name:
                self.liststore_episodes[i][column] = True
                return

    def __liststore_episodes_populate(self):

        if self.__selected_series is None:
            return

        self.liststore_episodes.clear()
        self.column_name.set_spacing(0)

        if not os.path.exists(self.__selected_series.get_path()):
            return

        # initialize the list
        videos_list = []
        for _ in self.__selected_series.get_videos():
            videos_list.append(None)

        # sort it by id
        for video in self.__selected_series.get_videos():
            try:
                videos_list[video.get_id() - 1] = video
            except Exception as e:
                print(str(e))

        _, default_color = gtk_utils.gtk_default_font_color('theme_text_color',
                                                            widget=self.treeview_episodes,
                                                            on_error="#000000")

        _, hide_color = gtk_utils.gtk_default_font_color('warning_color',
                                                         widget=self.treeview_episodes,
                                                         on_error="#ff9900")

        _, error_color = gtk_utils.gtk_default_font_color('error_color',
                                                         widget=self.treeview_episodes,
                                                         on_error="#ff0000")

        _, new_color = gtk_utils.gtk_default_font_color('success_color',
                                                         widget=self.treeview_episodes,
                                                         on_error="#009933")

        for video in videos_list:
            if video:

                if not video.get_display():
                    color = hide_color

                elif video.get_is_new():
                    color = new_color

                elif not video.exists():
                    color = error_color

                else:
                    color = default_color



                # add the video to the list store
                if video.get_display() or not self.checkbox_hidden_items.get_active():
                    self.liststore_episodes.append([video.get_id(),
                                                    video.get_empty_name(),
                                                    video.get_extension(),
                                                    video.get_play(),
                                                    video.get_o_played(),
                                                    video.get_r_played(),
                                                    color])
            else:
                print("Error loading the liststore_episodes. The series '{}' has an empty video.".format(
                    self.__selected_series.get_name()))

    def __menu_series_display(self, event):

        menu = Gtk.Menu()

        menuitem = Gtk.ImageMenuItem(label=Texts.MenuItemSeries.settings)
        menu.append(menuitem)
        menuitem.connect('activate', self.__on_menuitem_series_settings)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

        return True

    def __on_thread_load_series(self):

        #
        # Load the files header
        #
        if os.path.exists(FOLDER_LIST_PATH):
            for file_name in sorted(os.listdir(FOLDER_LIST_PATH)):

                if not file_name.lower().endswith('.csv'):
                    continue

                file_path = os.path.join(FOLDER_LIST_PATH, file_name)

                with open(file_path, mode='rt', encoding='utf-8') as f:
                    series_header = f.readline().split('|')
                    series_path = f.readline().split('|')

                if len(series_header) != 5 or len(series_path) != 2:
                    print("Error, Wrong format for series file = ", file_path)  # todo: show user message
                    continue

                data_path = series_path[0].strip()
                recursive = str_to_boolean(series_path[1])

                random = str_to_boolean(series_header[0])
                keep_playing = str_to_boolean(series_header[1])
                start_at = float(series_header[2])
                audio_track = int(series_header[3])
                subtitles_track = int(series_header[4])

                self.__series_load_from_path(file_name,
                                             data_path,
                                             recursive,
                                             random,
                                             keep_playing,
                                             start_at,
                                             audio_track,
                                             subtitles_track,
                                             select=False)

        #
        #   Select & Load the last series that was played
        #
        current_series_name = self.__ccp.get_str('current_series')

        try:
            series_data = self.__series_dict[current_series_name]
        except KeyError:
            series_data = None
        else:
            series_data.load_videos()
            self.__current_media = CurrentMedia(series_data)

        series_found = False
        for i, row in enumerate(self.liststore_series):
            if row[1] == current_series_name:
                GLib.idle_add(self.treeview_series.set_cursor, i)
                series_found = True

        #
        #   Load the rest of the videos
        #
        for series in self.__series_dict.values():
            if series != series_data:
                series.load_videos()

        #
        #   Select a default series if none
        #
        if not series_found:
            GLib.idle_add(self.treeview_series.set_cursor, 0)
            GLib.idle_add(self.window_root.set_sensitive, True)

        #
        #   Enable the GUI
        #
        default_cursor = Gdk.Cursor.new_from_name(self.window_root.get_display(), 'default')
        GLib.idle_add(self.window_root.get_root_window().set_cursor, default_cursor)
        GLib.idle_add(self.treeview_series.set_sensitive, True)
        GLib.idle_add(self.menubar.set_sensitive, True)

    def __on_thread_scan_media_player(self):

        this_thread = current_thread()

        cached_video = None
        cached_position = 0

        while getattr(this_thread, "do_run", True):

            if self.__current_media.series is None:
                continue

            position = self.__media_player.get_position()
            current_episode = self.__current_media.current_episode()

            if current_episode != cached_video:
                cached_video = current_episode
                cached_position = 0

            if cached_video is None:
                continue

            if self.__media_player.is_paused() and position != cached_position:
                cached_position = position
                self.__current_media.series.set_video_position(cached_video, cached_position)

            if self.__media_player.get_random() != self.__current_media.series.get_random():
                self.__current_media.series.set_random(self.__media_player.get_random())
                self.__current_media.series.save()

            if self.__media_player.get_keep_playing() != self.__current_media.series.get_keep_playing():
                self.__current_media.series.set_keep_playing(self.__media_player.get_keep_playing())
                self.__current_media.series.save()

            # If the current video got to the end...
            if round(position, 3) >= 0.999:
                self.__current_media.mark_seen_episode()

                # Update the treeview if the series is selected
                if self.__selected_series.get_name() == self.__current_media.series.get_name():
                    GLib.idle_add(self.__liststore_episodes_mark,
                                  cached_video.get_empty_name(),
                                  self.__current_media.series.get_random())

                # Play the next episode
                if not self.__current_media.series.get_keep_playing():
                    GLib.idle_add(self.__media_player.pause)
                    GLib.idle_add(self.window_root.unfullscreen)

                else:
                    next_video = self.__current_media.get_next_episode()

                    if next_video is None:
                        GLib.idle_add(self.window_root.unfullscreen)
                        GLib.idle_add(gtk_utils.gtk_dialog_info, self.window_root,
                                      Texts.DialogSeries.all_episodes_played)

                    else:
                        self.__media_player.set_video(next_video.get_path(),
                                                      next_video.get_position(),
                                                      self.__current_media.series.get_subtitles_track(),
                                                      self.__current_media.series.get_audio_track(),
                                                      self.__current_media.series.get_start_at(),
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

    def __on_menuitem_series_settings(self, *_):
        self.__display_settings_window()

    """
    def __on_menuitem_series_find(self, _):

        path = gtk_dialog_file(self.window_root)
        if path is None:
            return

        self.__selected_series.find_series(path)
        gtk_selection_set_first_selected_cell(self.treeview_selection_series, 0, self.__selected_series.get_image())
        self.__liststore_episodes_populate()
        
    """

    def __on_menuitem_series_ignore_episode(self, _):

        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if not treepaths == []:
            for treepath in treepaths:
                episode_name = gtk_utils.gtk_treepath_get_merged_cells(self.liststore_episodes,
                                                                       treepath,
                                                                       1,
                                                                       2)
                self.__selected_series.ignore_video(episode_name)

            self.__liststore_episodes_populate()

    def __on_menuitem_series_dont_ignore_episode(self, _):

        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if not treepaths == []:
            for treepath in treepaths:
                episode_name = gtk_utils.gtk_treepath_get_merged_cells(self.liststore_episodes,
                                                                       treepath,
                                                                       1,
                                                                       2)
                self.__selected_series.dont_ignore_video(episode_name)

            self.__liststore_episodes_populate()

    def __on_menuitem_episode_open_dir(self, _, video_name):
        path = self.__selected_series.get_path_from_video_name(video_name)
        if os.path.exists(path):
            open_directory(path)


def run():
    vlist_player = MainWindow()
    Gtk.main()
    vlist_player.join()
    VLC_INSTANCE.release()
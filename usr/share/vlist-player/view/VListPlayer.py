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
import webbrowser
from threading import Thread, current_thread

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk, GObject, GLib

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from Paths import *
from Texts import *
from view.gtk_utils import *
from model.Series import Series
from controller.CCParser import CCParser
from model.CurrentMedia import CurrentMedia
from system_utils import EventCodes, open_directory
from view.MediaPlayer import MediaPlayerWidget, VLC_INSTANCE


def gtk_file_chooser(parent, mode='', start_path=''):
    window_choose_file = Gtk.FileChooserDialog(TEXT_PROGRAM_NAME,
                                               parent,
                                               Gtk.FileChooserAction.OPEN,
                                               (Gtk.STOCK_CANCEL,
                                                Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN,
                                                Gtk.ResponseType.OK))

    window_choose_file.set_default_response(Gtk.ResponseType.NONE)
    window_choose_file.set_icon_from_file(ICON_LOGO_SMALL)

    window_choose_file.set_transient_for(parent)

    if mode == 'picture':
        file_filter = Gtk.FileFilter()
        file_filter.set_name('Picture')
        file_filter.add_pattern('*.jpeg')
        file_filter.add_pattern('*.jpg')
        file_filter.add_pattern('*.png')
        window_choose_file.add_filter(file_filter)

    if start_path == '':
        window_choose_file.set_current_folder(HOME_PATH)
    else:
        window_choose_file.set_current_folder(start_path)

    response = window_choose_file.run()
    if response == Gtk.ResponseType.OK:
        file_path = window_choose_file.get_filename()
    else:
        file_path = None
    window_choose_file.destroy()

    return file_path


class VListPlayer(object):

    def __init__(self):

        self.__is_full_screen = None
        self.__series_dict = {}
        self.__threads = []

        self.__ccp = CCParser(CONFIGURATION_FILE, 'vlist-player')

        """
            load items from glade
        """
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "vlist-player.glade"))
        builder.connect_signals(self)

        glade_ids = (
            'window_root', 'box_window',
            'menubar',
            'box_window',
            'box_main',
            'treeview_selection_episodes', 'progressbar', 'checkbox_hidden_items',
            'button_root_play_and_stop', 'treeview_episodes', 'treeview_series',
            'treeview_selection_series', 'liststore_series', 'liststore_episodes', 'spinbutton_audio',
            'spinbutton_subtitles',
            'spinbutton_start_at', 'box_episodes', 'box_series', 'box_series_data',
            'box_series_menu', 'column_number', 'column_name', 'column_extension', 'column_play',
            'column_oplayed',
            'column_rplayed', 'checkbutton_random', 'checkbutton_keep_playing', 'checkbox_hide_extensions',
            'checkbox_hide_number',
            'checkbox_hide_name', 'checkbox_hide_extension', 'checkbox_hide_play', 'checkbox_hide_oplayed',
            'checkbox_hide_rplayed',
            'checkbox_hide_warning_missing_series', 'checkbox_hide_missing_series',

            'window_rename',
            'entry_rename', 'label_old_name',

            'window_about',
            'window_controls',
            'window_files',
            'window_preferences',
            'window_finding_files',
        )

        for glade_id in glade_ids:
            setattr(self, glade_id, builder.get_object(glade_id))

        """
            Media Player
        """
        self.__current_media = CurrentMedia()
        self.__media_player = MediaPlayerWidget(self.window_root)

        paned = Gtk.Paned(orientation=Gtk.Orientation.VERTICAL)
        paned.set_wide_handle(True)
        paned.set_position(200)
        paned.add1(self.__media_player)
        self.box_window.remove(self.box_main)
        paned.add2(self.box_main)
        self.box_window.pack_start(paned, True, True, 0)

        self.__thread_scan_media_player = Thread(target=self.__on_thread_scan_media_player)
        self.__thread_scan_media_player.start()

        """
            configuration
        """

        # font colors
        color = Gdk.RGBA()
        color.parse(gtk_default_font_color())
        color.to_string()
        self.__default_font_color = color

        color = Gdk.RGBA()
        color.parse('#FF0000')
        color.to_string()
        self.__hidden_font_color = color

        # extra
        self.window_root.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.window_root.connect('delete-event', self.quit)
        self.window_root.connect("configure-event", self.__on_configure_event)

        # checkboxes
        self.checkbox_hide_number.set_active(self.__ccp.get_bool('number'))
        self.checkbox_hide_name.set_active(self.__ccp.get_bool('name'))
        self.checkbox_hide_extension.set_active(self.__ccp.get_bool('extensions'))
        self.checkbox_hide_play.set_active(self.__ccp.get_bool('play'))
        self.checkbox_hide_oplayed.set_active(self.__ccp.get_bool('oplayed'))
        self.checkbox_hide_rplayed.set_active(self.__ccp.get_bool('rplayed'))
        self.checkbox_hide_warning_missing_series.set_active(self.__ccp.get_bool('warningMissingSeries'))
        self.checkbox_hidden_items.set_active(self.__ccp.get_bool_defval('hidden', False))
        self.checkbox_hide_missing_series.set_active(self.__ccp.get_bool_defval('hide-missing-series', False))

        """
            Display the window
        """
        self.window_root.maximize()
        self.window_root.show_all()
        self.__media_player.hide_controls()

        """
            Load the existent series
        """
        th = Thread(target=self.__on_thread_load_series)
        th.start()
        self.__threads.append(th)

    def join(self):
        for th in self.__threads:
            th.join()

        self.__thread_scan_media_player.join()
        self.__media_player.join()

    def __save_current_video_position(self):
        if self.__current_media.series is not None:
            episode = self.__current_media.current_episode()
            if episode is not None:
                position = self.__media_player.get_position()
                if position > 0:
                    episode.set_position(position)

            self.__current_media.series.write_data()

    def quit(self, *_):
        self.__save_current_video_position()
        self.__media_player.quit()
        self.__thread_scan_media_player.do_run = False
        Gtk.main_quit()

    def on_treeview_episodes_drag_end(self, *_):

        # Get the new order
        new_order = [row[0] for row in self.liststore_episodes]

        # Update the treeview
        for i, row in enumerate(self.liststore_episodes, 1):
            row[0] = i

            # Update the CSV file
        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series = self.__series_dict[selected_series_name]
        series.reorder(new_order)

    def on_treeview_series_press_event(self, _, event, inside_treeview=True):

        # check if some row is selected
        if self.treeview_selection_series.count_selected_rows() <= 0:
            return

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series_data = self.__series_dict[selected_series_name]

        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == EventCodes.Cursor.left_click:

                # check if the liststore is empty
                if len(self.liststore_episodes) <= 0 and not self.checkbox_hide_warning_missing_series.get_active():
                    gtk_info(self.window_root, TEXT_CANT_PLAY_SERIES_MISSING, None)
                    return

                """
                    Play a video of the series
                """
                if self.__current_media.series is not None:

                    if self.__current_media.series.get_name() == selected_series_name:
                        return

                    self.__save_current_video_position()

                self.__ccp.write('current_series', selected_series_name)
                self.__current_media = CurrentMedia(series_data)
                self.__set_video()

        elif event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == EventCodes.Cursor.right_click and self.treeview_selection_series.count_selected_rows() == 1:

                # Get the iter where the user is pointing
                pointing_treepath = self.treeview_series.get_path_at_pos(event.x, event.y)[0]

                # If the iter is not in the selected iters, remove the previous selection
                model, treepaths = self.treeview_selection_series.get_selected_rows()

                if pointing_treepath not in treepaths and inside_treeview:
                    self.treeview_selection_series.unselect_all()
                    self.treeview_selection_series.select_path(pointing_treepath)

                self.__menu_series_display(series_data, event)

    def __set_video(self, video_name=None, play=True):

        if self.__current_media.series is None:
            return

        if video_name is None:
            video = self.__current_media.next_episode(self.checkbutton_random.get_active())
        else:
            video = self.__current_media.get_episode(video_name)

        if video is None:
            gtk_info(self.window_root, TEXT_END_OF_SERIES)

        elif not os.path.exists(video.get_path()):
            gtk_info(self.window_root, TEXT_CANT_PLAY_MEDIA_MISSING)

        else:
            self.__media_player.set_video(video.get_path(),
                                          video.get_position(),
                                          self.__current_media.series.get_subtitles_track(),
                                          self.__current_media.series.get_audio_track(),
                                          self.__current_media.series.get_start_at(),
                                          play)

    def on_treeview_episodes_press_event(self, _, event):
        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if len(treepaths) == 0:
            return

        selection_length = len(treepaths)

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series_data = self.__series_dict[selected_series_name]

        """
            Active or deactivate the buttons move up and down
        """

        if event.button == EventCodes.Cursor.left_click and \
                selection_length == 1 and \
                event.type == Gdk.EventType._2BUTTON_PRESS:

            """
                Play the video of the series
            """

            self.__ccp.write('current_series', selected_series_name)

            if self.__current_media.series is not None:
                self.__save_current_video_position()

            episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepaths[0], 1, 2)

            self.__current_media = CurrentMedia(series_data)
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

                selected_episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepaths[0], 1, 2)

                menuitem = Gtk.ImageMenuItem(label=TEXT_FOLDER)
                menu.append(menuitem)
                menuitem.connect('activate', self.__menuitem_episode_open_dir, selected_episode_name)
                img = Gtk.Image(stock=Gtk.STOCK_OPEN)
                menuitem.set_image(img)


            elif selection_length > 1:

                for i, label in enumerate((TEXT_PLAY, TEXT_O_PLAYED, TEXT_R_PLAYED), 4):
                    # mark to check
                    menuitem = Gtk.ImageMenuItem(label=label)
                    menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, i, True)
                    img = Gtk.Image(stock=Gtk.STOCK_APPLY)
                    menuitem.set_image(img)

                    # mark to uncheck
                    menuitem = Gtk.ImageMenuItem(label=label)
                    menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, i, False)
                    img = Gtk.Image(stock=Gtk.STOCK_MISSING_IMAGE)
                    menuitem.set_image(img)

            """
                Menu "Fin videos"
            """
            list_of_names = [gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2) for treepath in
                             treepaths]

            if series_data.missing_videos(list_of_names):
                menuitem = Gtk.ImageMenuItem(label=TEXT_FIND)
                menuitem.connect('activate', self.__series_find_videos, list_of_names)
                menu.append(menuitem)
                img = Gtk.Image(stock=Gtk.STOCK_DIALOG_WARNING)
                menuitem.set_image(img)

            # ignore videos
            menuitem = Gtk.ImageMenuItem(label=TEXT_IGNORE)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_ignore_episode)
            img = Gtk.Image(stock=Gtk.STOCK_FIND_AND_REPLACE)
            menuitem.set_image(img)

            # don't ignore videos
            menuitem = Gtk.ImageMenuItem(label=TEXT_DONT_IGNORE)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_dont_ignore_episode)
            img = Gtk.Image(stock=Gtk.STOCK_FIND)
            menuitem.set_image(img)

            menu.show_all()
            menu.popup(None, None, None, None, event.button, event.time)

            return True

    def on_treeview_selection_series_changed(self, treeselection):
        if treeselection.count_selected_rows() > 0:
            self.__liststore_episodes_populate(True)

    def on_cellrenderertoggle_play_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), 4)

    def on_cellrenderertoggle_oplayed_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), 5)

    def on_cellrenderertoggle_rplayed_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), 6)

    def on_spinbutton_audio_value_changed(self, spinbutton):
        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        value = spinbutton.get_value_as_int()

        self.__series_dict[series_name].set_audio_track(value)

    def on_spinbutton_subtitles_value_changed(self, spinbutton):

        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        value = spinbutton.get_value_as_int()

        self.__series_dict[series_name].set_subtitles_track(value)

    def on_spinbutton_start_at_value_changed(self, spinbutton):

        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        value = float(spinbutton.get_value())

        str_value = str(value).split('.')
        minutes = int(str_value[0])
        seconds = int(str_value[1])
        if seconds > 60:
            minutes += 1
            spinbutton.set_value(minutes + 0.00)

        self.__series_dict[series_name].set_start_at(value)

    def on_checkbutton_random_toggled(self, radiobutton, *_):
        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        radiobutton_state = radiobutton.get_active()
        self.__series_dict[series_name].set_random(radiobutton_state)
        self.__liststore_episodes_populate(False)

    def on_checkbutton_keep_playing_toggled(self, radiobutton, *_):
        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        radiobutton_state = radiobutton.get_active()
        self.__series_dict[series_name].set_keep_playing(radiobutton_state)

    def on_checkbox_episodes_toggled(self, row, column):

        state = not self.liststore_episodes[row][column]

        self.liststore_episodes[row][column] = state

        series = self.__series_dict[
            gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        episode_name = '{}{}'.format(self.liststore_episodes[row][1], self.liststore_episodes[row][2])

        series.change_checkbox_state(episode_name, column, state)

        self.__liststore_episodes_populate(False)

    def on_checkbox_hide_missing_series_toggled(self, *_):
        self.__ccp.write('hide-missing-series', self.checkbox_hide_missing_series.get_active())
        self.__liststore_series_populate()

    def on_checkbox_hide_number_toggled(self, *_):
        state = self.checkbox_hide_number.get_active()
        self.column_number.set_visible(not state)
        self.__ccp.write('number', state)

    def on_checkbox_hide_name_toggled(self, *_):
        state = self.checkbox_hide_name.get_active()
        self.column_name.set_visible(not state)
        self.__ccp.write('name', state)

    def on_checkbox_hide_extension_toggled(self, *_):
        state = self.checkbox_hide_extension.get_active()
        self.column_extension.set_visible(not state)
        self.__ccp.write('extensions', state)

    def on_checkbox_hide_play_toggled(self, *_):
        state = self.checkbox_hide_play.get_active()
        self.column_play.set_visible(not state)
        self.__ccp.write('play', state)

    def on_checkbox_hide_oplayed_toggled(self, *_):
        state = self.checkbox_hide_oplayed.get_active()
        self.column_oplayed.set_visible(not state)
        self.__ccp.write('oplayed', state)

    def on_checkbox_hide_rplayed_toggled(self, *_):
        state = self.checkbox_hide_rplayed.get_active()
        self.column_rplayed.set_visible(not state)
        self.__ccp.write('rplayed', state)

    def on_checkbox_hide_warning_missing_series_toggled(self, *_):
        self.__ccp.write('warningMissingSeries', self.checkbox_hide_warning_missing_series.get_active())

    def on_checkbox_hidden_items_toggled(self, *_):
        self.__ccp.write('hide-items', self.checkbox_hidden_items.get_active())
        self.__liststore_episodes_populate(True)

    def on_menuitem_about_activate(self, *_):
        _ = self.window_about.run()
        self.window_about.hide()

    @staticmethod
    def on_menuitem_issues_activate(*_):
        webbrowser.open('https://github.com/rsm-gh/vlist-player/issues', new=2)

    def on_menuitem_controls_activate(self, *_):
        self.window_controls.show()

    def on_menuitem_finding_activate(self, *_):
        self.window_finding_files.show()

    def on_menuitem_files_activate(self, *_):
        self.window_files.show()

    def on_imagemenuitem_preferences_activate(self, *_):
        self.window_preferences.show()

    def on_menuitem_list_activate(self, *_):
        self.__series_add_from_fchooser(False)

    def on_menuitem_list_recursive_activate(self, *_):
        self.__series_add_from_fchooser(True)

    def on_menuitem_checkbox_activated(self, _, column, state):

        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if len(treepaths) == 0:
            return

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series_data = self.__series_dict[selected_series_name]

        episode_names = []
        for treepath in treepaths:
            episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
            self.liststore_episodes[treepath][column] = state
            episode_names.append(episode_name)

        series_data.change_checkbox_state(episode_names, column, state)

        self.__liststore_episodes_populate(True)

    def on_button_cancel_rename_clicked(self, *_):
        self.window_rename.hide()

    def on_button_close_preferences_clicked(self, *_):
        self.window_preferences.hide()

    def on_button_close_controls_clicked(self, *_):
        self.window_controls.hide()

    def on_button_close_files_clicked(self, *_):
        self.window_files.hide()

    def on_button_close_window_list_clicked(self, *_):
        self.window_list.hide()

    def on_button_close_find_files_clicked(self, *_):
        self.window_finding_files.hide()

    def on_button_okay_rename_clicked(self, *_):

        current_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        new_name = self.entry_rename.get_text()

        if new_name in self.__series_dict.keys():
            gtk_info(self.window_rename, TEXT_SERIES_NEWNAME_ALREADY_EXISTS.format(new_name), None)

        elif not current_name == new_name:

            series = self.__series_dict[current_name]
            series.rename(new_name)
            self.__series_dict.pop(current_name)
            self.__series_dict[new_name] = series
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 1, new_name)

            self.__current_media.next_episode(self.checkbutton_random.get_active())

        self.window_rename.hide()

    def __on_configure_event(self, *_):

        if Gdk.WindowState.FULLSCREEN & self.window_root.get_window().get_state():
            fullscreen = True
        else:
            fullscreen = False

        if self.__is_full_screen != fullscreen:
            self.__is_full_screen = fullscreen

            if fullscreen:
                self.menubar.hide()
                self.box_main.hide()
            else:
                self.menubar.show()
                self.box_main.show()

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

            # If the current video got to the end...
            if round(position, 3) >= 0.999:
                self.__current_media.mark_seen_episode()
                GLib.idle_add(self.__liststore_episodes_populate, True)

                # Play the next episode
                if not self.checkbutton_keep_playing.get_active():
                    GLib.idle_add(self.__media_player.pause)
                    GLib.idle_add(self.window_root.unfullscreen)

                else:
                    next_video = self.__current_media.next_episode(self.checkbutton_random.get_active())

                    if next_video is None:
                        GLib.idle_add(self.window_root.unfullscreen)
                        GLib.idle_add(gtk_info, self.window_root, TEXT_END_OF_SERIES)

                    else:
                        self.__media_player.set_video(next_video.get_path(),
                                                      next_video.get_position(),
                                                      self.__current_media.series.get_subtitles_track(),
                                                      self.__current_media.series.get_audio_track(),
                                                      self.__current_media.series.get_start_at(),
                                                      True)

            time.sleep(0.5)

    def __on_thread_load_series(self):
        """
            Load the saved lists
        """
        for file_name in sorted(os.listdir(FOLDER_LIST_PATH)):

            if not file_name.lower().endswith('.csv'):
                continue

            file_path = os.path.join(FOLDER_LIST_PATH, file_name)

            with open(file_path, mode='rt', encoding='utf-8') as f:
                series_info = f.readline().split('|')

            if len(series_info) < 7:
                print("Error, Wrong format for series file = ", file_path)  # todo: show user message
                continue

            path = series_info[0]
            recursive = series_info[1]
            random = series_info[2]
            keep_playing = series_info[3]
            start_at = float(series_info[4])
            audio_track = int(series_info[5])
            subtitles_track = int(series_info[6])

            if '/' in path:
                self.__series_load_from_path(path,
                                             file_path,
                                             recursive,
                                             random,
                                             keep_playing,
                                             start_at,
                                             audio_track,
                                             subtitles_track,
                                             select=False)

        """
            Select the last series that was played
        """
        current_series_name = self.__ccp.get_str('current_series')

        try:
            series_data = self.__series_dict[current_series_name]
        except KeyError:
            pass
        else:
            self.__current_media = CurrentMedia(series_data)

        for i, row in enumerate(self.liststore_series):
            if row[1] == current_series_name:
                GLib.idle_add(self.treeview_series.set_cursor, i)
                return

        GLib.idle_add(self.treeview_series.set_cursor, 0)

    def __series_load_from_path(self,
                                path,
                                data_path,
                                recursive,
                                random,
                                keep_playing,
                                start_at=0.0,
                                audio_track=-2,
                                subtitles_track=-2,
                                select=True):

        new_series = Series(path,
                            data_path,
                            recursive,
                            random,
                            keep_playing,
                            start_at,
                            audio_track,
                            subtitles_track)

        self.__series_dict[new_series.get_name()] = new_series

        if os.path.exists(new_series.get_path()) or not self.checkbox_hide_missing_series.get_active():
            GLib.idle_add(self.__liststore_series_append, (new_series.get_image(), new_series.get_name()))

        if select:  # select the row once the series has been added
            for i, row in enumerate(self.liststore_series):
                if row[1] == new_series.get_name():
                    GLib.idle_add(self.treeview_series.set_cursor, i)
                    break

    def __liststore_series_append(self, data):
        """
            I do not understand why this must be a separate method.
            It is not possible to call directly: GLib.idle_add(self.liststore_series.append, data)
        """
        self.liststore_series.append(data)

    def __series_add_from_fchooser(self, recursive):

        path = gtk_folder_chooser(self.window_root)
        if not path:
            return

        series_name = os.path.basename(path)

        for series in self.__series_dict.values():
            if series.get_path() == path:
                gtk_info(self.window_root, TEXT_SERIES_ALREADY_EXISTS, None)
                return

            elif series.get_name() == series_name:
                gtk_info(self.window_root, TEXT_SERIES_NAME_ALREADY_EXISTS.format(series_name), None)
                return

        th = Thread(target=self.__series_load_from_path, args=[path, None, recursive, False, True])
        th.start()
        self.__threads.append(th)

    def __series_open(self, _):
        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series_data = self.__series_dict[selected_series_name]
        open_directory(series_data.get_path())

    def __series_find_videos(self, _, video_names):

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series_data = self.__series_dict[selected_series_name]

        path = gtk_file_chooser(self.window_root)

        if path is None:
            return

        if len(video_names) == 1:  # if the user only selected one video to find...
            found_videos = series_data.find_video(video_names[0], path)
            if found_videos:
                gtk_info(self.window_root, TEXT_X_OTHER_VIDEOS_HAVE_BEEN_FOUND.format(found_videos), None)

        elif len(video_names) > 1:
            found_videos = series_data.find_videos(path)

            if found_videos:
                gtk_info(self.window_root, TEXT_X_VIDEOS_HAVE_BEEN_FOUND.format(found_videos), None)

        self.__liststore_episodes_populate(True)

    def __liststore_episodes_populate(self, update_liststore):

        if self.treeview_selection_episodes.count_selected_rows() < 0:
            return

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if selected_series_name is None:
            return

        series_data = self.__series_dict[selected_series_name]

        #
        #    Update the series area
        #

        self.checkbutton_keep_playing.set_active(series_data.get_keep_playing())
        self.checkbutton_random.set_active(series_data.get_random())

        self.spinbutton_audio.set_value(series_data.get_audio_track())
        self.spinbutton_subtitles.set_value(series_data.get_subtitles_track())
        self.spinbutton_start_at.set_value(series_data.get_start_at())

        if self.checkbutton_random.get_active():
            played, total, percent = series_data.get_r_played_stats()
        else:
            played, total, percent = series_data.get_o_played_stats()

        self.progressbar.set_fraction(percent)

        """
            update the episodes area
        """
        if not update_liststore:
            return

        self.liststore_episodes.clear()
        self.column_name.set_spacing(0)

        if not os.path.exists(series_data.get_path()):
            return

        # initialize the list
        videos_list = []
        for _ in series_data.get_videos():
            videos_list.append(None)

        # sort it by id
        for video in series_data.get_videos():
            try:
                videos_list[video.get_id() - 1] = video
            except Exception as e:
                print(str(e))

        for video in videos_list:
            if video:

                # get the color of the font
                if video.get_display():
                    color = self.__default_font_color
                else:
                    color = self.__hidden_font_color

                # add the video to the list store
                if video.get_display() or not self.checkbox_hidden_items.get_active():
                    self.liststore_episodes.append([video.get_id(),
                                                    video.get_empty_name(),
                                                    video.get_extension(),
                                                    video.get_state(),
                                                    video.get_play(),
                                                    video.get_o_played(),
                                                    video.get_r_played(),
                                                    " ",
                                                    color])
            else:
                print("Error loading the liststore_episodes. The series '{}' has an empty video.".format(
                    series_data.get_name()))

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

    def __menu_series_display(self, series_data, event):

        menu = Gtk.Menu()

        if not os.path.exists(series_data.get_path()):
            menuitem = Gtk.ImageMenuItem(label=TEXT_FIND)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_find)
            img = Gtk.Image(stock=Gtk.STOCK_DIALOG_WARNING)
            menuitem.set_image(img)

        else:
            menuitem = Gtk.ImageMenuItem(label=TEXT_OPEN_FOLDER)
            menu.append(menuitem)
            menuitem.connect('activate', self.__series_open)
            img = Gtk.Image(stock=Gtk.STOCK_OPEN)
            menuitem.set_image(img)

            menuitem = Gtk.ImageMenuItem(label=TEXT_RENAME)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_rename)
            img = Gtk.Image(stock=Gtk.STOCK_BOLD)
            menuitem.set_image(img)

            menuitem = Gtk.ImageMenuItem(label=TEXT_RESET)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_reset)
            img = Gtk.Image(stock=Gtk.STOCK_REFRESH)
            menuitem.set_image(img)

            menuitem = Gtk.ImageMenuItem(label=TEXT_ADD_PICTURE)
            menu.append(menuitem)
            menuitem.connect('activate', self.__on_menuitem_series_add_picture)
            img = Gtk.Image(stock=Gtk.STOCK_SELECT_COLOR)
            menuitem.set_image(img)

        menuitem = Gtk.ImageMenuItem(label=TEXT_DELETE)
        menu.append(menuitem)
        menuitem.connect('activate', self.__on_menuitem_series_delete)
        img = Gtk.Image(stock=Gtk.STOCK_CANCEL)
        menuitem.set_image(img)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)

        return True

    def __menuitem_episode_open_dir(self, _, video_name):

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series_data = self.__series_dict[selected_series_name]
        path = series_data.get_path_from_video_name(video_name)

        if os.path.exists(path):
            open_directory(path)

    def __on_menuitem_series_add_picture(self, _):
        """
            Add a picture to a series
        """
        file = gtk_file_chooser(self.window_root, 'picture')
        if file is not None:
            series = self.__series_dict[
                gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

            series.set_image(file)
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 0, series.get_image())
            self.__liststore_episodes_populate(False)

    def __on_menuitem_series_find(self, _):

        path = gtk_folder_chooser(self.window_root)
        if not path:
            return

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series_data = self.__series_dict[selected_series_name]

        series_data.find_series(path)
        gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 0, series_data.get_image())
        self.__liststore_episodes_populate(True)

    def __on_menuitem_series_reset(self, _):

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if gtk_dialog_question(self.window_root, TEXT_RESET_SERIES.format(selected_series_name), None):
            series = self.__series_dict[selected_series_name]
            series.reset_data()
            self.__liststore_episodes_populate(True)

    def __on_menuitem_series_rename(self, _):
        """
            change the name of a series
        """
        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        self.label_old_name.set_text(selected_series_name)
        self.entry_rename.set_text(selected_series_name)

        self.window_rename.show()

    def __on_menuitem_series_delete(self, _):
        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if gtk_dialog_question(self.window_root, TEXT_DELETE_SERIES.format(selected_series_name), None):

            self.__series_dict.pop(selected_series_name)

            gtk_remove_first_selected_row_from_liststore(self.treeview_selection_series)

            if os.path.exists(SERIES_PATH.format(selected_series_name)):
                os.remove(SERIES_PATH.format(selected_series_name))

    def __on_menuitem_series_ignore_episode(self, _):

        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if not treepaths == []:
            selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            series = self.__series_dict[selected_series_name]

            for treepath in treepaths:
                episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
                series.ignore_video(episode_name)

            self.__liststore_episodes_populate(True)

    def __on_menuitem_series_dont_ignore_episode(self, _):

        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if not treepaths == []:
            selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            series = self.__series_dict[selected_series_name]

            for treepath in treepaths:
                episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
                series.dont_ignore_video(episode_name)

            self.__liststore_episodes_populate(True)


if __name__ == '__main__':
    vlist_player = VListPlayer()
    Gtk.main()
    vlist_player.join()
    VLC_INSTANCE.release()

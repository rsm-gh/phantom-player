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
import threading

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, Gdk

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from Paths import *
from Texts import *
from model import Series
from model.CurrentMedia import CurrentMedia
from view.MediaPlayer import MediaPlayerWidget, VLC_INSTANCE
from view.gtk_utils import *
from controller.CCParser import CCParser
from system_utils import open_directory, open_link


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


class VListPlayer(Gtk.Window):

    def __init__(self):

        super().__init__()

        self.__thread_vlc_scan = True
        self.__rc_menu = None

        """
            load items from glade
        """
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join(_SCRIPT_DIR, "vlist-player.glade"))
        builder.connect_signals(self)

        glade_objects_ids = (

            'window_root',
            'label_current_series', 'treeview_selection_episodes', 'progressbar', 'checkbox_hidden_items',
            'eventbox_selected_series_name', 'button_root_play_and_stop', 'treeview_episodes', 'treeview_series',
            'treeview_selection_series', 'liststore_series', 'liststore_episodes', 'spinbutton_audio',
            'spinbutton_subtitles',
            'spinbutton_start_at', 'box_episodes', 'box_series', 'box_main', 'box_series_data',
            'box_series_menu', 'box_main', 'column_number', 'column_name', 'column_extension', 'column_play',
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

        for glade_object_id in glade_objects_ids:
            setattr(self, glade_object_id, builder.get_object(glade_object_id))

        """
            Media Player
        """
        self.__current_media = CurrentMedia()
        self.__mp_widget = MediaPlayerWidget(self)
        self.box_episodes.pack_start(self.__mp_widget, True, True, 0)
        self.box_episodes.reorder_child(self.__mp_widget, 0)
        threading.Thread(target=self.__thread_scan_media_player).start()

        """
            configuration
        """

        # list of classes
        self.__list_episodes_class = []

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
        self.window_root.connect('delete-event', self.quit_the_program)

        self.__ccp = CCParser(CONFIGURATION_FILE, 'vlist-player')

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
        self.window_root.show_all()

        if not self.__ccp.get_bool_defval('fullmode', False):
            self.__episodes_hide_rc_menu(False)

        """
            Load the existent lists
        """
        threading.Thread(target=self.__series_load_data).start()

    def __series_load_data(self):
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
                print("Error, Wrong format for series file = ", file_path)
                continue

            path = series_info[0]
            recursive = series_info[1]
            random = series_info[2]
            keep_playing = series_info[3]
            start_at = series_info[4]
            audio_track = series_info[5]
            subtitles_track = series_info[6]


            if '/' in path:
                self.__series_load_from_path(path,
                                             file_path,
                                             recursive,
                                             random,
                                             keep_playing,
                                             start_at,
                                             audio_track,
                                             subtitles_track)

        """
            Load the last series that has been played
        """
        current_series_name = self.__ccp.get_str('current_series')

        for i, row in enumerate(self.liststore_series):
            if row[1] == current_series_name:
                Gdk.threads_enter()
                self.treeview_series.set_cursor(i)
                Gdk.threads_leave()
                break

    def __thread_scan_media_player(self):
        self.__thread_vlc_scan = True

        while self.__thread_vlc_scan:

            if self.__current_media.series is not None:

                position = self.__mp_widget.get_position()
                stopped_position = self.__mp_widget.get_stopped_position()
                series = self.__current_media.series

                # If the player was stopped
                if stopped_position > 0:
                    series.set_video_position(self.__current_media.video, stopped_position)

                # If the current video got to the end...
                if round(position, 3) >= 0.999:

                    self.__current_media.series.mark_episode(self.__current_media.video, self.__current_media.random,
                                                             True)

                    self.__episode_update()

                    Gdk.threads_enter()
                    self.__episodes_populate_liststore(True)
                    Gdk.threads_leave()

                    if self.checkbutton_keep_playing.get_active():
                        if self.__current_media.video:
                            self.__mp_widget.play_video(self.__current_media.video.get_path(),
                                                           self.__current_media.video.get_position(),
                                                           series.get_subtitles_track(),
                                                           series.get_audio_track(),
                                                           series.get_start_at(),
                                                           True)

                        else:
                            Gdk.threads_enter()
                            self.__mp_widget.hide()
                            Gdk.threads_leave()
                            Gdk.threads_enter()
                            gtk_info(self.window_root, TEXT_END_OF_SERIES)
                            Gdk.threads_leave()
                    else:
                        Gdk.threads_enter()
                        self.__mp_widget.stop_position()
                        Gdk.threads_leave()
                        Gdk.threads_enter()
                        self.__mp_widget.hide()
                        Gdk.threads_leave()

            time.sleep(0.5)

    def __episodes_populate_liststore(self, update_liststore):

        if self.treeview_selection_episodes.count_selected_rows() >= 0:

            selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            series = Series.series_dictionary[selected_series_name]

            #
            #    Update the series area
            #

            self.checkbutton_keep_playing.set_active(series.get_keep_playing())
            self.checkbutton_random.set_active(series.get_random())

            self.spinbutton_audio.set_value(series.get_audio_track())
            self.spinbutton_subtitles.set_value(series.get_subtitles_track())
            self.spinbutton_start_at.set_value(series.get_start_at())

            if self.checkbutton_random.get_active():
                (played, total, percent) = series.get_r_played_stats()
            else:
                (played, total, percent) = series.get_o_played_stats()

            progress_text = "{}/{}".format(played, total)

            self.label_current_series.set_label(selected_series_name)
            self.progressbar.set_fraction(percent)

            self.progressbar.set_text(progress_text)
            self.progressbar.set_show_text(True)

            #   Update the big image
            for children in self.eventbox_selected_series_name.get_children():
                self.eventbox_selected_series_name.remove(children)

            image = series.get_big_image()
            self.eventbox_selected_series_name.add(image)
            image.show()

            """
                update the episodes area
            """
            if update_liststore:
                self.liststore_episodes.clear()
                self.column_name.set_spacing(0)

                if os.path.exists(series.get_path()):

                    # initialize the list
                    videos_list = []
                    for _ in series.get_videos():
                        videos_list.append(None)

                    # sort it by id
                    for video in series.get_videos():
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
                                                                color,
                                                                ])
                        else:
                            print("Error loading the liststore_episodes. The series '{}' has an empty video.".format(
                                series.get_name()))

    def __episodes_hide_rc_menu(self, write=True):

        rx, ry = self.window_root.get_size()
        state = self.box_episodes.get_visible()

        if state:
            bx = self.box_episodes.get_allocation().width
            self.box_episodes.hide()
            self.window_root.resize(rx - bx - 15, ry)  # 15 is the border with
            self.box_main.set_child_packing(self.box_series, True, True, 0, Gtk.PackType.START)
        else:
            self.box_main.set_child_packing(self.box_series, False, False, 0, Gtk.PackType.START)
            self.box_episodes.show_all()

        if write:
            self.__ccp.write('fullmode', not state)

    def __episode_open_dir(self, _, video_name):

        series = Series.series_dictionary[
            gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        path = series.get_path_from_video_name(video_name)

        if os.path.exists(path):
            open_directory(path)

    def __episode_update(self):
        series = Series.series_dictionary[
            gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

        self.__current_media.series = series

        if self.checkbutton_random.get_active():
            self.__current_media.video = series.get_r_episode()
        else:
            self.__current_media.video = series.get_o_episode()

        self.__current_media.random = self.checkbutton_random.get_active()

    def __series_load_from_path(self, path,
                                data_path,
                                recursive,
                                random,
                                keep_playing,
                                start_at=0.0,
                                audio_track=-2,
                                subtitles_track=-2):

        new_series = Series.Serie(path,
                                  data_path,
                                  recursive,
                                  random,
                                  keep_playing,
                                  start_at,
                                  audio_track,
                                  subtitles_track)

        if os.path.exists(new_series.get_path()) or not self.checkbox_hide_missing_series.get_active():
            Gdk.threads_enter()
            self.liststore_series.append([new_series.get_image(), new_series.get_name()])
            Gdk.threads_leave()

        # select the row once a series has been added
        for i, row in enumerate(self.liststore_series):
            if row[1] == new_series.get_name():
                Gdk.threads_enter()
                self.treeview_series.set_cursor(i)
                Gdk.threads_leave()

                break

    def __series_populate_liststore(self):

        # Populate
        #
        Gdk.threads_enter()
        self.liststore_series.clear()
        Gdk.threads_leave()

        for name in sorted(Series.series_dictionary.keys()):
            series = Series.series_dictionary[name]

            if os.path.exists(series.get_path()) or not self.checkbox_hide_missing_series.get_active():
                Gdk.threads_enter()
                self.liststore_series.append([series.get_image(), series.get_name()])
                Gdk.threads_leave()

        if len(self.liststore_series) <= 0:
            Gdk.threads_enter()
            self.eventbox_selected_series_name.add(Gtk.Image.new_from_file(ICON_LOGO_BIG))
            Gdk.threads_leave()

        # Select the current series
        #
        current_series_name = self.__ccp.get_str('current_series')

        for i, row in enumerate(self.liststore_series):
            if row[1] == current_series_name:
                Gdk.threads_enter()
                self.treeview_series.set_cursor(i)
                Gdk.threads_leave()
                return

        Gdk.threads_enter()
        self.treeview_series.set_cursor(0)
        Gdk.threads_leave()

    def __series_open(self, _):
        series = Series.series_dictionary[
            gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        open_directory(series.get_path())

    def __series_find_videos(self, _, video_names):

        series = Series.series_dictionary[
            gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

        path = gtk_file_chooser(self.window_root)

        if path is not None:
            if len(video_names) == 1:  # if the user only selected one video to find...
                found_videos = series.find_video(video_names[0], path)
                if found_videos:
                    gtk_info(self.window_root, TEXT_X_OTHER_VIDEOS_HAVE_BEEN_FOUND.format(found_videos), None)

            elif len(video_names) > 1:
                found_videos = series.find_videos(path)

                if found_videos:
                    gtk_info(self.window_root, TEXT_X_VIDEOS_HAVE_BEEN_FOUND.format(found_videos), None)

            self.__episodes_populate_liststore(True)

    def __series_add_picture(self, _):
        """
            Add a picture to a series
        """
        file = gtk_file_chooser(self.window_root, 'picture')
        if file is not None:
            series = Series.series_dictionary[
                gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

            series.set_image(file)
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 0, series.get_image())
            self.__episodes_populate_liststore(False)

    def __series_find(self, _):

        path = gtk_folder_chooser(self.window_root)

        if path:
            series = Series.series_dictionary[
                gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

            series.find_series(path)
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 0, series.get_image())
            self.__episodes_populate_liststore(True)

    def __series_reset(self, _):

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if gtk_dialog_question(self.window_root, TEXT_RESET_SERIES.format(selected_series_name), None):
            series = Series.series_dictionary[selected_series_name]
            series.reset_data()
            self.__episodes_populate_liststore(True)

    def __series_rename(self, _):
        """
            change the name of a series
        """
        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        self.label_old_name.set_text(selected_series_name)
        self.entry_rename.set_text(selected_series_name)

        self.window_rename.show()

    def __series_delete(self, _):
        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if gtk_dialog_question(self.window_root, TEXT_DELETE_SERIES.format(selected_series_name), None):

            Series.series_dictionary.pop(selected_series_name)

            gtk_remove_first_selected_row_from_liststore(self.treeview_selection_series)

            if os.path.exists(SERIES_PATH.format(selected_series_name)):
                os.remove(SERIES_PATH.format(selected_series_name))

    def __series_ignore_episode(self, _):

        (model, treepaths) = self.treeview_selection_episodes.get_selected_rows()

        if not treepaths == []:
            selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            series = Series.series_dictionary[selected_series_name]

            for treepath in treepaths:
                episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
                series.ignore_video(episode_name)

            self.__episodes_populate_liststore(True)

    def __series_dont_ignore_episode(self, _):

        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if not treepaths == []:
            selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            series = Series.series_dictionary[selected_series_name]

            for treepath in treepaths:
                episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
                series.dont_ignore_video(episode_name)

            self.__episodes_populate_liststore(True)

    def quit_the_program(self, *_):

        if self.__mp_widget.get_property('visible'):
            self.window_root.hide()
            self.__mp_widget.die_on_quit()
            return True
        else:
            self.__thread_vlc_scan = False
            self.__mp_widget.stop_threads()
            Gtk.main_quit()

    def on_spinbutton_audio_value_changed(self, spinbutton):
        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        value = spinbutton.get_value_as_int()

        Series.series_dictionary[series_name].set_audio_track(value)

    def on_spinbutton_subtitles_value_changed(self, spinbutton):

        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        value = spinbutton.get_value_as_int()

        Series.series_dictionary[series_name].set_subtitles_track(value)

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


        Series.series_dictionary[series_name].set_start_at(value)

    def on_checkbutton_random_toggled(self, radiobutton, *_):
        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        radiobutton_state = radiobutton.get_active()
        Series.series_dictionary[series_name].set_random(radiobutton_state)
        self.__episodes_populate_liststore(False)

    def on_checkbutton_keep_playing_toggled(self, radiobutton, *_):
        series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)

        if series_name is None:
            return

        radiobutton_state = radiobutton.get_active()
        Series.series_dictionary[series_name].set_keep_playing(radiobutton_state)

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

    def on_checkbox_hidden_items_toggled(self, *_):
        self.__ccp.write('hide-items', self.checkbox_hidden_items.get_active())
        self.__episodes_populate_liststore(True)

    def on_checkbox_hide_warning_missing_series_toggled(self, *_):
        self.__ccp.write('warningMissingSeries', self.checkbox_hide_warning_missing_series.get_active())

    def on_checkbox_episodes_toggled(self, row, column):

        state = not self.liststore_episodes[row][column]

        self.liststore_episodes[row][column] = state

        series = Series.series_dictionary[
            gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        episode_name = '{}{}'.format(self.liststore_episodes[row][1], self.liststore_episodes[row][2])

        series.change_checkbox_state(episode_name, column, state)

        self.__episodes_populate_liststore(False)

    def on_button_close_preferences_clicked(self, *_):
        self.window_preferences.hide()

    def on_button_close_controls_clicked(self, *_):
        self.window_controls.hide()

    def on_button_close_files_clicked(self, *_):
        self.window_files.hide()

    def on_button_cancel_rename_clicked(self, *_):
        self.window_rename.hide()

    def on_button_close_window_list_clicked(self, *_):
        self.window_list.hide()

    def on_treeview_episodes_drag_end(self, *_):

        # Get the new order
        new_order = [row[0] for row in self.liststore_episodes]

        # Update the treeview
        for i, row in enumerate(self.liststore_episodes, 1):
            row[0] = i

            # Update the CSV file
        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series = Series.series_dictionary[selected_series_name]
        series.reorder(new_order)

    def on_button_okay_rename_clicked(self, *_):

        current_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        new_name = self.entry_rename.get_text()

        if new_name in Series.series_dictionary.keys():
            gtk_info(self.window_rename, TEXT_SERIES_NEWNAME_ALREADY_EXISTS.format(new_name), None)

        elif not current_name == new_name:

            series = Series.series_dictionary[current_name]
            series.rename(new_name)
            Series.series_dictionary.pop(current_name)
            Series.series_dictionary[new_name] = series
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 1, new_name)
            self.label_current_series.set_label(new_name)

            self.__episode_update()

        self.window_rename.hide()

    @staticmethod
    def on_imagemenuitem_bugs_activate(*_):
        open_link('https://github.com/rsm-gh/vlist-player/issues')

    def on_imagemenuitem_preferences_activate(self, *_):
        self.window_preferences.show()

    def on_menuitem_list_from_folder_recursive_activate(self, *_):
        path = gtk_folder_chooser(self.window_root)
        if path:
            series_name = os.path.basename(path)

            for series in Series.series_dictionary.values():
                if series.get_path() == path:
                    gtk_info(self.window_root, TEXT_SERIES_ALREADY_EXISTS, None)
                    return

                if series.get_name() == series_name:
                    gtk_info(self.window_root, TEXT_SERIES_NAME_ALREADY_EXISTS.format(series_name), None)
                    return

            threading.Thread(target=self.__series_load_from_path, args=[path, None, True, False, True]).start()

    def on_menuitem_checkbox_activated(self, _, column, state):

        (model, treepaths) = self.treeview_selection_episodes.get_selected_rows()

        if not treepaths == []:

            selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            series = Series.series_dictionary[selected_series_name]

            episode_names = []
            for treepath in treepaths:
                episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)

                self.liststore_episodes[treepath][column] = state

                episode_names.append(episode_name)

            series.change_checkbox_state(episode_names, column, state)

            self.__episodes_populate_liststore(True)

    def on_menuitem_list_from_folder_activate(self, *_):
        path = gtk_folder_chooser(self.window_root)
        if path:

            series_name = os.path.basename(path)

            for series in Series.series_dictionary.values():
                if series.get_path() == path:
                    gtk_info(self.window_root, TEXT_SERIES_ALREADY_EXISTS, None)
                    return

                if series.get_name() == series_name:
                    gtk_info(self.window_root, TEXT_SERIES_NAME_ALREADY_EXISTS.format(series_name), None)
                    return

            threading.Thread(target=self.__series_load_from_path, args=[path, None, False, False, True]).start()

    def on_button_close_find_files_clicked(self, *_):
        self.window_finding_files.hide()

    def on_imagemenuitem_finding_files_activate(self, *_):
        self.window_finding_files.show()

    def on_imagemenuitem_about_activate(self, *_):
        _ = self.window_about.run()
        self.window_about.hide()

    def on_imagemenuitem_controls_activate(self, *_):
        self.window_controls.show()

    def on_imagemenuitem_files_activate(self, *_):
        self.window_files.show()

    def on_checkbox_hide_missing_series_toggled(self, *_):
        self.__ccp.write('hide-missing-series', self.checkbox_hide_missing_series.get_active())
        threading.Thread(target=self.__series_populate_liststore).start()

    def on_cellrenderertoggle_play_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), 4)

    def on_cellrenderertoggle_oplayed_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), 5)

    def on_cellrenderertoggle_rplayed_toggled(self, _, row):
        self.on_checkbox_episodes_toggled(int(row), 6)

    def on_treeview_episodes_press_event(self, _, event):
        model, treepaths = self.treeview_selection_episodes.get_selected_rows()

        if len(treepaths) == 0:
            return

        selection_length = len(treepaths)

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series = Series.series_dictionary[selected_series_name]

        """
            Active or deactivate the buttons move up and down
        """

        if event.button == 1 and selection_length == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepaths[0], 1, 2)

            path = series.get_path_from_video_name(episode_name)

            if path and os.path.exists(path):
                self.__mp_widget.play_video(path, 0, series.get_subtitles_track(), series.get_audio_track(),
                                               series.get_start_at())
            else:
                gtk_info(self.window_root, TEXT_CANT_PLAY_MEDIA_MISSING)


        elif event.button == 3:  # right click

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

            self.__rc_menu = Gtk.Menu()

            """
                Open the containing folder (only if the user selected one video)
            """
            if selection_length == 1:

                selected_episode_name = gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepaths[0], 1, 2)

                menuitem = Gtk.ImageMenuItem(TEXT_FOLDER)
                self.__rc_menu.append(menuitem)
                menuitem.connect('activate', self.__episode_open_dir, selected_episode_name)
                img = Gtk.Image(stock=Gtk.STOCK_OPEN)
                menuitem.set_image(img)


            elif selection_length > 1:

                for i, label in enumerate((TEXT_PLAY, TEXT_O_PLAYED, TEXT_R_PLAYED), 4):
                    # mark to check
                    menuitem = Gtk.ImageMenuItem(label)
                    self.__rc_menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, i, True)
                    img = Gtk.Image(stock=Gtk.STOCK_APPLY)
                    menuitem.set_image(img)

                    # mark to uncheck
                    menuitem = Gtk.ImageMenuItem(label)
                    self.__rc_menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, i, False)
                    img = Gtk.Image(stock=Gtk.STOCK_MISSING_IMAGE)
                    menuitem.set_image(img)

            """
                Menu "Fin videos"
            """
            list_of_names = [gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2) for treepath in
                             treepaths]

            if series.missing_videos(list_of_names):
                menuitem = Gtk.ImageMenuItem(TEXT_FIND)
                menuitem.connect('activate', self.__series_find_videos, list_of_names)
                self.__rc_menu.append(menuitem)
                img = Gtk.Image(stock=Gtk.STOCK_DIALOG_WARNING)
                menuitem.set_image(img)

            # ignore videos
            menuitem = Gtk.ImageMenuItem(TEXT_IGNORE)
            self.__rc_menu.append(menuitem)
            menuitem.connect('activate', self.__series_ignore_episode)
            img = Gtk.Image(stock=Gtk.STOCK_FIND_AND_REPLACE)
            menuitem.set_image(img)

            # don't ignore videos
            menuitem = Gtk.ImageMenuItem(TEXT_DONT_IGNORE)
            self.__rc_menu.append(menuitem)
            menuitem.connect('activate', self.__series_dont_ignore_episode)
            img = Gtk.Image(stock=Gtk.STOCK_FIND)
            menuitem.set_image(img)

            self.__rc_menu.show_all()
            self.__rc_menu.popup(None, None, None, None, event.button, event.time)

            return True

    def on_treeview_selection_series_changed(self, treeselection):
        if treeselection.count_selected_rows() > 0:
            self.__episodes_populate_liststore(True)

    def on_eventbox_selected_series_name_button_press_event(self, _, event):
        self.on_treeview_series_press_event(self.treeview_series, event, False)

    def on_treeview_series_press_event(self, _, event, inside_treeview=True):

        # check if some row is selected
        if self.treeview_selection_series.count_selected_rows() <= 0:
            return

        selected_series_name = gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        series = Series.series_dictionary[selected_series_name]

        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == 1:  # left click

                # check if the liststore is empty
                if len(self.liststore_episodes) <= 0 and not self.checkbox_hide_warning_missing_series.get_active():
                    gtk_info(self.window_root, TEXT_CANT_PLAY_SERIES_MISSING, None)

                """
                    Play a video of the series
                """
                self.__ccp.write('current_series', selected_series_name)

                if not self.__mp_widget.is_playing_or_paused() or self.__current_media.series.get_name() != selected_series_name:
                    self.__episode_update()

                    if not self.__current_media.video:
                        gtk_info(self.window_root, TEXT_END_OF_SERIES)
                        self.__mp_widget.hide()

                    elif not os.path.exists(self.__current_media.video.get_path()):
                        gtk_info(self.window_root, TEXT_CANT_PLAY_MEDIA_MISSING)
                        self.__mp_widget.hide()
                    else:
                        self.__mp_widget.play_video(self.__current_media.video.get_path(),
                                                       self.__current_media.video.get_position(),
                                                       series.get_subtitles_track(),
                                                       series.get_audio_track(),
                                                       series.get_start_at(),
                                                       )

                        self.__mp_widget.present()
                else:
                    self.__mp_widget.present()


        elif event.type == Gdk.EventType.BUTTON_PRESS:

            if self.treeview_selection_series.count_selected_rows() >= 0 and event.button == 3:  # right click

                # get the iter where the user is pointing
                pointing_treepath = self.treeview_series.get_path_at_pos(event.x, event.y)[0]

                # if the iter is not in the selected iters, remove the previous selection
                model, treepaths = self.treeview_selection_series.get_selected_rows()

                if pointing_treepath not in treepaths and inside_treeview:
                    self.treeview_selection_series.unselect_all()
                    self.treeview_selection_series.select_path(pointing_treepath)

                """ 
                    Right click menu
                """
                self.__rc_menu = Gtk.Menu()

                if os.path.exists(series.get_path()):

                    menuitem = Gtk.ImageMenuItem(TEXT_OPEN_FOLDER)
                    self.__rc_menu.append(menuitem)
                    menuitem.connect('activate', self.__series_open)
                    img = Gtk.Image(stock=Gtk.STOCK_OPEN)
                    menuitem.set_image(img)

                    menuitem = Gtk.ImageMenuItem(TEXT_RENAME)
                    self.__rc_menu.append(menuitem)
                    menuitem.connect('activate', self.__series_rename)
                    img = Gtk.Image(stock=Gtk.STOCK_BOLD)
                    menuitem.set_image(img)

                    menuitem = Gtk.ImageMenuItem(TEXT_RESET)
                    self.__rc_menu.append(menuitem)
                    menuitem.connect('activate', self.__series_reset)
                    img = Gtk.Image(stock=Gtk.STOCK_REFRESH)
                    menuitem.set_image(img)

                    menuitem = Gtk.ImageMenuItem(TEXT_ADD_PICTURE)
                    self.__rc_menu.append(menuitem)
                    menuitem.connect('activate', self.__series_add_picture)
                    img = Gtk.Image(stock=Gtk.STOCK_SELECT_COLOR)
                    menuitem.set_image(img)
                else:
                    menuitem = Gtk.ImageMenuItem(TEXT_FIND)
                    self.__rc_menu.append(menuitem)
                    menuitem.connect('activate', self.__series_find)
                    img = Gtk.Image(stock=Gtk.STOCK_DIALOG_WARNING)
                    menuitem.set_image(img)

                menuitem = Gtk.ImageMenuItem(TEXT_DELETE)
                self.__rc_menu.append(menuitem)
                menuitem.connect('activate', self.__series_delete)
                img = Gtk.Image(stock=Gtk.STOCK_CANCEL)
                menuitem.set_image(img)

                self.__rc_menu.show_all()
                self.__rc_menu.popup(None, None, None, None, event.button, event.time)

                return True


if __name__ == '__main__':
    _ = VListPlayer()
    Gtk.main()
    VLC_INSTANCE.release()

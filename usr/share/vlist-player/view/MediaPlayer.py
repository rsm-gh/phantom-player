#!/usr/bin/python3
#

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli.
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
#

import os
import sys
import gi
import time
import threading
from datetime import timedelta

gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
from gi.repository import Gtk, GObject, Gdk

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from Paths import *
from system_utils import turn_off_screensaver, get_active_window_title
from view.VLCWidget import VLCWidget, VLC_INSTANCE


def format_milliseconds_to_time(number):
    time_string = str(timedelta(milliseconds=number)).split('.')[0]

    # remove the hours if they are not necessary
    try:
        if int(time_string.split(':', 1)[0]) == 0:
            time_string = time_string.split(':', 1)[1]
    except Exception:
        pass

    return time_string

class MediaPlayerWidget(Gtk.Overlay):

    def __init__(self, root_window):

        super().__init__()

        self.__root_window = root_window

        self.__width = 600
        self.__height = 300
        self.__stopped_position = 0
        self.__update__scale_progress = True
        self.__thread_player_activity_status = False
        self.__thread_mouse_motion_status = False

        self.__vlc_widget = VLCWidget(self.__root_window)
        self.__vlc_widget.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#000000'))


        self.add(self.__vlc_widget)

        # Buttons box
        self.__buttons_box = Gtk.VBox()
        self.__buttons_box.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self.__buttons_box.set_valign(Gtk.Align.CENTER)
        self.__buttons_box.set_halign(Gtk.Align.START)

        self.__button_play_pause = Gtk.ToolButton(Gtk.STOCK_MEDIA_PLAY)
        self.__button_play_pause.connect('clicked', self.__on_button_play_pause_clicked)
        self.__button_play_pause.set_can_focus(False)

        self.__button_restart = Gtk.ToolButton(Gtk.STOCK_MEDIA_PREVIOUS)
        self.__button_restart.connect('clicked', self.__on_button_restart_the_video)
        self.__button_restart.set_can_focus(False)

        self.__button_end_video = Gtk.ToolButton(Gtk.STOCK_MEDIA_NEXT)
        self.__button_end_video.connect('clicked', self.__on_button_end_the_video)
        self.__button_end_video.set_can_focus(False)

        self.__buttons_box.pack_start(self.__button_restart, True, True, 0)
        self.__buttons_box.pack_start(self.__button_play_pause, True, True, 0)
        self.__buttons_box.pack_start(self.__button_end_video, True, True, 0)

        self.add_overlay(self.__buttons_box)

        # Scales Box        

        self.__scales_box = Gtk.Box()
        self.__scales_box.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self.__scales_box.set_valign(Gtk.Align.END)
        self.__scales_box.set_halign(Gtk.Align.CENTER)

        self.__label_progress = Gtk.Label()
        self.__label_progress.set_markup('<span font="{0}" color="white">00:00:00</span>'.format(self.__height / 29.0))
        self.__label_progress.set_margin_right(5)
        self.__label_progress.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))

        self.__scale_progress = Gtk.Scale()
        self.__scale_progress.set_range(0, 1)
        self.__scale_progress.set_size_request(self.__width / 2, self.__height / 29.0)
        self.__scale_progress.set_draw_value(False)
        self.__scale_progress.set_hexpand(True)
        self.__scale_progress.set_can_focus(False)
        self.__scale_progress.add_mark(0.25, Gtk.PositionType.TOP, None)
        self.__scale_progress.add_mark(0.5, Gtk.PositionType.TOP, None)
        self.__scale_progress.add_mark(0.75, Gtk.PositionType.TOP, None)
        self.__scale_progress.connect('button-press-event', self.__scale_button_press)
        self.__scale_progress.connect('button-release-event', self.__scale_button_release)

        self.__label_length = Gtk.Label()
        self.__label_length.set_markup('<span font="{0}" color="white">00:00:00</span>'.format(self.__height / 29.0))
        self.__label_length.set_margin_right(5)
        self.__label_length.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))

        self.__scale_volume = Gtk.VolumeButton()
        self.__scale_volume.connect('value_changed', self.__scale_volume_changed)

        self.__scales_box.pack_start(self.__label_progress, True, True, 3)
        self.__scales_box.pack_start(self.__scale_progress, True, True, 1)
        self.__scales_box.pack_start(self.__label_length, True, True, 3)
        self.__scales_box.pack_start(self.__scale_volume, True, True, 3)

        self.add_overlay(self.__scales_box)

        #   Extra volume label

        self.__label_volume2 = Gtk.Label()
        self.__label_volume2.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self.__label_volume2.set_markup(
            '<span font="{1}" color="white"> Vol: {0}% </span>'.format(0, self.__height / 30.0))
        self.__label_volume2.set_valign(Gtk.Align.START)
        self.__label_volume2.set_halign(Gtk.Align.END)
        self.add_overlay(self.__label_volume2)

        self.connect('key-press-event', self.__on_key_pressed)

        """
            Init the threads
        """
        threading.Thread(target=self.__thread_mouse_motion).start()
        threading.Thread(target=self.__thread_player_activity).start()

    def __on_button_player_stop(self, *_):
        self.__stopped_position = self.__vlc_widget.player.get_position()
        self.__vlc_widget.player.stop()
        turn_off_screensaver(False)
        self.hide()

    def __on_button_play_pause_clicked(self, *_):
        if not self.__vlc_widget.is_playing():
            self.__button_play_pause.set_stock_id('gtk-media-pause')
            self.__vlc_widget.player.play()
            turn_off_screensaver(True)
        else:
            self.__button_play_pause.set_stock_id('gtk-media-play')
            self.__vlc_widget.player.pause()
            turn_off_screensaver(False)

    @staticmethod
    def __thread_hide_label(label):
        time.sleep(1.5)
        Gdk.threads_enter()
        label.hide()
        Gdk.threads_leave()

    def __thread_mouse_motion(self):
        #
        #   Hide or display the toolboxes
        #
        self.__thread_mouse_motion_status = True
        state = '?'

        while self.__thread_mouse_motion_status:

            movement_time = time.time() - self.__vlc_widget.get_mouse_time()

            if state != 'hidden' and movement_time >= 3:
                state = 'hidden'
                Gdk.threads_enter()
                self.__buttons_box.hide()
                self.__scales_box.hide()
                Gdk.threads_leave()
            elif state != 'shown' and movement_time < 3:
                state = 'shown'
                Gdk.threads_enter()
                self.__buttons_box.show()
                self.__scales_box.show()
                self.__label_volume2.show()
                Gdk.threads_leave()

            time.sleep(0.3)

    def __thread_player_activity(self):
        """
            This method scans the state of the player to update the tool buttons, volume, play-stop etc
        """

        self.__thread_player_activity_status = True
        while self.__thread_player_activity_status:

            time.sleep(0.2)

            vlc_is_playing = self.__vlc_widget.is_playing()
            vlc_volume = self.__vlc_widget.player.audio_get_volume()
            vlc_position = self.__vlc_widget.player.get_position()
            scale_volume_value = int(self.__scale_volume.get_value() * 100)
            scale_progres_value = self.__scale_progress.get_value()

            # Update the play-pause button
            if vlc_is_playing and self.__button_play_pause.get_stock_id() == 'gtk-media-play':
                Gdk.threads_enter()
                self.__button_play_pause.set_stock_id('gtk-media-pause')
                Gdk.threads_leave()
            elif not vlc_is_playing and self.__button_play_pause.get_stock_id() == 'gtk-media-pause':
                Gdk.threads_enter()
                self.__button_play_pause.set_stock_id('gtk-media-play')
                Gdk.threads_leave()

            """
                Update the volume scale
            """
            if vlc_volume <= 100 and vlc_volume != scale_volume_value:

                Gdk.threads_enter()
                self.__scale_volume.set_value(vlc_volume / 100.000)
                Gdk.threads_leave()

                Gdk.threads_enter()
                self.__label_volume2.set_markup(
                    '<span font="{1}" color="white"> Vol: {0}% </span>'.format(vlc_volume, self.__height / 30.0))
                Gdk.threads_leave()

                Gdk.threads_enter()
                self.__label_volume2.show()
                Gdk.threads_leave()


            elif not self.__scales_box.get_property('visible') and self.__label_volume2.get_property('visible'):
                threading.Thread(target=self.__thread_hide_label, args=[self.__label_volume2]).start()

            """
                Update the progress scale
            """
            if self.__update__scale_progress and scale_progres_value != vlc_position:
                Gdk.threads_enter()
                self.__scale_progress.set_value(vlc_position)
                Gdk.threads_leave()

            """
                Verify if the window is on top
            """
            self.__vlc_widget.set_on_top(get_active_window_title() == self.__root_window.get_title())

            """
                Update the time of the player
            """
            if vlc_is_playing:
                video_length = format_milliseconds_to_time(self.__vlc_widget.player.get_length()) + "   "
                video_time = format_milliseconds_to_time(self.__vlc_widget.player.get_time())

                Gdk.threads_enter()
                self.__label_length.set_markup(
                    '<span font="{1}" color="white">{0}</span>'.format(video_length, self.__height / 29.0))
                Gdk.threads_leave()

                Gdk.threads_enter()
                self.__label_progress.set_markup(
                    '<span font="{1}" color="white">{0}</span>'.format(video_time, self.__height / 29.0))
                Gdk.threads_leave()
            else:
                video_length = self.__label_length.get_text().strip()
                video_time = self.__label_progress.get_text().strip()

            """
                Update the size of the widgets
            """

            if self.get_property('visible'):
                width, height = self.__root_window.get_size()

                if width != self.__width or height != self.__height:
                    self.__width = width
                    self.__height = height

                    Gdk.threads_enter()
                    self.__scale_progress.set_size_request(self.__width / 2, -1)
                    Gdk.threads_leave()

                    Gdk.threads_enter()
                    self.__label_volume2.set_markup(
                        '<span font="{1}" color="white"> Vol: {0}% </span>'.format(vlc_volume, self.__height / 30.0))
                    Gdk.threads_leave()

                    Gdk.threads_enter()
                    self.__label_length.set_markup(
                        '<span font="{1}" color="white">{0}</span>'.format(video_length, self.__height / 29.0))
                    Gdk.threads_leave()

                    Gdk.threads_enter()
                    self.__label_progress.set_markup(
                        '<span font="{1}" color="white">{0}</span>'.format(video_time, self.__height / 29.0))
                    Gdk.threads_leave()

                    # Gdk.threads_enter()
                    # self.__buttons_box.set_size_request(self.__height/28.0, -1)
                    # Gdk.threads_leave()

            else:
                if vlc_is_playing:
                    self.__vlc_widget.player.stop()

    def __on_key_pressed(self, _, ev):
        esc_key = 65307
        f11_key = 65480
        space_bar = 32
        #enter_key = 65293
        arrow_up = 65362
        arrow_down = 65364
        arrow_right = 65363
        arrow_left = 65361

        key = ev.keyval

        # display the toolbox if the arrows are shown
        if key == arrow_left or key == arrow_right:
            self.__vlc_widget._mouse_time = time.time()

        if key == esc_key:
            self.unfullscreen()

        elif key == f11_key:
            self.fullscreen()

        elif key == space_bar:
            self.__on_button_play_pause_clicked(None, None)

        elif key == arrow_up:
            self.__vlc_widget.volume_up()

        elif key == arrow_down:
            self.__vlc_widget.volume_down()

    def __scale_volume_changed(self, _, value):
        value = int(value * 100)

        self.__label_volume2.set_markup(
            '<span font="{1}" color="white"> Vol: {0}% </span>'.format(value, self.__height / 30.0))
        if self.__vlc_widget.player.audio_get_volume() != value:
            self.__vlc_widget.player.audio_set_volume(value)

    def __scale_button_press(self, *_):
        self.__update__scale_progress = False

    def __scale_button_release(self, *_):
        self.__vlc_widget.player.set_position(self.__scale_progress.get_value())
        self.__update__scale_progress = True

    def __on_button_restart_the_video(self, *_):
        self.__vlc_widget.player.set_position(0)

    def __on_button_end_the_video(self, *_):
        self.__vlc_widget.player.set_position(1)
        self.__stopped_position = 0

    @staticmethod
    def __delayed_method(delay, method, arg=None):

        time.sleep(delay)

        Gdk.threads_enter()
        if arg is None:
            _ = method()
        else:
            _ = method(arg)
        Gdk.threads_leave()

    def __start_video_at(self, position, start_at):
        """
            It is necessary to give some time to the player to start playing
            so the following methods can be applied.
            I chose 0.05 seconds
        """

        video_length = self.__vlc_widget.player.get_length()
        start_at = str(start_at).split('.')
        str_seconds = str(start_at[1])
        minutes = int(start_at[0])
        if len(str_seconds) == 1:
            seconds = int(str_seconds) * 10
        else:
            seconds = int(str_seconds)
        start_at = minutes * 60 + seconds

        if video_length > 0 and start_at > 0:
            video_length = video_length / 1000.000
            start_at_percent = start_at / video_length
        else:
            start_at_percent = 0
        if start_at_percent > position:
            start_time = start_at_percent
        elif position > 0:
            start_time = position
        else:
            start_time = 0

        if start_time > 0:
            Gdk.threads_enter()
            self.__vlc_widget.player.set_position(start_time)
            Gdk.threads_leave()

    def is_playing_or_paused(self):
        if self.__vlc_widget.is_playing() or self.__vlc_widget.is_paused():
            return True

        return False

    def quit(self):
        self.__vlc_widget.player.stop()
        self.__thread_player_activity_status = False
        self.__thread_mouse_motion_status = False
        turn_off_screensaver(False)

    def get_stopped_position(self):
        return self.__stopped_position

    def stop_position(self):
        self.__vlc_widget.player.stop()

    def get_position(self):
        return self.__vlc_widget.player.get_position()

    def get_state(self):
        return self.__vlc_widget.player.get_state()

    def play_video(self, file_path, position=0, subtitles_track=-2, audio_track=-2, start_at=0.0, thread=False):

        if os.path.exists(file_path):

            self.__stopped_position = position

            media = VLC_INSTANCE.media_new(file_path)
            media.parse()

            turn_off_screensaver(True)

            if thread:
                Gdk.threads_enter()
                self.__vlc_widget.player.set_media(media)
                Gdk.threads_leave()

                Gdk.threads_enter()
                self.__root_window.set_title(media.get_meta(0))
                Gdk.threads_leave()

                Gdk.threads_enter()
                self.__vlc_widget.player.play()
                Gdk.threads_leave()

                if not self.get_property('visible'):
                    Gdk.threads_enter()
                    self.show_all()
                    Gdk.threads_leave()
            else:
                self.__vlc_widget.player.set_media(media)
                self.__root_window.set_title(media.get_meta(0))
                self.__vlc_widget.player.play()
                if not self.get_property('visible'):
                    self.show_all()

            threading.Thread(target=self.__start_video_at, args=[position, start_at]).start()

            if subtitles_track == -1 or subtitles_track >= 0:
                threading.Thread(target=self.__delayed_method, args=[0.05,
                                                                     self.__vlc_widget.player.video_set_spu,
                                                                     subtitles_track]
                                 ).start()

            if audio_track > -2:
                threading.Thread(target=self.__delayed_method, args=[0.05,
                                                                     self.__vlc_widget.player.audio_set_track,
                                                                     audio_track]
                                 ).start()


class MediaPlayer(Gtk.Window):
    """ This class creates a media player built in a Gtk.Window """

    def __init__(self):

        super().__init__()

        self.__media_player_widget = MediaPlayerWidget(self)
        self.add(self.__media_player_widget)

        self.connect('delete-event', self.quit)

        self.set_size_request(600, 300)
        self.show_all()

    def quit(self, *_):
        self.__media_player_widget.quit()
        Gtk.main_quit()

    def play_video(self, path):
        self.__media_player_widget.play_video(path)


if __name__ == '__main__':

    GObject.threads_init()
    Gdk.threads_init()

    player = MediaPlayer()
    player.play_video('/home/cadweb/Downloads/Seed/InkMaster/Ink.Master.S15E06.1080p.WEB.h264-EDITH[eztv.re].mkv')
    Gtk.main()
    VLC_INSTANCE.release()

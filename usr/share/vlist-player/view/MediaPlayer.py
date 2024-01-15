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
from time import time, sleep
from datetime import timedelta
from threading import Thread, current_thread

gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')
from gi.repository import Gtk, GObject, Gdk

_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_PROJECT_DIR = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_DIR)

from Paths import *
from controller import vlc
from view.VLCWidget import VLCWidget, VLC_INSTANCE
from system_utils import EventCodes, turn_off_screensaver

def format_milliseconds_to_time(number):
    time_string = str(timedelta(milliseconds=number)).split('.')[0]

    # remove the hours if they are not necessary
    try:
        if int(time_string.split(':', 1)[0]) == 0:
            time_string = time_string.split(':', 1)[1]
    except Exception:
        pass

    return time_string


def format_track(track):
    """ Format the tracks provided by pyVLC. Track must be a tuple (int, string)"""

    number = str(track[0])

    try:
        content = track[1].strip().replace('[', '').replace(']', '').replace('_', ' ').title()
    except Exception as e:
        content = track[1]
        print(str(e))

    if len(number) == 0:
        numb = '  '
    elif len(number) == 1:
        numb = ' {}'.format(number)
    else:
        numb = str(number)

    return ' {}   {}'.format(numb, content)


def gtk_file_chooser(parent, start_path=''):
    window_choose_file = Gtk.FileChooserDialog('Video List Player',
                                               parent,
                                               Gtk.FileChooserAction.OPEN,
                                               (Gtk.STOCK_CANCEL,
                                                Gtk.ResponseType.CANCEL,
                                                Gtk.STOCK_OPEN,
                                                Gtk.ResponseType.OK))

    window_choose_file.set_default_response(Gtk.ResponseType.NONE)
    window_choose_file.set_icon_from_file(ICON_LOGO_SMALL)
    window_choose_file.set_transient_for(parent)

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


class MediaPlayerWidget(Gtk.Overlay):
    __gtype_name__ = 'MediaPlayerWidget'

    def __init__(self, root_window):

        super().__init__()

        self.__root_window = root_window
        self.__has_media = False
        self.__widgets_shown = True
        self.__motion_time = time()
        self.__volume_increment = 3  # %
        self.__width = 600
        self.__height = 300
        self.__update__scale_progress = True

        self.__vlc_widget = VLCWidget(self.__root_window)
        self.__vlc_widget.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#000000'))
        self.__vlc_widget.connect("draw", self.__redraw_bg)
        self.add(self.__vlc_widget)

        # Signals
        self.__vlc_widget.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.__vlc_widget.connect('motion_notify_event', self.__on_motion_notify_event)

        self.__vlc_widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.__vlc_widget.connect('button-press-event', self.__on_mouse_button_press)

        self.__vlc_widget.add_events(Gdk.EventMask.SCROLL_MASK)
        self.__vlc_widget.connect('scroll_event', self.__on_mouse_scroll)

        self.__root_window.connect('key-press-event', self.__on_key_pressed)

        # Buttons Box
        self.__buttons_box = Gtk.Box()
        self.__buttons_box.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self.__buttons_box.set_valign(Gtk.Align.END)
        self.__buttons_box.set_halign(Gtk.Align.CENTER)
        self.add_overlay(self.__buttons_box)

        self.__button_restart = Gtk.ToolButton(stock_id=Gtk.STOCK_MEDIA_PREVIOUS)
        self.__button_restart.connect('clicked', self.__on_button_restart_the_video)
        self.__button_restart.set_can_focus(False)
        self.__buttons_box.pack_start(self.__button_restart, True, True, 3)

        self.__button_play_pause = Gtk.ToolButton(stock_id=Gtk.STOCK_MEDIA_PLAY)
        self.__button_play_pause.connect('clicked', self.__on_button_play_pause_clicked)
        self.__button_play_pause.set_can_focus(False)
        self.__buttons_box.pack_start(self.__button_play_pause, True, True, 3)

        self.__button_end_video = Gtk.ToolButton(stock_id=Gtk.STOCK_MEDIA_NEXT)
        self.__button_end_video.connect('clicked', self.__on_button_end_the_video)
        self.__button_end_video.set_can_focus(False)
        self.__buttons_box.pack_start(self.__button_end_video, True, True, 3)

        self.__label_progress = Gtk.Label()
        self.__label_progress.set_markup('<span font="{0}" color="white">00:00:00</span>'.format(self.__height / 29.0))
        self.__label_progress.set_margin_end(5)
        self.__label_progress.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self.__buttons_box.pack_start(self.__label_progress, True, True, 3)

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
        self.__buttons_box.pack_start(self.__scale_progress, True, True, 1)

        self.__label_length = Gtk.Label()
        self.__label_length.set_markup('<span font="{0}" color="white">00:00:00</span>'.format(self.__height / 29.0))
        self.__label_length.set_margin_end(5)
        self.__label_length.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self.__buttons_box.pack_start(self.__label_length, True, True, 3)

        self.__scale_volume = Gtk.VolumeButton()
        self.__scale_volume.connect('value_changed', self.__scale_volume_changed)
        self.__buttons_box.pack_start(self.__scale_volume, True, True, 3)

        #   Extra volume label
        self.__label_volume = Gtk.Label()
        self.__label_volume.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self.__label_volume.set_markup(
            '<span font="{1}" color="white"> Vol: {0}% </span>'.format(0, self.__height / 30.0))
        self.__label_volume.set_valign(Gtk.Align.START)
        self.__label_volume.set_halign(Gtk.Align.END)
        self.add_overlay(self.__label_volume)

        """
            Init the threads
        """
        self.__thread_player_activity = Thread(target=self.__on_thread_player_activity)
        self.__thread_player_activity.start()

        self.__thread_scan_motion = Thread(target=self.__on_thread_scan_motion)
        self.__thread_scan_motion.start()

    def hide_controls(self):
        self.__buttons_box.hide()
        self.__buttons_box.hide()
        self.__label_volume.hide()

    def stop(self):
        self.__vlc_widget.player.stop()

    def get_position(self):
        return self.__vlc_widget.player.get_position()

    def get_state(self):
        return self.__vlc_widget.player.get_state()

    def is_playing(self):
        if self.get_state() == vlc.State.Playing:
            return True

        return False

    def is_paused(self):
        if self.get_state() == vlc.State.Paused:
            return True

        return False

    def volume_up(self):
        actual_volume = self.__vlc_widget.player.audio_get_volume()
        if actual_volume + self.__volume_increment <= 100:
            self.__vlc_widget.player.audio_set_volume(actual_volume + self.__volume_increment)
        else:
            self.__vlc_widget.player.audio_set_volume(100)

    def volume_down(self):
        actual_volume = self.__vlc_widget.player.audio_get_volume()
        if actual_volume >= self.__volume_increment:
            self.__vlc_widget.player.audio_set_volume(actual_volume - self.__volume_increment)
        else:
            self.__vlc_widget.player.audio_set_volume(0)

    def set_subtitles_from_file(self, *_):
        """
            Todo: read the result of player.video_set_subtitle_file(path) and display a message
            in case of problem.
        """
        path = gtk_file_chooser(self.__root_window)

        if path is not None:
            self.__vlc_widget.player.video_set_subtitle_file(path)

        return True

    def play_video(self,
                   file_path,
                   position=0,
                   subtitles_track=-2,
                   audio_track=-2,
                   start_at=0.0,
                   thread=False):

        if not os.path.exists(file_path):
            return

        media = VLC_INSTANCE.media_new(file_path)
        media.parse()

        self.__has_media = True

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

        Thread(target=self.__start_video_at, args=[position, start_at]).start()

        if subtitles_track == -1 or subtitles_track >= 0:
            Thread(target=self.__delayed_method, args=[0.05,
                                                       self.__vlc_widget.player.video_set_spu,
                                                       subtitles_track]
                   ).start()

        if audio_track > -2:
            Thread(target=self.__delayed_method, args=[0.05,
                                                       self.__vlc_widget.player.audio_set_track,
                                                       audio_track]
                   ).start()

    def quit(self):

        self.__vlc_widget.player.stop()

        self.__thread_scan_motion.do_run = False
        self.__thread_player_activity.do_run = False

        turn_off_screensaver(False)

    def join(self):
        self.__thread_player_activity.join()
        self.__thread_scan_motion.join()

    @staticmethod
    def __thread_hide_label(label):
        sleep(1.5)
        Gdk.threads_enter()
        label.hide()
        Gdk.threads_leave()

    def __scale_volume_changed(self, _, value):
        value = int(value * 100)

        self.__label_volume.set_markup(
            '<span font="{1}" color="white"> Vol: {0}% </span>'.format(value, self.__height / 30.0))
        if self.__vlc_widget.player.audio_get_volume() != value:
            self.__vlc_widget.player.audio_set_volume(value)

    def __scale_button_press(self, *_):
        self.__update__scale_progress = False

    def __scale_button_release(self, *_):
        self.__vlc_widget.player.set_position(self.__scale_progress.get_value())
        self.__update__scale_progress = True

    def __on_thread_scan_motion(self, *_):

        this_thread = current_thread()

        while getattr(this_thread, "do_run", True):

            time_delta = time() - self.__motion_time

            if time_delta > 3 and self.__widgets_shown:
                self.__widgets_shown = False
                Gdk.threads_enter()
                self.__label_volume.hide()
                self.__buttons_box.hide()
                Gdk.threads_leave()

            sleep(.5)

    def __on_menu_video_subs_audio(self, _, player_type, track):
        """
            Todo: self.__vlc_widget.player.XXX_set_track returns a status.
            It would be good to read the status and display a message in case of problem.
        """
        if player_type == 0:
            self.__vlc_widget.player.audio_set_track(track)

        elif player_type == 1:
            self.__vlc_widget.player.video_set_track(track)

        elif player_type == 2:
            self.__vlc_widget.player.video_set_spu(track)

    def __on_button_player_stop(self, *_):
        self.__stopped_position = self.__vlc_widget.player.get_position()
        self.__vlc_widget.player.stop()
        turn_off_screensaver(False)
        self.hide()

    def __on_button_play_pause_clicked(self, *_):
        if not self.is_playing():
            self.__button_play_pause.set_stock_id('gtk-media-pause')
            self.__vlc_widget.player.play()
            turn_off_screensaver(True)
        else:
            self.__button_play_pause.set_stock_id('gtk-media-play')
            self.__vlc_widget.player.pause()
            turn_off_screensaver(False)

    def __on_thread_player_activity(self):
        """
            This method scans the state of the player to update the tool buttons, volume, play-stop etc
        """

        this_thread = current_thread()

        while getattr(this_thread, "do_run", True):

            vlc_is_playing = self.is_playing()
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
                self.__label_volume.set_markup(
                    '<span font="{1}" color="white"> Vol: {0}% </span>'.format(vlc_volume, self.__height / 30.0))
                Gdk.threads_leave()

                Gdk.threads_enter()
                self.__label_volume.show()
                Gdk.threads_leave()


            elif not self.__buttons_box.get_property('visible') and self.__label_volume.get_property('visible'):
                Thread(target=self.__thread_hide_label, args=[self.__label_volume]).start()

            """
                Update the progress scale
            """
            if self.__update__scale_progress and scale_progres_value != vlc_position:
                Gdk.threads_enter()
                self.__scale_progress.set_value(vlc_position)
                Gdk.threads_leave()

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
                    self.__label_volume.set_markup(
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

            else:
                if vlc_is_playing:
                    self.__vlc_widget.player.stop()
            """

            sleep(0.2)

    def __on_key_pressed(self, _, event):

        key = event.keyval

        if key == EventCodes.Keyboard.f11 and self.__has_media:
            self.__root_window.fullscreen()

        elif Gdk.WindowState.FULLSCREEN & self.__root_window.get_window().get_state():

            # display the toolbox if the arrows are shown
            if key in (EventCodes.Keyboard.arrow_left, EventCodes.Keyboard.arrow_right):
                self.__motion_time = time()

            if key == EventCodes.Keyboard.esc:
                self.__root_window.unfullscreen()

            elif key in (EventCodes.Keyboard.space_bar, EventCodes.Keyboard.enter):
                self.__on_button_play_pause_clicked(None, None)

            elif key == EventCodes.Keyboard.arrow_up:
                self.volume_up()

            elif key == EventCodes.Keyboard.arrow_down:
                self.volume_down()

    def __on_button_restart_the_video(self, *_):
        self.__vlc_widget.player.set_position(0)

    def __on_button_end_the_video(self, *_):
        self.__vlc_widget.player.set_position(1)
        self.__stopped_position = 0

    def __vlc_rc_menu(self, event):

        menu = Gtk.Menu()

        """
            Audio Menu
        """
        state = self.__root_window.get_window().get_state()

        if Gdk.WindowState.FULLSCREEN & state:
            menuitem = Gtk.ImageMenuItem(label="Un-Fullscreen")
            menuitem.connect('activate', self.__unfullscreen)
        else:
            menuitem = Gtk.ImageMenuItem(label="Fullscreen")
            menuitem.connect('activate', self.__fullscreen)

        menu.append(menuitem)

        """
            Audio Menu
        """
        menuitem = Gtk.ImageMenuItem(label="Audio")
        menu.append(menuitem)
        submenu = Gtk.Menu()
        menuitem.set_submenu(submenu)

        selected_track = self.__vlc_widget.player.audio_get_track()

        item = Gtk.CheckMenuItem(label="-1  Disable")
        item.connect('activate', self.__on_menu_video_subs_audio, 0, -1)
        if selected_track == -1:
            item.set_active(True)

        submenu.append(item)

        try:
            tracks = [(audio[0], audio[1].decode('utf-8')) for audio in
                      self.__vlc_widget.player.audio_get_track_description()]
        except Exception as e:
            tracks = self.__vlc_widget.player.audio_get_track_description()
            print(str(e))

        for track in tracks:
            if 'Disable' not in track:
                item = Gtk.CheckMenuItem(label=format_track(track))
                item.connect('activate', self.__on_menu_video_subs_audio, 0, track[0])
                if selected_track == track[0]:
                    item.set_active(True)
                submenu.append(item)

        """
            Subtitles
        """
        menuitem = Gtk.ImageMenuItem(label="Subtitles")
        menu.append(menuitem)
        submenu = Gtk.Menu()
        menuitem.set_submenu(submenu)

        selected_track = self.__vlc_widget.player.video_get_spu()

        item = Gtk.CheckMenuItem(label="-1  Disable")
        item.connect('activate', self.__on_menu_video_subs_audio, 2, -1)
        if selected_track == -1:
            item.set_active(True)

        submenu.append(item)

        try:
            tracks = [(video_spu[0], video_spu[1].decode('utf-8')) for video_spu in
                      self.__vlc_widget.player.video_get_spu_description()]
        except Exception as e:
            tracks = self.__vlc_widget.player.video_get_spu_description()
            print(str(e))

        for track in tracks:
            if 'Disable' not in track:
                item = Gtk.CheckMenuItem(label=format_track(track))
                item.connect('activate', self.__on_menu_video_subs_audio, 2, track[0])
                if selected_track == track[0]:
                    item.set_active(True)
                submenu.append(item)

        menu.show_all()
        menu.popup(None, None, None, None, event.button, event.time)
        return True

    def __on_motion_notify_event(self, *_):
        self.__motion_time = time()

        if not self.__widgets_shown and self.__has_media:
            self.__widgets_shown = True
            self.__buttons_box.show()
            self.__label_volume.show()

    def __on_mouse_button_press(self, _, event):

        if not self.__has_media:
            return

        elif event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == EventCodes.Cursor.left_click:
                if Gdk.WindowState.FULLSCREEN & self.__root_window.get_window().get_state():
                    self.__root_window.unfullscreen()
                else:
                    self.__root_window.fullscreen()

        elif event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == EventCodes.Cursor.left_click:

                if self.is_playing():
                    self.__vlc_widget.player.pause()
                    turn_off_screensaver(False)
                else:
                    self.__vlc_widget.player.play()
                    turn_off_screensaver(True)

            elif event.button == EventCodes.Cursor.right_click:
                self.__vlc_rc_menu(event)

    @staticmethod
    def __delayed_method(delay, method, arg=None):

        sleep(delay)

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

    def __on_mouse_scroll(self, _, event):

        if not self.__has_media:
            return

        elif event.direction == Gdk.ScrollDirection.UP:
            self.volume_down()

        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.volume_up()

    @staticmethod
    def __redraw_bg(_, cairo_ctx):
        """To redraw the black background when resized"""
        cairo_ctx.set_source_rgb(0, 0, 0)
        cairo_ctx.paint()

    def __fullscreen(self, *_):
        """This is only for the Gtk.Menu"""
        self.__root_window.fullscreen()

    def __unfullscreen(self, *_):
        """This is only for the Gtk.Menu"""
        self.__root_window.unfullscreen()


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

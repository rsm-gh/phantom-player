#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
    Patch:
        + The control buttons had different sized, and It seems that in GTK3 it was not possible to use
          `ToolButton.set_image`, to properly size all the images, I used a MenuButton(). The sizing works, but it's needed then to:
            1) only listen when the button is active.
            2) de-active the button.
"""

import os
import threading

import vlc
from time import time, sleep
from datetime import timedelta
from threading import Thread, current_thread
from gi.repository import Gtk, GObject, Gdk, GLib

import vlc_utils
from console_printer import print_debug
from model.Playlist import Track, TimeValue
from view import gtk_utils
from view.VLCWidget import VLCWidget
from system_utils import EventCodes, turn_off_screensaver
from settings import ThemeButtons
from Texts import Texts

_VOLUME_LABEL_NONE = " Muted "
_VOLUME_LABEL = " Vol: {}% "
_EMPTY__VIDEO_LENGTH = "00:00"
_DEFAULT_CSS = """
scale, label, box {
    background-color: @theme_bg_color;
}
"""

_MAX_PARSE_TIMEOUT = 5000  # in milliseconds


def format_milliseconds_to_time(number):
    if number <= 0:
        return _EMPTY__VIDEO_LENGTH

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
        content = " ".join(track[1].replace('_', ' ').split()).replace('[', '').replace(']', '').title().strip()

        if 'Track' in content and "-" in content:
            content = content.split('-', 1)[1].strip()

        if content.startswith("Track "):
            content = "Track {}".format(number)

    except Exception as e:
        content = track[1]
        print(track)
        print(str(e))

    if len(number) == 0:
        numb = '  '
    elif len(number) == 1:
        numb = '  {}'.format(number)
    else:
        numb = str(number)

    return '{}:   {}'.format(numb, content)


class WidgetsShown:
    _none = 0
    _volume = 1
    _toolbox = 2


class CustomSignals:
    _paused = 'paused'
    _play = 'play'
    _stop = 'stop'
    _time_changed = 'time-changed'
    _video_restart = 'video-restart'
    _video_end = 'video-end'
    _btn_random_toggled = 'btn-random-clicked'
    _btn_keep_playing_toggled = 'btn-keep-playing-clicked'


class DelayedMediaData:
    def __init__(self, start_at, sub_track, audio_track, play):
        # To be used when the video is being loaded.
        self._start_at = start_at
        self._sub_track = sub_track
        self._audio_track = audio_track
        self._play = play

        # To be defined after the video is loaded.
        self._video_settings_loaded = False

    def set_video_settings_loaded(self, value):
        self._video_settings_loaded = value

    def set_sub_track(self, value):
        self._sub_track = value

    def set_audio_track(self, value):
        self._audio_track = value


class VideoScanStatus:
    _none = 0
    _scan = 2


class MediaPlayerWidget(Gtk.Box):
    __gtype_name__ = 'MediaPlayerWidget'

    def __init__(self,
                 root_window,
                 random_button=False,
                 keep_playing_button=False,
                 un_max_fixed_toolbar=True,
                 volume_level=35):
        """
             un_max_fixed_toolbar: Automatically hide the toolbar when the window is un-maximized
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.__delayed_media_data = None
        self.__window_root = root_window
        self.__motion_time = time()
        self.__scale_progress_pressed = False
        self.__hidden_controls = False
        self.__media = None
        self.__volume = -1
        self.__video_is_loaded = False
        self.__video_ended = False
        self.__was_playing_before_press = False
        self.__video_status_before_press = VideoScanStatus._none
        self.__menuitem_subtitles_activated = None
        self.__menuitem_subtitles_file = None
        self.__emitted_time = -1
        self.__un_maximized_fixed_toolbar = un_max_fixed_toolbar
        self.__widgets_shown = WidgetsShown._toolbox

        display = self.get_display()
        self.__empty_cursor = Gdk.Cursor.new_from_name(display, 'none')
        self.__default_cursor = Gdk.Cursor.new_from_name(display, 'default')

        #
        # Root Window controllers
        #

        if un_max_fixed_toolbar:
            # It is important to add the motion_notify to the root_window, instead of the VLC widget
            # to avoid hiding-it on un-maximized mode.
            self.__window_root.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
            self.__window_root.connect('motion_notify_event', self.__on_motion_notify_event)

        self.__window_root.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.__window_root.connect('key-press-event', self.__on_window_root_key_pressed)

        #
        # VLC Widget
        #
        self.__vlc_widget = VLCWidget()

        self.__vlc_widget.add_events(Gdk.EventMask.SCROLL_MASK)
        self.__vlc_widget.connect('scroll_event', self.__on_player_scroll)

        self.__vlc_widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.__vlc_widget.connect('button-press-event', self.__on_player_press)

        if not un_max_fixed_toolbar:
            self.__vlc_widget.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
            self.__vlc_widget.connect('motion_notify_event', self.__on_motion_notify_event)

        # Player events
        event_manager = self.__vlc_widget._player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self.__on_player_time_changed)
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.__on_player_end_reached)
        # event_manager.event_attach(vlc.EventType.MediaParsedChanged, self.__on_player_parse_changed)

        # Buttons Box
        self.__buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                     sensitive=False,
                                     valign=Gtk.Align.END,
                                     halign=Gtk.Align.FILL)

        self.__menubutton_restart = self.__add_menu_button(ThemeButtons._previous,
                                                           Texts.MediaPlayer.Tooltip._start,
                                                           self.__on_menubutton_restart_clicked)

        self.__menubutton_play = self.__add_menu_button(ThemeButtons._play,
                                                        Texts.MediaPlayer.Tooltip._play,
                                                        self.__on_menubutton_play_clicked)

        self.__menubutton_next = self.__add_menu_button(ThemeButtons._next,
                                                        Texts.MediaPlayer.Tooltip._end,
                                                        self.__on_menubutton_end_clicked)

        self.__scale_progress = Gtk.Scale(hexpand=True, draw_value=False)
        self.__scale_progress.set_range(0, 0)  # If no video is loaded, disable the scale

        self.__scale_progress.connect('button-press-event', self.__on_scale_progress_press)
        self.__scale_progress.connect('button-release-event', self.__on_scale_progress_release)

        self.__scale_progress.connect('value-changed', self.__on_scale_progress_value_changed)
        self.__buttons_box.pack_start(child=self.__scale_progress, expand=True, fill=True, padding=3)

        self.__label_video_progress = Gtk.Label(label=_EMPTY__VIDEO_LENGTH,
                                                margin_start=5,
                                                margin_end=5,
                                                xalign=1)
        self.__buttons_box.pack_start(self.__label_video_progress, expand=False, fill=False, padding=0)

        self.__label_video_length = Gtk.Label(label=" / " + _EMPTY__VIDEO_LENGTH,
                                              margin_start=5,
                                              margin_end=5,
                                              xalign=0)
        self.__buttons_box.pack_start(self.__label_video_length, expand=False, fill=False, padding=0)

        if keep_playing_button:
            self.__button_keep_playing = self.__add_menu_button(ThemeButtons._keep_playing,
                                                                Texts.MediaPlayer.Tooltip._keep_playing,
                                                                self.__on_menubutton_keep_playing_toggled)
        else:
            self.__button_keep_playing = None

        if random_button:
            self.__button_random = self.__add_menu_button(ThemeButtons._random,
                                                          Texts.MediaPlayer.Tooltip._random,
                                                          self.__on_menubutton_random_toggled)

        else:
            self.__button_random = None

        self.__menubutton_settings = Gtk.MenuButton(direction=Gtk.ArrowType.UP,
                                                    tooltip_text=Texts.MediaPlayer.Tooltip._tracks)
        self.__menubutton_settings.set_relief(Gtk.ReliefStyle.NONE)
        self.__menubutton_settings.set_image(Gtk.Image.new_from_icon_name(ThemeButtons._settings, Gtk.IconSize.BUTTON))
        self.__buttons_box.pack_start(self.__menubutton_settings, expand=False, fill=False, padding=3)

        self.__button_volume = Gtk.VolumeButton(icons=ThemeButtons._volume)
        self.__button_volume.connect('value-changed', self.__on_button_volume_changed)

        self.__buttons_box.pack_start(self.__button_volume, expand=False, fill=False, padding=3)

        self.__menubutton_fullscreen = self.__add_menu_button(ThemeButtons._fullscreen,
                                                              Texts.MediaPlayer.Tooltip._fullscreen,
                                                              self.__on_menubutton_fullscreen_clicked)

        gtk_utils.set_css(self.__buttons_box, _DEFAULT_CSS)

        #   Extra volume label
        self.__label_volume = Gtk.Label(valign=Gtk.Align.START,
                                        halign=Gtk.Align.END,
                                        margin_start=5,
                                        margin_end=5)
        gtk_utils.set_css(self.__label_volume, _DEFAULT_CSS)
        self.__set_volume(volume_level)

        #
        # Overlay
        #
        self.__overlay = Gtk.Overlay(vexpand=True,
                                     hexpand=True)
        # The overlay must be added before the buttons box in case of self.__un_maximized_fixed_toolbar
        self.pack_start(self.__overlay, expand=True, fill=True, padding=0)

        self.__overlay.add(self.__vlc_widget)
        self.__overlay.add_overlay(self.__label_volume)

        if self.__un_maximized_fixed_toolbar:
            self.__set_fullscreen(False)
        else:
            self.__overlay.add_overlay(self.__buttons_box)

        #
        # Create the custom signals
        #
        GObject.signal_new(CustomSignals._paused,
                           self, GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           ())
        GObject.signal_new(CustomSignals._play,
                           self,
                           GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           ())
        GObject.signal_new(CustomSignals._stop,
                           self,
                           GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           ())
        GObject.signal_new(CustomSignals._video_end,
                           self,
                           GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           (bool, bool))  # forced, was playing
        GObject.signal_new(CustomSignals._video_restart,
                           self, GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           ())
        GObject.signal_new(CustomSignals._time_changed,
                           self,
                           GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           (int,))
        GObject.signal_new(CustomSignals._btn_random_toggled,
                           self,
                           GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           (bool,))
        GObject.signal_new(CustomSignals._btn_keep_playing_toggled,
                           self,
                           GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE, (bool,))

        #
        #    Init the threads
        #
        self.__thread_scan_motion = Thread(target=self.__on_thread_motion_activity)
        self.__thread_scan_motion.start()

    def has_media(self):
        return self.__media is not None

    def play_pause(self):
        if self.is_playing():
            self.pause()
        else:
            self.play()

    def play(self, from_scale=True):
        """
            from_scale: if the video should start playing at the scale position.
        """

        if self.__media is None:
            self.__menubutton_play.set_active(False)
            raise ValueError('Attempting to play without media.')

        if from_scale and self.__scale_progress.get_value() == self.__scale_progress.get_adjustment().get_upper():
            self.__scale_progress.set_value(0)

        if self.__vlc_widget._player.will_play() == 0 or self.__video_ended or not self.__video_is_loaded:
            threading.Thread(target=self.__on_thread_set_video, args=[True, from_scale]).start()
        else:
            self.__vlc_widget._player.play()

        self.__menubutton_play.set_image(Gtk.Image.new_from_icon_name(ThemeButtons._pause, Gtk.IconSize.BUTTON))
        self.__menubutton_play.set_tooltip_text(Texts.MediaPlayer.Tooltip._pause)

        turn_off_screensaver(True)
        self.emit(CustomSignals._play)

    def pause(self, emit=True):
        self.__menubutton_play.set_image(Gtk.Image.new_from_icon_name(ThemeButtons._play, Gtk.IconSize.BUTTON))
        self.__menubutton_play.set_tooltip_text(Texts.MediaPlayer.Tooltip._play)
        self.__vlc_widget._player.pause()
        turn_off_screensaver(False)
        if emit:
            self.emit(CustomSignals._paused)

    def stop(self):
        self.__vlc_widget._player.stop()
        self.__menubutton_play.set_image(Gtk.Image.new_from_icon_name(ThemeButtons._play, Gtk.IconSize.BUTTON))
        self.__menubutton_play.set_tooltip_text(Texts.MediaPlayer.Tooltip._play)
        self.__scale_progress.set_range(0, 0)  # If no video loaded, disable the scale
        self.__buttons_box.set_sensitive(False)
        self.__label_video_progress.set_text(_EMPTY__VIDEO_LENGTH)
        self.__label_video_length.set_text(" / " + _EMPTY__VIDEO_LENGTH)
        self.__label_volume.hide()
        self.__scale_progress.set_value(0)
        self.__media = None
        self.__emitted_time = -1
        self.emit(CustomSignals._stop)

    def is_playing(self):
        return self.get_state() == vlc.State.Playing

    def is_paused(self):
        return self.get_state() == vlc.State.Paused

    def is_nothing(self):
        return self.get_state() == vlc.State.NothingSpecial

    def volume_up(self):
        new_volume = self.__volume + 1
        if new_volume <= 100:
            self.__set_volume(new_volume)

    def volume_down(self):
        new_volume = self.__volume - 1
        if new_volume >= 0:
            self.__set_volume(new_volume)

    def hide_controls(self):
        self.__buttons_box.hide()
        self.__buttons_box.hide()
        self.__label_volume.hide()
        self.__widgets_shown = WidgetsShown._none

    def display_playlist_controls(self, show=True):

        if self.__button_random is not None:
            if show:
                self.__button_random.show()
            else:
                self.__button_random.hide()

        if self.__button_keep_playing is not None:
            if show:
                self.__button_keep_playing.show()
            else:
                self.__button_keep_playing.hide()

    def hide_volume_label(self):
        self.__label_volume.hide()

    def quit(self):
        self.stop()

        turn_off_screensaver(False)

        self.__thread_scan_motion.do_run = False
        self.__thread_scan_motion.join()

        vlc_utils.release()

    def set_video(self,
                  file_path,
                  start_at=TimeValue._minium,
                  subtitles_track=Track.Value._undefined,
                  audio_track=Track.Value._undefined,
                  play=True):

        self.__media = None
        self.__video_ended = False
        self.__video_is_loaded = False
        self.__menuitem_subtitles_activated = None
        self.__menuitem_subtitles_file = None
        self.__emitted_time = -1

        GLib.idle_add(self.__buttons_box.set_sensitive, False),
        GLib.idle_add(self.__menubutton_settings.set_sensitive, False)
        GLib.idle_add(self.__label_video_progress.set_text, _EMPTY__VIDEO_LENGTH)
        GLib.idle_add(self.__label_video_length.set_text, " / " + _EMPTY__VIDEO_LENGTH)
        #  self.__scale_progress.set_value is not updated here to avoid blinking the GUI.

        GLib.idle_add(self.__vlc_widget._player.stop)  # To remove any previous video

        if not os.path.exists(file_path):
            return

        self.__media = vlc_utils.parse_media(file_path=file_path)

        # Patch 001: Some actions will be performed when the video length be properly parsed
        self.__delayed_media_data = DelayedMediaData(start_at=int(start_at * 1000),
                                                     sub_track=subtitles_track,
                                                     audio_track=audio_track,
                                                     play=play)

        if play:
            self.play(from_scale=False)
        else:
            threading.Thread(target=self.__on_thread_set_video, args=[False, False]).start()

    def set_random(self, state):
        self.__button_random.set_active(state)

    def set_keep_playing(self, state):
        self.__button_keep_playing.set_active(state)

    def get_state(self):
        return self.__vlc_widget._player.get_state()

    def get_random(self):
        if self.__button_random is None:
            return False

        return self.__button_random.get_active()

    def get_keep_playing(self):
        if self.__button_keep_playing is None:
            return False

        return self.__button_keep_playing.get_active()

    def __end_video(self, forced):

        if forced:
            was_playing = self.is_playing()
        else:
            was_playing = True

        self.__video_ended = True
        self.__video_is_loaded = False

        self.pause()
        self.__vlc_widget._player.stop()

        GLib.idle_add(self.__set_scale_progress_end)

        self.emit(CustomSignals._video_end, forced, was_playing)

        self.__menubutton_next.set_active(False)

    def __add_menu_button(self, icon_name, tooltip, on_toggle):
        """
            It's important to use MenuButtons instead ToolButtons or
            set_image will miss, and the icons will have different sizes
            than the VolumeButton.
        """
        button = Gtk.MenuButton(sensitive=True,
                                tooltip_text=tooltip)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_image(Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON))
        button.connect('toggled', on_toggle)
        self.__buttons_box.pack_start(button, expand=False, fill=False, padding=3)

        return button

    def __populate_settings_menubutton(self):

        menu = Gtk.Menu()
        self.__menubutton_settings.set_popup(menu)

        #
        # Audio Menu
        #
        menuitem = Gtk.MenuItem(label="Audio")
        menu.append(menuitem)
        submenu = Gtk.Menu()
        menuitem.set_submenu(submenu)

        selected_track = self.__vlc_widget._player.audio_get_track()

        try:
            tracks = [(audio[0], audio[1].decode('utf-8')) for audio in
                      self.__vlc_widget._player.audio_get_track_description()]
        except Exception as e:
            tracks = self.__vlc_widget._player.audio_get_track_description()
            print(str(e))

        default_item = Gtk.RadioMenuItem(label="-1:  Disable")
        if selected_track == -1:
            default_item.set_active(True)
        default_item.connect('activate', self.__on_menuitem_track_activate, Track.Type._audio, -1)
        submenu.append(default_item)

        for track in tracks:
            if 'Disable' in track:
                continue

            item = Gtk.RadioMenuItem(label=format_track(track))
            item.connect('activate', self.__on_menuitem_track_activate, Track.Type._audio, track[0])
            item.join_group(default_item)

            if selected_track == track[0]:
                item.set_active(True)
            submenu.append(item)

        #
        # Subtitles
        #
        menuitem = Gtk.MenuItem(label="Subtitles")
        menu.append(menuitem)
        submenu = Gtk.Menu()
        menuitem.set_submenu(submenu)

        selected_track = self.__vlc_widget._player.video_get_spu()

        default_item = Gtk.RadioMenuItem(label="-1:  Disable")
        if selected_track == -1:
            default_item.set_active(True)
            self.__menuitem_subtitles_activated = default_item
        default_item.connect('activate', self.__on_menuitem_track_activate, Track.Type._subtitles, -1)
        submenu.append(default_item)

        try:
            tracks = [(video_spu[0], video_spu[1].decode('utf-8')) for video_spu in
                      self.__vlc_widget._player.video_get_spu_description()]
        except Exception as e:
            tracks = self.__vlc_widget._player.video_get_spu_description()
            print(str(e))

        for track in tracks:
            if 'Disable' in track:
                continue

            item = Gtk.RadioMenuItem(label=format_track(track))
            item.join_group(default_item)
            if selected_track == track[0]:
                item.set_active(True)
                self.__menuitem_subtitles_activated = item
            item.connect('activate', self.__on_menuitem_track_activate, Track.Type._subtitles, track[0])
            submenu.append(item)

        self.__menuitem_subtitles_file = Gtk.RadioMenuItem(label="From file...")
        self.__menuitem_subtitles_file.join_group(default_item)
        self.__menuitem_subtitles_file.connect('activate', self.__on_menuitem_file_subs_activate)
        submenu.append(self.__menuitem_subtitles_file)

        menu.show_all()
        self.__menubutton_settings.set_sensitive(True)
        self.__delayed_media_data.set_video_settings_loaded(True)

    def __set_volume(self, value=None, display_label=True, update_button=True):

        if self.__volume != value:

            self.__volume = value

            if value > 0:
                self.__label_volume.set_text(_VOLUME_LABEL.format(value))
            else:
                self.__label_volume.set_text(_VOLUME_LABEL_NONE)

            self.__vlc_widget._player.audio_set_volume(value)

            if update_button:
                if value <= 0:
                    value = 0
                else:
                    value = value / 100
                self.__button_volume.set_value(value)

        if display_label:
            self.__motion_time = time()
            self.__label_volume.show()

    def __set_cursor_empty(self):
        window = self.get_window()
        if window is not None:  # it can become none when quitting.
            window.set_cursor(self.__empty_cursor)

    def __set_cursor_default(self):
        window = self.get_window()
        if window is not None:  # it can become none when quitting.
            window.set_cursor(self.__default_cursor)

    def __set_fullscreen(self, fullscreen):

        if self.__un_maximized_fixed_toolbar:
            parent = self.__buttons_box.get_parent()
            if parent is not None:
                parent.remove(self.__buttons_box)

        if fullscreen:
            self.__window_root.fullscreen()
            self.__menubutton_fullscreen.set_image(
                Gtk.Image.new_from_icon_name(ThemeButtons._un_fullscreen, Gtk.IconSize.BUTTON))
            self.__menubutton_fullscreen.set_tooltip_text(Texts.MediaPlayer.Tooltip._unfullscreen)
            if self.__un_maximized_fixed_toolbar:
                self.__overlay.add_overlay(self.__buttons_box)
        else:
            self.__window_root.unfullscreen()
            self.__menubutton_fullscreen.set_image(
                Gtk.Image.new_from_icon_name(ThemeButtons._fullscreen, Gtk.IconSize.BUTTON))
            self.__menubutton_fullscreen.set_tooltip_text(Texts.MediaPlayer.Tooltip._fullscreen)
            if self.__un_maximized_fixed_toolbar:
                self.pack_start(self.__buttons_box, expand=False, fill=True, padding=0)

        self.__menubutton_fullscreen.set_active(False)

    def __set_scale_progress_end(self):
        """
            To be called ONLY from GLib.

            It is necessary to apply a delay, so the Glib methods
            of self.__on_thread_player_activity do not override the end value.

            self.__stop_player_scan() may end the thread, but Glib methods already sent
            will not be killed.
        """
        sleep(.2)
        self.__scale_progress.set_value(self.__scale_progress.get_adjustment().get_upper())

    def __on_thread_set_video(self, play, from_scale):
        """
           Parse video is an async function, so this must be called in a
           thread to avoid blocking the GUI.
        """

        if self.__media is None or self.__delayed_media_data is None:
            return

        GLib.idle_add(self.__vlc_widget._player.set_media, self.__media)
        GLib.idle_add(self.__vlc_widget._player.audio_set_volume, self.__volume)

        if play:
            GLib.idle_add(self.__vlc_widget._player.play)
            self.__video_is_loaded = True

        while self.__media.get_parsed_status() == 0:
            sleep(.1)

        GLib.idle_add(self.__window_root.set_title, self.__media.get_meta(0))

        video_length = self.__media.get_duration()
        if video_length < 0:
            return

        GLib.idle_add(self.__label_video_length.set_text, " / " + format_milliseconds_to_time(video_length))
        GLib.idle_add(self.__scale_progress.set_range, 0, video_length)

        #
        # Set the audio track
        #
        if self.__delayed_media_data._audio_track != Track.Value._undefined:
            GLib.idle_add(self.__vlc_widget._player.audio_set_track,
                          self.__delayed_media_data._audio_track)

        #
        # Set the subtitles' track
        #
        if self.__delayed_media_data._sub_track != Track.Value._undefined:
            GLib.idle_add(self.__vlc_widget._player.video_set_spu,
                          self.__delayed_media_data._sub_track)

        #
        # Start the video at some position (if necessary)
        #
        if from_scale:
            start_time = int(self.__scale_progress.get_value())
        else:
            start_time = self.__delayed_media_data._start_at
            GLib.idle_add(self.__scale_progress.set_value, start_time)

        if start_time > video_length:
            start_time = video_length

        if 0 < start_time <= video_length:  # if start_at == 0, this is not necessary
            GLib.idle_add(self.__vlc_widget._player.set_time, start_time)

        #
        # Re-Activate the GUI
        #
        GLib.idle_add(self.__buttons_box.set_sensitive, True)

        if play and not self.__delayed_media_data._video_settings_loaded:
            GLib.idle_add(self.__populate_settings_menubutton)

    def __on_thread_motion_activity(self, *_):

        this_thread = current_thread()

        while getattr(this_thread, "do_run", True):

            time_delta = time() - self.__motion_time

            if self.__un_maximized_fixed_toolbar:
                fullscreen = gtk_utils.window_is_fullscreen(self.__window_root)
            else:
                fullscreen = None

            if (time_delta > 3 and not self.__scale_progress_pressed and
                    ((not self.__un_maximized_fixed_toolbar and self.__widgets_shown > WidgetsShown._none) or
                     (self.__widgets_shown != WidgetsShown._toolbox and fullscreen is not None) or
                     (self.__hidden_controls is False and self.__media))):

                GLib.idle_add(self.__label_volume.hide)
                GLib.idle_add(self.__set_cursor_empty)

                if fullscreen in (True, None):
                    self.__widgets_shown = WidgetsShown._none
                    GLib.idle_add(self.__buttons_box.hide)
                else:
                    self.__widgets_shown = WidgetsShown._toolbox

                self.__hidden_controls = True

            sleep(.5)

    def __on_motion_notify_event(self, *_):
        self.__motion_time = time()

        if self.__hidden_controls:
            self.__hidden_controls = False
            self.__widgets_shown = WidgetsShown._toolbox
            self.__buttons_box.show()
            self.__set_cursor_default()

    def __on_window_root_key_pressed(self, _, event):

        if event.keyval == EventCodes.Keyboard._f11 and self.__media is not None:
            self.__set_fullscreen(True)

        elif gtk_utils.window_is_fullscreen(self.__window_root):
            match event.keyval:
                # display the toolbox if the arrows are pressed?
                case EventCodes.Keyboard._arrow_left | EventCodes.Keyboard._arrow_right:
                    self.__motion_time = time()

                case EventCodes.Keyboard._esc:
                    self.__set_fullscreen(False)

                case EventCodes.Keyboard._space_bar | EventCodes.Keyboard._enter:
                    self.play_pause()

                case EventCodes.Keyboard._arrow_up:
                    self.volume_up()

                case EventCodes.Keyboard._arrow_down:
                    self.volume_down()

    def __on_player_scroll(self, _, event):

        if self.__media is None:
            return

        elif event.direction == Gdk.ScrollDirection.UP:
            self.volume_up()

        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.volume_down()

    def __on_player_press(self, _, event):

        if self.__media is None:
            return

        elif self.__scale_progress_pressed:
            return

        elif not gtk_utils.window_is_fullscreen(self.__window_root):
            return

        elif event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == EventCodes.Cursor._left_click:
                if self.is_playing():
                    self.__vlc_widget._player.pause()
                    turn_off_screensaver(False)
                else:
                    self.__vlc_widget._player.play()
                    turn_off_screensaver(True)

    def __on_player_end_reached(self, _event):
        GLib.idle_add(self.__end_video, False)

    def __on_player_time_changed(self, event):

        if self.__scale_progress_pressed:
            # The final time will be sent when the press button be released
            return

        elif self.__media is None:
            return

        # Only update if the number of seconds has changed
        new_time = int(event.u.new_time)
        if new_time <= 0:
            seconds = 0
        else:
            seconds = int(new_time / 1000)

        if seconds == self.__emitted_time:
            return
        self.__emitted_time = seconds

        GLib.idle_add(self.__scale_progress.set_value, new_time)
        self.emit(CustomSignals._time_changed, seconds)

    def __on_menubutton_restart_clicked(self, *_):

        if not self.__menubutton_restart.get_active():
            return

        self.__vlc_widget._player.set_time(0)
        self.__scale_progress.set_value(0)  # Necessary if the video is paused.
        self.emit(CustomSignals._video_restart)
        self.__menubutton_restart.set_active(False)

    def __on_menubutton_play_clicked(self, *_):

        if not self.__menubutton_play.get_active():
            return

        self.play_pause()

        self.__menubutton_play.set_active(False)

    def __on_menubutton_end_clicked(self, *_):

        if not self.__menubutton_next.get_active():
            return

        self.__end_video(forced=True)

    def __on_menubutton_keep_playing_toggled(self, widget):
        self.emit(CustomSignals._btn_keep_playing_toggled, widget.get_active())

    def __on_menubutton_random_toggled(self, widget):
        self.emit(CustomSignals._btn_random_toggled, widget.get_active())

    def __on_menubutton_fullscreen_clicked(self, button):

        if not button.get_active():
            return

        self.__set_fullscreen(not gtk_utils.window_is_fullscreen(self.__window_root))

        button.set_active(False)

    def __on_button_volume_changed(self, _, value):
        self.__set_volume(int(value * 100), display_label=False, update_button=False)

    def __on_menuitem_track_activate(self, menuitem, track_type, track):

        # To filter duplicated signals, only listen to the active one.
        if not menuitem.get_active():
            return

        if track_type == Track.Type._audio:
            self.__vlc_widget._player.audio_set_track(track)
            self.__delayed_media_data.set_audio_track(track)

        elif track_type == Track.Type._subtitles:
            self.__vlc_widget._player.video_set_spu(track)
            self.__delayed_media_data.set_sub_track(track)
            self.__menuitem_subtitles_activated = menuitem

        elif track_type == Track.Type._video:
            self.__vlc_widget._player.video_set_track(track)

    def __on_menuitem_file_subs_activate(self, menuitem, *_):

        # Filter to only when the menuitem was activated.
        if not menuitem.get_active():
            return

        file_filter = Gtk.FileFilter()
        file_filter.set_name('*.srt')
        file_filter.add_pattern('*.srt')

        path = gtk_utils.dialog_select_file(parent=self.__window_root,
                                            file_filter=file_filter)

        if path is None:
            # The action as canceled so, reselect the previous item
            if self.__menuitem_subtitles_activated != self.__menuitem_subtitles_file:
                self.__menuitem_subtitles_activated.set_active(True)
        else:
            self.__vlc_widget._player.video_set_subtitle_file(path)
            self.__menuitem_subtitles_activated = self.__menuitem_subtitles_file

    def __on_scale_progress_press(self, *_):

        if not self.__scale_progress_pressed:
            self.__was_playing_before_press = self.is_playing()
            if self.__was_playing_before_press:
                threading.Thread(target=self.__on_thread_scale_progress_long_press).start()

        self.__scale_progress_pressed = True

    def __on_thread_scale_progress_long_press(self):
        sleep(.25)
        if self.__scale_progress_pressed:
            GLib.idle_add(self.__vlc_widget._player.pause)

    def __on_scale_progress_release(self, widget, *_):

        value = int(widget.get_value())

        if value == 0:
            self.__on_menubutton_restart_clicked()

        elif value == widget.get_adjustment().get_upper():
            self.__end_video(forced=True)

        else:
            self.__vlc_widget._player.set_time(int(widget.get_value()))

            if self.__was_playing_before_press:  # In case of long press
                if self.is_paused():
                    self.__vlc_widget._player.play()

        self.__motion_time = time()
        self.__scale_progress_pressed = False

    def __on_scale_progress_value_changed(self, widget, *_):
        self.__label_video_progress.set_text(format_milliseconds_to_time(int(widget.get_value())))

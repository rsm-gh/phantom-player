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
import vlc
import sys
from time import time, sleep
from datetime import timedelta
from threading import Thread, current_thread
from gi.repository import Gtk, GObject, Gdk, GLib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from model.Playlist import Track, TimeValue
from model.Video import VideoPosition
from view import gtk_utils
from view.VLCWidget import VLCWidget, VLC_INSTANCE
from system_utils import EventCodes, turn_off_screensaver
from settings import ThemeButtons
from Texts import Texts

_EMPTY__VIDEO_LENGTH = "00:00"
_DEFAULT_PROGRESS_LABEL = "{0} / {0}".format(_EMPTY__VIDEO_LENGTH)
_DEFAULT_CSS = """
scale, label, box {
    background-color: @theme_bg_color;
}
"""


def calculate_end_position(video_length):
    """
        Calculate a position and the round digits
        that are necessary to track 1 second.
    """

    seconds = video_length // 1000

    if seconds <= 1:
        return .6, 1

    digits = 0
    while True:
        digits += 1
        end_pos = float("." + ("9" * digits))
        delta = 1 - end_pos
        quantity = 1 / delta
        step = seconds / quantity
        if step <= 1 or digits > 9:
            break

    return end_pos, digits


def calculate_start_position(saved_position, start_at, end_position, video_length, replay):
    """
        Calculate the position where the player should start.
    """

    #
    # Convert the start_at in seconds, to a position.
    #
    if video_length > 0 and start_at > 0:
        seconds = video_length / 1000
        start_at_position = start_at / seconds

        # Verify that the start_at_position is before end_position.
        # Videos cannot start at the end.
        if start_at_position >= end_position:
            print("Warning, start_at_position >= end_position", start_at_position, end_position)
            start_at_position = VideoPosition._start
    else:
        start_at_position = VideoPosition._start

    #
    # Check if the saved_position should be restarted
    #
    if saved_position >= end_position and replay:
        saved_position = VideoPosition._start

    #
    # Select the preferred position
    #
    if start_at_position > saved_position:
        preferred_position = start_at_position

    elif saved_position > VideoPosition._end:
        preferred_position = VideoPosition._end

    elif saved_position < VideoPosition._start:
        preferred_position = VideoPosition._start

    else:
        preferred_position = saved_position


    return preferred_position



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
        content = track[1].strip().replace('[', '').replace(']', '').replace('_', ' ').title().strip()
    except Exception as e:
        content = track[1]
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
    _position_changed = 'position-changed'
    _video_restart = 'video-restart'
    _video_end = 'video-end'
    _btn_random_toggled = 'btn-random-clicked'
    _btn_keep_playing_toggled = 'btn-keep-playing-clicked'


class DelayedMediaData:
    def __init__(self, position, start_at, sub_track, audio_track, replay, play):
        self._position = position
        self._start_at = start_at
        self._sub_track = sub_track
        self._audio_track = audio_track
        self._replay = replay
        self._play = play

class VideoChangeStatus:
    _none = 0
    _changing = 1
    _changed = 2


class MediaPlayerWidget(Gtk.VBox):
    __gtype_name__ = 'MediaPlayerWidget'

    def __init__(self,
                 root_window,
                 random_button=False,
                 keep_playing_button=False,
                 un_max_fixed_toolbar=True,
                 css_style=None):  # Automatically hide the toolbar when the window is un-maximized

        super().__init__()

        self.__delayed_media_data = None
        self.__root_window = root_window
        self.__motion_time = time()
        self.__scale_progress_pressed = False
        self.__video_duration = _EMPTY__VIDEO_LENGTH
        self.__hidden_controls = False
        self.__media = None
        self.__video_change_status = VideoChangeStatus._none  # Patch 001

        self.__un_maximized_fixed_toolbar = un_max_fixed_toolbar
        self.__widgets_shown = WidgetsShown._toolbox

        display = self.get_display()
        self.__empty_cursor = Gdk.Cursor.new_from_name(display, 'none')
        self.__default_cursor = Gdk.Cursor.new_from_name(display, 'default')

        self.__overlay = Gtk.Overlay()
        self.pack_start(self.__overlay, expand=True, fill=True, padding=0)

        self.__vlc_widget = VLCWidget()
        self.__overlay.add(self.__vlc_widget)

        if un_max_fixed_toolbar:
            # It is important to add the motion_notify to the root_window,
            # to avoid hiding-it on un-maximized mode.
            event_widget = self.__root_window
        else:
            event_widget = self.__vlc_widget
        event_widget.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        event_widget.connect('motion_notify_event', self.__on_motion_notify_event)

        self.__vlc_widget.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.__vlc_widget.connect('button-press-event', self.__on_mouse_button_press)

        self.__vlc_widget.add_events(Gdk.EventMask.SCROLL_MASK)
        self.__vlc_widget.connect('scroll_event', self.__on_mouse_scroll)

        self.__root_window.connect('key-press-event', self.__on_key_pressed)

        # Style
        if css_style is None:
            css_style = _DEFAULT_CSS

        # Buttons Box
        self.__buttons_box = Gtk.Box()
        self.__buttons_box.set_valign(Gtk.Align.END)
        self.__buttons_box.set_halign(Gtk.Align.FILL)
        self.__buttons_box.set_sensitive(False)

        self.__toolbutton_previous = Gtk.ToolButton()
        self.__toolbutton_previous.set_tooltip_text(Texts.MediaPlayer.Tooltip._start)
        self.__toolbutton_previous.set_icon_name(ThemeButtons._previous)
        self.__toolbutton_previous.connect('clicked', self.__on_toolbutton_restart_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_previous, expand=False, fill=False, padding=3)

        self.__toolbutton_play = Gtk.ToolButton()
        self.__toolbutton_play.set_icon_name(ThemeButtons._play)
        self.__toolbutton_play.set_tooltip_text(Texts.MediaPlayer.Tooltip._play)
        self.__toolbutton_play.connect('clicked', self.__on_toolbutton_play_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_play, expand=False, fill=False, padding=3)

        self.__toolbutton_next = Gtk.ToolButton()
        self.__toolbutton_next.set_icon_name(ThemeButtons._next)
        self.__toolbutton_next.set_tooltip_text(Texts.MediaPlayer.Tooltip._end)
        self.__toolbutton_next.connect('clicked', self.__on_toolbutton_end_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_next, expand=False, fill=False, padding=3)

        self.__scale_progress = Gtk.Scale()
        self.__scale_progress.set_range(VideoPosition._start, VideoPosition._end)
        self.__scale_progress.set_draw_value(False)
        self.__scale_progress.set_hexpand(True)
        self.__scale_progress.connect('button-press-event', self.__on_scale_progress_press)
        self.__scale_progress.connect('button-release-event', self.__on_scale_progress_release)
        self.__scale_progress.connect('value_changed', self.__on_scale_progress_changed)
        self.__buttons_box.pack_start(child=self.__scale_progress, expand=True, fill=True, padding=3)

        self.__label_progress = Gtk.Label()
        self.__label_progress.set_text(_DEFAULT_PROGRESS_LABEL)
        self.__label_progress.set_margin_end(5)
        self.__buttons_box.pack_start(self.__label_progress, expand=False, fill=False, padding=3)

        if keep_playing_button:
            self.__toggletoolbutton_keep_playing = Gtk.ToggleToolButton()
            self.__toggletoolbutton_keep_playing.set_tooltip_text(Texts.MediaPlayer.Tooltip._keep_playing)
            self.__toggletoolbutton_keep_playing.set_icon_name(ThemeButtons._keep_playing)
            self.__toggletoolbutton_keep_playing.connect('toggled', self.__on_togglebutton_keep_playing_toggled)
            self.__buttons_box.pack_start(self.__toggletoolbutton_keep_playing, expand=False, fill=False, padding=3)
        else:
            self.__toggletoolbutton_keep_playing = None

        if random_button:
            self.__toggletoolbutton_random = Gtk.ToggleToolButton()
            self.__toggletoolbutton_random.set_tooltip_text(Texts.MediaPlayer.Tooltip._random)
            self.__toggletoolbutton_random.set_icon_name(ThemeButtons._random)
            self.__toggletoolbutton_random.connect('toggled', self.__on_togglebutton_random_toggled)
            self.__buttons_box.pack_start(self.__toggletoolbutton_random, expand=False, fill=False, padding=3)
        else:
            self.__toggletoolbutton_random = None

        self.__menubutton_settings = Gtk.MenuButton()
        self.__menubutton_settings.set_tooltip_text(Texts.MediaPlayer.Tooltip._tracks)
        self.__menubutton_settings.set_relief(Gtk.ReliefStyle.NONE)
        self.__menubutton_settings.set_image(Gtk.Image.new_from_icon_name(ThemeButtons._settings, Gtk.IconSize.BUTTON))
        self.__menubutton_settings.set_direction(Gtk.ArrowType.UP)
        self.__buttons_box.pack_start(self.__menubutton_settings, expand=False, fill=False, padding=3)

        self.__volumebutton = Gtk.VolumeButton()
        self.__volumebutton.set_icons(ThemeButtons._volume)
        self.__volumebutton.connect('value_changed', self.__on_scale_volume_changed)
        # this is being called when the button is pressed, not the scale...
        # self.__volumebutton.connect('button-press-event', self.__on_scale_volume_press)
        # self.__volumebutton.connect('button-release-event', self.__on_scale_volume_release)
        self.__buttons_box.pack_start(self.__volumebutton, expand=False, fill=False, padding=3)

        self.__toolbutton_fullscreen = Gtk.ToolButton()
        self.__toolbutton_fullscreen.set_tooltip_text(Texts.MediaPlayer.Tooltip._fullscreen)
        self.__toolbutton_fullscreen.set_icon_name(ThemeButtons._fullscreen)
        self.__toolbutton_fullscreen.connect('clicked', self.__on_toolbutton_fullscreen_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_fullscreen, expand=False, fill=False, padding=3)

        gtk_utils.set_css(self.__buttons_box, css_style)

        #   Extra volume label
        self.__label_volume = Gtk.Label()
        self.__label_volume.set_text(" Vol: 0% ")
        self.__label_volume.set_valign(Gtk.Align.START)
        self.__label_volume.set_halign(Gtk.Align.END)
        self.__label_volume.set_margin_start(5)
        self.__label_volume.set_margin_end(5)
        gtk_utils.set_css(self.__label_volume, css_style)
        self.__overlay.add_overlay(self.__label_volume)

        #
        # Add the toolbar
        #
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
                           ())
        GObject.signal_new(CustomSignals._video_restart,
                           self, GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           ())
        GObject.signal_new(CustomSignals._position_changed,
                           self,
                           GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE,
                           (float,))
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
        self.__thread_player_activity = Thread(target=self.__on_thread_player_activity)
        self.__thread_player_activity.start()

        self.__thread_scan_motion = Thread(target=self.__on_thread_motion_activity)
        self.__thread_scan_motion.start()

    def play(self):
        self.__toolbutton_play.set_icon_name(ThemeButtons._pause)
        self.__toolbutton_play.set_tooltip_text(Texts.MediaPlayer.Tooltip._pause)
        self.__vlc_widget.player.play()
        turn_off_screensaver(True)
        self.emit(CustomSignals._play)

    def pause(self):
        self.__toolbutton_play.set_icon_name(ThemeButtons._play)
        self.__toolbutton_play.set_tooltip_text(Texts.MediaPlayer.Tooltip._play)
        self.__vlc_widget.player.pause()
        turn_off_screensaver(False)
        self.emit(CustomSignals._paused)

    def stop(self):
        self.__video_change_status = VideoChangeStatus._none
        self.__vlc_widget.player.stop()
        self.__buttons_box.set_sensitive(False)
        self.__label_progress.set_text(_DEFAULT_PROGRESS_LABEL)
        self.__label_volume.hide()
        self.__scale_progress.set_value(VideoPosition._start)
        self.__media = None
        self.emit(CustomSignals._stop)

    def is_playing(self):
        return self.get_state() == vlc.State.Playing

    def is_paused(self):
        return self.get_state() == vlc.State.Paused

    def is_nothing(self):
        return self.get_state() == vlc.State.NothingSpecial

    def volume_up(self):
        actual_volume = self.__vlc_widget.player.audio_get_volume()
        if actual_volume + 1 <= 100:
            self.__vlc_widget.player.audio_set_volume(actual_volume + 1)

    def volume_down(self):
        actual_volume = self.__vlc_widget.player.audio_get_volume()
        if actual_volume >= 1:
            self.__vlc_widget.player.audio_set_volume(actual_volume - 1)

    def hide_controls(self):
        self.__buttons_box.hide()
        self.__buttons_box.hide()
        self.__label_volume.hide()
        self.__widgets_shown = WidgetsShown._none

    def hide_volume_label(self):
        self.__label_volume.hide()

    def join(self):
        self.__thread_player_activity.join()
        self.__thread_scan_motion.join()

    def quit(self):
        self.__vlc_widget.player.stop()
        self.__thread_scan_motion.do_run = False
        self.__thread_player_activity.do_run = False

        turn_off_screensaver(False)

    def set_video(self,
                  file_path,
                  position=VideoPosition._start,
                  start_at=TimeValue._minium,
                  subtitles_track=Track.Value._undefined,
                  audio_track=Track.Value._undefined,
                  play=True,
                  replay=False):

        self.__video_change_status = VideoChangeStatus._changing
        self.__media = None
        self.__video_duration = 0

        GLib.idle_add(self.__buttons_box.set_sensitive, False),
        GLib.idle_add(self.__menubutton_settings.set_sensitive, False)
        GLib.idle_add(self.__label_progress.set_text, _DEFAULT_PROGRESS_LABEL)
        GLib.idle_add(self.__scale_progress.set_value, VideoPosition._start)

        GLib.idle_add(self.__vlc_widget.player.stop) # To remove any previous video

        if not os.path.exists(file_path):
            return

        media = VLC_INSTANCE.media_new(file_path)
        media.parse()
        self.__media = media # assigned only after `parse()` has finished.

        GLib.idle_add(self.__root_window.set_title, self.__media.get_meta(0))

        if play:
            turn_off_screensaver(True)

        GLib.idle_add(self.__vlc_widget.player.set_media, self.__media)
        GLib.idle_add(self.play)

        # Patch 001: Some actions will be performed when the video length be properly parsed
        self.__delayed_media_data = DelayedMediaData(position=position,
                                                     start_at=start_at,
                                                     sub_track=subtitles_track,
                                                     audio_track=audio_track,
                                                     replay=replay,
                                                     play=play)


    def set_random(self, state):
        self.__toggletoolbutton_random.set_active(state)

    def set_keep_playing(self, state):
        self.__toggletoolbutton_keep_playing.set_active(state)

    def get_position(self):
        return self.__vlc_widget.player.get_position()

    def get_state(self):
        return self.__vlc_widget.player.get_state()

    def get_random(self):
        if self.__toggletoolbutton_random is None:
            return False

        return self.__toggletoolbutton_random.get_active()

    def get_keep_playing(self):
        if self.__toggletoolbutton_keep_playing is None:
            return False

        return self.__toggletoolbutton_keep_playing.get_active()

    def get_media(self):
        # self.__vlc_widget.player.get_media()
        return self.__media

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

        selected_track = self.__vlc_widget.player.audio_get_track()

        try:
            tracks = [(audio[0], audio[1].decode('utf-8')) for audio in
                      self.__vlc_widget.player.audio_get_track_description()]
        except Exception as e:
            tracks = self.__vlc_widget.player.audio_get_track_description()
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

        selected_track = self.__vlc_widget.player.video_get_spu()

        default_item = Gtk.RadioMenuItem(label="-1:  Disable")
        if selected_track == -1:
            default_item.set_active(True)
        default_item.connect('activate', self.__on_menuitem_track_activate, Track.Type._subtitles, -1)
        submenu.append(default_item)

        try:
            tracks = [(video_spu[0], video_spu[1].decode('utf-8')) for video_spu in
                      self.__vlc_widget.player.video_get_spu_description()]
        except Exception as e:
            tracks = self.__vlc_widget.player.video_get_spu_description()
            print(str(e))

        for track in tracks:
            if 'Disable' in track:
                continue

            item = Gtk.RadioMenuItem(label=format_track(track))
            item.join_group(default_item)
            if selected_track == track[0]:
                item.set_active(True)
            item.connect('activate', self.__on_menuitem_track_activate, Track.Type._subtitles, track[0])
            submenu.append(item)

        item = Gtk.RadioMenuItem(label="From file...")
        item.join_group(default_item)
        item.connect('activate', self.__on_menuitem_file_subs_activate)
        submenu.append(item)

        menu.show_all()

    def __get_window_is_fullscreen(self):

        window = self.__root_window.get_window()

        if window is None:
            return False

        elif Gdk.WindowState.FULLSCREEN & window.get_state():
            return True

        return False

    def __set_cursor_empty(self):
        self.get_window().set_cursor(self.__empty_cursor)

    def __set_cursor_default(self):
        self.get_window().set_cursor(self.__default_cursor)

    def __set_fullscreen(self, fullscreen):

        if self.__un_maximized_fixed_toolbar:
            parent = self.__buttons_box.get_parent()
            if parent is not None:
                parent.remove(self.__buttons_box)

        if fullscreen:
            self.__root_window.fullscreen()
            self.__toolbutton_fullscreen.set_icon_name(ThemeButtons._un_fullscreen)
            self.__toolbutton_fullscreen.set_tooltip_text(Texts.MediaPlayer.Tooltip._unfullscreen)
            if self.__un_maximized_fixed_toolbar:
                self.__overlay.add_overlay(self.__buttons_box)
        else:
            self.__root_window.unfullscreen()
            self.__toolbutton_fullscreen.set_icon_name(ThemeButtons._fullscreen)
            self.__toolbutton_fullscreen.set_tooltip_text(Texts.MediaPlayer.Tooltip._fullscreen)
            if self.__un_maximized_fixed_toolbar:
                self.pack_start(self.__buttons_box, expand=False, fill=True, padding=0)

    def __on_thread_player_activity(self):
        """
            This method scans the state of the player to:
                + Emit a signal if the video position changes
                + Emit a signal when the video ends
                + Update the tool buttons (volume, play-stop, etc...)
        """

        this_thread = current_thread()

        cached_emitted_position = 0
        cached_vlc_position = 0
        end_position = -1
        position_precision = -1

        while getattr(this_thread, "do_run", True):

            sleep(.25)

            if self.__video_change_status == VideoChangeStatus._changing:

                if self.__media is None or self.__delayed_media_data is None:
                    continue

                #
                # Patch 001: In case of a new video, wait until the media duration
                # can be correctly parsed to apply all the settings that depend on it.
                #
                self.__video_duration = self.__media.get_duration()
                cached_emitted_position = 0
                cached_vlc_position = 0
                end_position = -1
                position_precision = -1

                if self.__video_duration <= 0 < end_position:
                    continue

                self.__video_change_status = VideoChangeStatus._changed
                end_position, position_precision = calculate_end_position(self.__video_duration)

                #
                # Set the audio track
                #
                if self.__delayed_media_data._audio_track != Track.Value._undefined:
                    GLib.idle_add(self.__vlc_widget.player.audio_set_track,
                                  self.__delayed_media_data._audio_track)

                #
                # Set the subtitles' track
                #
                if self.__delayed_media_data._sub_track != Track.Value._undefined:
                    GLib.timeout_add_seconds(self.__vlc_widget.player.video_set_spu,
                                             self.__delayed_media_data._sub_track)


                #
                # Start the video at some position (if necessary)
                #
                start_position = calculate_start_position(saved_position=self.__delayed_media_data._position,
                                                          start_at=self.__delayed_media_data._start_at,
                                                          end_position=end_position,
                                                          video_length=self.__video_duration,
                                                          replay=self.__delayed_media_data._replay)
                if start_position > VideoPosition._start:
                    GLib.idle_add(self.__vlc_widget.player.set_position, start_position)


                #
                # Pause the video if requested
                #
                if not self.__delayed_media_data._play:
                    GLib.idle_add(self.__vlc_widget.player.pause)

                #
                # Re-Activate the GUI
                #
                GLib.idle_add(self.__buttons_box.set_sensitive, True)
                GLib.timeout_add_seconds(1, self.__populate_settings_menubutton)
                GLib.timeout_add_seconds(1, self.__menubutton_settings.set_sensitive, True)


            elif self.__video_change_status == VideoChangeStatus._changed:

                if self.__scale_progress_pressed:
                    continue

                vlc_is_playing = self.is_playing()

                #
                #    Update the play-pause button
                #
                if vlc_is_playing and self.__toolbutton_play.get_icon_name() != ThemeButtons._pause:
                    GLib.idle_add(self.__toolbutton_play.set_icon_name, ThemeButtons._pause)

                elif not vlc_is_playing and self.__toolbutton_play.get_icon_name() != ThemeButtons._play:
                    GLib.idle_add(self.__toolbutton_play.set_icon_name, ThemeButtons._play)

                #
                #    Update the volume. Is this necessary?
                #
                vlc_volume = self.__vlc_widget.player.audio_get_volume()
                scale_volume_value = int(self.__volumebutton.get_value() * 100)
                if vlc_volume <= 100 and vlc_volume != scale_volume_value:
                    GLib.idle_add(self.__volumebutton.set_value, vlc_volume / 100.000)
                    GLib.idle_add(self.__label_volume.set_text, " Vol: {}% ".format(vlc_volume))
                    GLib.idle_add(self.__label_volume.show)

                    self.__motion_time = time()
                    self.__widgets_shown = WidgetsShown._volume

                #
                #    Update the time of the scale and the time
                #
                vlc_position = self.__vlc_widget.player.get_position()
                if vlc_position > VideoPosition._end:
                    vlc_position = VideoPosition._end

                cached_emitted_position = self.__on_player_position_changed(vlc_position,
                                                                            position_precision,
                                                                            end_position,
                                                                            cached_emitted_position)

                if cached_emitted_position > vlc_position:
                    vlc_position = cached_emitted_position

                if vlc_position != cached_vlc_position:
                    cached_vlc_position = vlc_position
                    GLib.idle_add(self.__scale_progress.set_value, vlc_position)


    def __on_thread_motion_activity(self, *_):

        this_thread = current_thread()

        while getattr(this_thread, "do_run", True):

            time_delta = time() - self.__motion_time

            if self.__un_maximized_fixed_toolbar:
                fullscreen = self.__get_window_is_fullscreen()
            else:
                fullscreen = None

            if (time_delta > 3 and not self.__scale_progress_pressed and
                    ((not self.__un_maximized_fixed_toolbar and self.__widgets_shown > WidgetsShown._none) or
                     (self.__widgets_shown != WidgetsShown._toolbox and fullscreen is not None) or
                     (self.__hidden_controls is False and self.get_media()))):

                GLib.idle_add(self.__label_volume.hide)
                GLib.idle_add(self.__set_cursor_empty)

                if fullscreen in (True, None):
                    self.__widgets_shown = WidgetsShown._none
                    GLib.idle_add(self.__buttons_box.hide)
                else:
                    self.__widgets_shown = WidgetsShown._toolbox

                self.__hidden_controls = True

            sleep(.5)

    def __on_key_pressed(self, _, event):

        key = event.keyval

        if key == EventCodes.Keyboard.f11 and self.get_media() is not None:
            self.__set_fullscreen(True)

        elif self.__get_window_is_fullscreen():

            # display the toolbox if the arrows are shown
            if key in (EventCodes.Keyboard.arrow_left, EventCodes.Keyboard.arrow_right):
                self.__motion_time = time()

            if key == EventCodes.Keyboard.esc:
                self.__set_fullscreen(False)

            elif key in (EventCodes.Keyboard.space_bar, EventCodes.Keyboard.enter):
                self.__on_toolbutton_play_clicked(None, None)

            elif key == EventCodes.Keyboard.arrow_up:
                self.volume_up()

            elif key == EventCodes.Keyboard.arrow_down:
                self.volume_down()

    def __on_player_position_changed(self, vlc_position, position_precision, end_position, cached_position):

        if vlc_position < VideoPosition._start:
            return cached_position

        elif vlc_position > VideoPosition._end:
            vlc_position = VideoPosition._end

        else:
            vlc_position = round(vlc_position, position_precision)

        if vlc_position == cached_position or cached_position >= end_position:
            return cached_position

        if vlc_position >= end_position:
            vlc_position = VideoPosition._end
            self.emit(CustomSignals._video_end)
        else:
            self.emit(CustomSignals._position_changed, vlc_position)

        return vlc_position

    def __on_motion_notify_event(self, *_):
        self.__motion_time = time()

        if self.__hidden_controls:
            self.__hidden_controls = False
            self.__widgets_shown = WidgetsShown._toolbox
            self.__buttons_box.show()
            self.__set_cursor_default()

    def __on_mouse_scroll(self, _, event):

        if self.get_media() is None:
            return

        elif event.direction == Gdk.ScrollDirection.UP:
            self.volume_up()

        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.volume_down()

    def __on_mouse_button_press(self, _, event):

        if self.get_media() is None:
            return

        elif self.__scale_progress_pressed:
            return

        elif event.type == Gdk.EventType.BUTTON_PRESS:

            if event.button == EventCodes.Cursor.left_click:

                if self.is_playing():
                    self.__vlc_widget.player.pause()
                    turn_off_screensaver(False)
                else:
                    self.__vlc_widget.player.play()
                    turn_off_screensaver(True)

    def __on_toolbutton_restart_clicked(self, *_):
        self.__vlc_widget.player.set_position(VideoPosition._start)
        self.emit(CustomSignals._video_restart)

    def __on_toolbutton_play_clicked(self, *_):
        if self.is_playing():
            self.pause()
        else:
            self.play()

    def __on_toolbutton_end_clicked(self, *_):
        self.__vlc_widget.player.set_position(VideoPosition._end - 0.001)  # position = 1 will not work
        # self.emit(CustomSignals._video_end) the thread will emit This signal

    def __on_togglebutton_keep_playing_toggled(self, widget):
        self.emit(CustomSignals._btn_keep_playing_toggled, widget.get_active())

    def __on_togglebutton_random_toggled(self, widget):
        self.emit(CustomSignals._btn_random_toggled, widget.get_active())

    def __on_toolbutton_fullscreen_clicked(self, *_):
        self.__set_fullscreen(not self.__get_window_is_fullscreen())

    def __on_menuitem_track_activate(self, _, track_type, track):

        if track_type == Track.Type._audio:
            self.__vlc_widget.player.audio_set_track(track)

        elif track_type == Track.Type._subtitles:
            self.__vlc_widget.player.video_set_track(track)

        elif track_type == Track.Type._spu:
            self.__vlc_widget.player.video_set_spu(track)

    def __on_menuitem_file_subs_activate(self, *_):

        path = gtk_utils.dialog_select_file(self.__root_window)

        if path is not None:
            self.__vlc_widget.player.video_set_subtitle_file(path)
            return True

        return False

    def __on_scale_volume_changed(self, _, value):
        value = int(value * 100)
        if self.__vlc_widget.player.audio_get_volume() != value:
            self.__motion_time = time()
            self.__label_volume.set_text(" Vol: {}% ".format(value))
            self.__label_volume.show()
            self.__vlc_widget.player.audio_set_volume(value)

    def __on_scale_volume_press(self, *_):
        pass
        # self.__scale_progress_pressed = True

    def __on_scale_volume_release(self, *_):
        self.__scale_progress_pressed = False

    def __on_scale_progress_press(self, *_):
        self.__scale_progress_pressed = True
        GLib.timeout_add_seconds(.5, self.__on_scale_progress_long_press)

    def __on_scale_progress_long_press(self):
        if self.__scale_progress_pressed:
            self.__vlc_widget.player.pause()  # In case of long press

    def __on_scale_progress_release(self, widget, *_):
        self.__vlc_widget.player.set_position(widget.get_value())
        if self.is_paused():
            self.__vlc_widget.player.play()  # In case of long press
        self.__motion_time = time()
        self.__scale_progress_pressed = False

    def __on_scale_progress_changed(self, widget, *_):
        if self.__media is not None:
            video_time = widget.get_value() * self.__media.get_duration()
            video_time = format_milliseconds_to_time(video_time)
            self.__label_progress.set_text(video_time + " / " + format_milliseconds_to_time(self.__video_duration))

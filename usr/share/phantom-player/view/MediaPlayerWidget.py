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

"""

    + Add the option to choose the subtitles' file...

    + Sometimes when clicking very fast the progress scale, the video position is not modified.
        Despite multiple ways of trying to fix this, I haven't found a solution.

    + It is necessary to connect the Scale of the Volume button, to avoid hiding the GUI when pressed.
        I haven't found a solution for this, because the press signals connect to the button and not the scale.

    + Fixes to the menu of the subtitles & audio tracks?

    + Fix to the VolumeButton: it should get hidden when clicking out of the button.

    + Start/Stop __on_thread_scan when paused, stopped? ?

    + It seems that: self.__vlc_widget.player.get_media() is always returning None. Why?
        To fix it, I created self.__media

    + self.__vlc_widget.player.XXX_set_track returns a status.
       It would be good to read the status and display a message in case of problem.

"""

import os
import vlc
import sys
from time import time, sleep
from datetime import timedelta
from threading import Thread, current_thread
from gi.repository import Gtk, GObject, Gdk, GLib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from model.Playlist import Track
from model.Video import VideoPosition
from view.gtk_utils import set_css
from view.VLCWidget import VLCWidget, VLC_INSTANCE
from system_utils import EventCodes, turn_off_screensaver

_EMPTY__VIDEO_LENGTH = "00:00"
_DEFAULT_PROGRESS_LABEL = "{0} / {0}".format(_EMPTY__VIDEO_LENGTH)


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
    none = 0
    volume = 1
    toolbox = 2

class ThemeButtons:
    """
        This class is not into settings.py because I want MediaPlayer.py
        to be a standalone (beside VLCWidget.py).
    """
    play = "media-playback-start"
    pause = "media-playback-pause"
    next = "go-next"
    previous = "go-previous"
    volume = ["audio-volume-muted", "audio-volume-high", "audio-volume-medium"]
    fullscreen = "view-fullscreen"
    un_fullscreen = "view-restore"
    random = "media-playlist-shuffle"
    keep_playing = "media-playlist-repeat"
    settings = "preferences-desktop"


class CustomSignals:
    paused = 'paused'
    play = 'play'
    stop = 'stop'
    position_changed = 'position-changed'
    video_restart = 'video-restart'
    video_end = 'video-end'
    btn_random_toggled = 'btn-random-clicked'
    btn_keep_playing_toggled = 'btn-keep-playing-clicked'


class MediaPlayerWidget(Gtk.VBox):
    __gtype_name__ = 'MediaPlayerWidget'

    def __init__(self,
                 root_window,
                 random_button=False,
                 keep_playing_button=False,
                 un_max_fixed_toolbar=True,
                 css_style=None):  # Automatically hide the toolbar when the window is un-maximized

        super().__init__()

        self.__root_window = root_window
        self.__motion_time = time()
        self.__scale_progress_pressed = False
        self.__video_length = _EMPTY__VIDEO_LENGTH
        self.__hidden_controls = False
        self.__media = None

        self.__un_maximized_fixed_toolbar = un_max_fixed_toolbar
        self.__widgets_shown = WidgetsShown.toolbox

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
            css_style = """
scale, label, box {
    background-color: @theme_bg_color;
}
"""
        # Buttons Box
        self.__buttons_box = Gtk.Box()
        self.__buttons_box.set_valign(Gtk.Align.END)
        self.__buttons_box.set_halign(Gtk.Align.FILL)
        self.__buttons_box.set_sensitive(False)

        self.__toolbutton_previous = Gtk.ToolButton()
        self.__toolbutton_previous.set_icon_name(ThemeButtons.previous)
        self.__toolbutton_previous.connect('clicked', self.__on_toolbutton_restart_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_previous, expand=False, fill=False, padding=3)

        self.__toolbutton_play = Gtk.ToolButton()
        self.__toolbutton_play.set_icon_name(ThemeButtons.play)
        self.__toolbutton_play.connect('clicked', self.__on_toolbutton_play_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_play, expand=False, fill=False, padding=3)

        self.__toolbutton_next = Gtk.ToolButton()
        self.__toolbutton_next.set_icon_name(ThemeButtons.next)
        self.__toolbutton_next.connect('clicked', self.__on_toolbutton_end_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_next, expand=False, fill=False, padding=3)

        self.__scale_progress = Gtk.Scale()
        self.__scale_progress.set_range(0, 1)
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
            self.__toggletoolbutton_keep_playing.set_icon_name(ThemeButtons.keep_playing)
            self.__toggletoolbutton_keep_playing.connect('toggled', self.__on_togglebutton_keep_playing_toggled)
            self.__buttons_box.pack_start(self.__toggletoolbutton_keep_playing, expand=False, fill=False, padding=3)
        else:
            self.__toggletoolbutton_keep_playing = None

        if random_button:
            self.__toggletoolbutton_random = Gtk.ToggleToolButton()
            self.__toggletoolbutton_random.set_icon_name(ThemeButtons.random)
            self.__toggletoolbutton_random.connect('toggled', self.__on_togglebutton_random_toggled)
            self.__buttons_box.pack_start(self.__toggletoolbutton_random, expand=False, fill=False, padding=3)
        else:
            self.__toggletoolbutton_random = None

        self.__menubutton_settings = Gtk.MenuButton()
        self.__menubutton_settings.set_relief(Gtk.ReliefStyle.NONE)
        self.__menubutton_settings.set_image(Gtk.Image.new_from_icon_name(ThemeButtons.settings, Gtk.IconSize.BUTTON))
        self.__menubutton_settings.set_direction(Gtk.ArrowType.UP)
        self.__buttons_box.pack_start(self.__menubutton_settings, expand=False, fill=False, padding=3)

        self.__volumebutton = Gtk.VolumeButton()
        self.__volumebutton.set_icons(ThemeButtons.volume)
        self.__volumebutton.connect('value_changed', self.__on_scale_volume_changed)
        # this is being called when the button is pressed, not the scale...
        # self.__volumebutton.connect('button-press-event', self.__on_scale_volume_press)
        # self.__volumebutton.connect('button-release-event', self.__on_scale_volume_release)
        self.__buttons_box.pack_start(self.__volumebutton, expand=False, fill=False, padding=3)

        self.__toolbutton_fullscreen = Gtk.ToolButton()
        self.__toolbutton_fullscreen.set_icon_name(ThemeButtons.fullscreen)
        self.__toolbutton_fullscreen.connect('clicked', self.__on_toolbutton_fullscreen_clicked)
        self.__buttons_box.pack_start(self.__toolbutton_fullscreen, expand=False, fill=False, padding=3)

        set_css(self.__buttons_box, css_style)

        #   Extra volume label
        self.__label_volume = Gtk.Label()
        self.__label_volume.set_text(" Vol: 0% ")
        self.__label_volume.set_valign(Gtk.Align.START)
        self.__label_volume.set_halign(Gtk.Align.END)
        self.__label_volume.set_margin_start(5)
        self.__label_volume.set_margin_end(5)
        set_css(self.__label_volume, css_style)
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
        GObject.signal_new(CustomSignals.paused, self, GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, ())
        GObject.signal_new(CustomSignals.play, self, GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, ())
        GObject.signal_new(CustomSignals.stop, self, GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, ())
        GObject.signal_new(CustomSignals.video_end, self, GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, ())
        GObject.signal_new(CustomSignals.video_restart, self, GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE, ())
        GObject.signal_new(CustomSignals.position_changed, self, GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE,
                           (float,))
        GObject.signal_new(CustomSignals.btn_random_toggled, self, GObject.SignalFlags.RUN_LAST, GObject.TYPE_NONE,
                           (bool,))
        GObject.signal_new(CustomSignals.btn_keep_playing_toggled, self, GObject.SignalFlags.RUN_LAST,
                           GObject.TYPE_NONE, (bool,))

        #
        #    Init the threads
        #
        self.__thread_player_activity = Thread(target=self.__on_thread_scan)
        self.__thread_player_activity.start()

        self.__thread_scan_motion = Thread(target=self.__on_thread_motion_activity)
        self.__thread_scan_motion.start()

    def play(self):
        self.__toolbutton_play.set_icon_name(ThemeButtons.pause)
        self.__vlc_widget.player.play()
        turn_off_screensaver(True)
        self.emit(CustomSignals.play)

    def pause(self):
        self.__toolbutton_play.set_icon_name(ThemeButtons.play)
        self.__vlc_widget.player.pause()
        turn_off_screensaver(False)
        self.emit(CustomSignals.paused)

    def stop(self):
        self.__vlc_widget.player.stop()
        self.__buttons_box.set_sensitive(False)
        self.__label_progress.set_text(_DEFAULT_PROGRESS_LABEL)
        self.__label_volume.hide()
        self.__scale_progress.set_value(VideoPosition.start)
        self.__media = None
        self.emit(CustomSignals.stop)

    def is_playing(self):
        if self.get_state() == vlc.State.Playing:
            return True

        return False

    def is_paused(self):
        if self.get_state() == vlc.State.Paused:
            return True

        return False

    def is_nothing(self):
        if self.get_state() == vlc.State.NothingSpecial:
            return True

        return False

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
        self.__widgets_shown = WidgetsShown.none

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
                  position=0.0,
                  subtitles_track=0,
                  audio_track=0,
                  start_at=0.0,
                  play=True):

        if play is False:
            return  # todo: fix this

        if not os.path.exists(file_path):
            return

        GLib.idle_add(self.__buttons_box.set_sensitive, True)

        media = VLC_INSTANCE.media_new(file_path)
        media.parse()
        media_title = media.get_meta(0)
        self.__video_length = format_milliseconds_to_time(media.get_duration())
        self.__media = media

        turn_off_screensaver(True)

        GLib.idle_add(self.__label_progress.set_text, _DEFAULT_PROGRESS_LABEL)
        GLib.idle_add(self.__vlc_widget.player.set_media, media)
        GLib.idle_add(self.__root_window.set_title, media_title)
        GLib.idle_add(self.play)

        GLib.timeout_add_seconds(.5, self.__populate_settings_menubutton)
        if audio_track != 0:
            GLib.timeout_add_seconds(.5, self.__vlc_widget.player.audio_set_track, audio_track)

        if subtitles_track != 0:
            GLib.timeout_add_seconds(.5, self.__vlc_widget.player.video_set_spu, subtitles_track)

        #
        # Calculate the player position
        #
        if start_at <= 0:
            start_at_percent = 0
        else:
            # convert the start time to percent
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

        # Set the start position if necessary
        if start_at_percent > position:
            start_position = start_at_percent

        elif position > 0:
            start_position = position
        else:
            start_position = 0

        GLib.idle_add(self.__vlc_widget.player.set_position, start_position)

    def set_subtitles_from_file(self, *_):
        """
            Todo: read the result of player.video_set_subtitle_file(path) and display a message
            in case of problem.
        """
        path = dialog_select_file(self.__root_window)

        if path is not None:
            self.__vlc_widget.player.video_set_subtitle_file(path)

        return True

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
        default_item.connect('activate', self.__on_menu_video_subs_audio, Track.Type.audio, -1)
        submenu.append(default_item)

        for track in tracks:
            if 'Disable' in track:
                continue

            item = Gtk.RadioMenuItem(label=format_track(track))
            item.connect('activate', self.__on_menu_video_subs_audio, Track.Type.audio, track[0])
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
        default_item.connect('activate', self.__on_menu_video_subs_audio, Track.Type.subtitles, -1)
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
            item.connect('activate', self.__on_menu_video_subs_audio, Track.Type.subtitles, track[0])
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
            self.__toolbutton_fullscreen.set_icon_name(ThemeButtons.un_fullscreen)
            if self.__un_maximized_fixed_toolbar:
                self.__overlay.add_overlay(self.__buttons_box)
        else:
            self.__root_window.unfullscreen()
            self.__toolbutton_fullscreen.set_icon_name(ThemeButtons.fullscreen)
            if self.__un_maximized_fixed_toolbar:
                self.pack_start(self.__buttons_box, expand=False, fill=True, padding=0)

    def __on_thread_scan(self):
        """
            This method scans the state of the player to update the tool buttons, volume, play-stop etc
        """

        this_thread = current_thread()

        cached_position = 0

        while getattr(this_thread, "do_run", True):

            vlc_is_playing = self.is_playing()

            if not self.__scale_progress_pressed:

                """
                    Update the play-pause button
                """
                if vlc_is_playing and self.__toolbutton_play.get_icon_name() != ThemeButtons.pause:
                    GLib.idle_add(self.__toolbutton_play.set_icon_name, ThemeButtons.pause)

                elif not vlc_is_playing and self.__toolbutton_play.get_icon_name() != ThemeButtons.play:
                    GLib.idle_add(self.__toolbutton_play.set_icon_name, ThemeButtons.play)

                """
                    Update the volume. Is this necessary?
                """
                vlc_volume = self.__vlc_widget.player.audio_get_volume()
                scale_volume_value = int(self.__volumebutton.get_value() * 100)
                if vlc_volume <= 100 and vlc_volume != scale_volume_value:
                    GLib.idle_add(self.__volumebutton.set_value, vlc_volume / 100.000)
                    GLib.idle_add(self.__label_volume.set_text, " Vol: {}% ".format(vlc_volume))
                    GLib.idle_add(self.__label_volume.show)

                    self.__motion_time = time()
                    self.__widgets_shown = WidgetsShown.volume

                """
                    Update the time of the scale and the time
                """
                if not self.__scale_progress_pressed:
                    # 'not self.__scale_progress_pressed' in case that
                    # the scale be pressed when the method is being executed.
                    vlc_position = self.__vlc_widget.player.get_position()

                    round_position = round(vlc_position, 4)
                    if round_position > 1.0:
                        round_position = 1.0

                    if round_position != cached_position and round_position >= 0:
                        cached_position = round_position
                        GLib.idle_add(self.__scale_progress.set_value, cached_position)
                        self.emit(CustomSignals.position_changed, cached_position)

                        if round_position >= 1.0:
                            self.emit(CustomSignals.video_end)

            """
                Wait
            """
            sleep(.25)

    def __on_thread_motion_activity(self, *_):

        this_thread = current_thread()

        while getattr(this_thread, "do_run", True):

            time_delta = time() - self.__motion_time

            if self.__un_maximized_fixed_toolbar:
                fullscreen = self.__get_window_is_fullscreen()
            else:
                fullscreen = None

            if (time_delta > 3 and not self.__scale_progress_pressed and
                    ((not self.__un_maximized_fixed_toolbar and self.__widgets_shown > WidgetsShown.none) or
                     (self.__widgets_shown != WidgetsShown.toolbox and fullscreen is not None) or
                     (self.__hidden_controls is False and self.get_media()))):

                GLib.idle_add(self.__label_volume.hide)
                GLib.idle_add(self.__set_cursor_empty)

                if fullscreen in (True, None):
                    self.__widgets_shown = WidgetsShown.none
                    GLib.idle_add(self.__buttons_box.hide)
                else:
                    self.__widgets_shown = WidgetsShown.toolbox

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

    def __on_motion_notify_event(self, *_):
        self.__motion_time = time()

        if self.__hidden_controls:
            self.__hidden_controls = False
            self.__widgets_shown = WidgetsShown.toolbox
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
        self.__vlc_widget.player.set_position(VideoPosition.start)
        self.emit(CustomSignals.video_restart)

    def __on_toolbutton_play_clicked(self, *_):
        if self.is_playing():
            self.pause()
        else:
            self.play()

    def __on_toolbutton_end_clicked(self, *_):
        self.__vlc_widget.player.set_position(VideoPosition.end_almost)  # position = 1 will not work
        # self.emit(CustomSignals.video_end) the thread will emit This signal

    def __on_togglebutton_keep_playing_toggled(self, widget):
        self.emit(CustomSignals.btn_keep_playing_toggled, widget.get_active())

    def __on_togglebutton_random_toggled(self, widget):
        self.emit(CustomSignals.btn_random_toggled, widget.get_active())

    def __on_toolbutton_fullscreen_clicked(self, *_):
        self.__set_fullscreen(not self.__get_window_is_fullscreen())

    def __on_menu_video_subs_audio(self, _, track_type, track):
        if track_type == Track.Type.audio:
            self.__vlc_widget.player.audio_set_track(track)

        elif track_type == Track.Type.subtitles:
            self.__vlc_widget.player.video_set_track(track)

        elif track_type == Track.Type.spu:
            self.__vlc_widget.player.video_set_spu(track)

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
            self.__label_progress.set_text(video_time + " / " + self.__video_length)

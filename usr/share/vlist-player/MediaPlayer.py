#!/usr/bin/python3
#

#  Copyright (C) 2014-2016 Rafael Senties Martinelli.
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
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA.
#

""" Special thanks to the VideoLAN Team ! """


"""
    To do:
    
        -  I'm currently working on how to display the mouse when it moves
            over the VLCWidget.
            
        
        -  An option to set the audio output device

"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GdkX11', '3.0')


from gi.repository import Gtk, GObject, GLib, Gdk, GdkX11
import sys
import threading
import time
import os
from datetime import timedelta

# local imports
import vlc
VLCStatePlaying=vlc.State.Playing
VLCStatePaused=vlc.State.Paused

GLOBAL_FILE_PATH=''

def turn_off_screensaver(state):
    """ True = Turn off screen saver """

    if state:
        try:
            os.system('''xset s off''')
        except:
            print("MediaPlayer error: It wasn't possible to turn off the screensaver")
    else:
        try:
            os.system('''xset s on''')
        except:
            print("MediaPlayer error: It wasn't possible to turn on the screensaver")
    

def get_active_window_title():
    output= os.popen('''xprop -id $(xprop -root _NET_ACTIVE_WINDOW | cut -d ' ' -f 5) WM_NAME''')
    output=str(output.read())
    
    try:
        return output.split('''= "''')[1][:-2]
    except:
        print("MediaPlayer error: It wasn't possible to get the window name")
        return None

def format_track(track):
    """ Format the tracks provided by pyVLC. Track must be a tupple (int, string)"""
    
    number=str(track[0])
    
    try:
        content=track[1].strip().replace('[','').replace(']','').replace('_',' ').title()
    except Exception as e:
        content=track[1]
        print(str(e))
    
    if len(number) == 0:
        numb='  '
    elif len(number)  == 1:
        numb=' {}'.format(number)
    else:
        numb=str(number)
        
    return ' {}   {}'.format(numb, content)

def format_miliseconds_to_time(number):
    
    time_string=str(timedelta(milliseconds=number)).split('.')[0]
    
    # remove the hours if they are not necessary
    try:
        if int(time_string.split(':',1)[0]) == 0:  
            time_string=time_string.split(':',1)[1]
    except:
        pass
    
    return time_string
    
    
def gtk_file_chooser(parent, path=''):

    window_choose_file=Gtk.FileChooserDialog(   'Video List Player',
                                                parent,
                                                Gtk.FileChooserAction.OPEN,
                                                (Gtk.STOCK_CANCEL, 
                                                    Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN, 
                                                    Gtk.ResponseType.OK))
                                                    
    window_choose_file.set_default_response(Gtk.ResponseType.NONE)
    window_choose_file.set_icon_from_file(ICON_LOGO_SMALL)
    
    window_choose_file.set_transient_for(parent)


    if path == '':
        window_choose_file.set_current_folder(HOME_PATH)
    else:
        window_choose_file.set_current_folder(path)
    
    response=window_choose_file.run()
    if response == Gtk.ResponseType.OK:
        file_path=window_choose_file.get_filename()
        window_choose_file.destroy()
        
        if file_path and os.path.exists(file_path):
            default_file_chooser_path=(os.path.dirname(file_path))
        
        return file_path
    else:
        window_choose_file.destroy()        
        return False
    

class VLCWidget(Gtk.DrawingArea):
    """ This class creates a vlc player built in a Gtk.DrawingArea """

    def __init__(self, root_window=False, *p):
        
        super().__init__()
        
        self.set_size_request(320, 200)

        self.connect('map', self._handle_embed)
        
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self._on_mouse_button_press)
        
        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('motion_notify_event', self._on_motion_notify_event)
        
        self.add_events(Gdk.EventMask.SCROLL_MASK)
        self.connect('scroll_event', self._on_mouse_scroll)
        
        self.vlc_instance = vlc.Instance(['--no-xlib'])
        self.player=self.vlc_instance.media_player_new()
        
        self.window_root=root_window
        

        # Variables
        #
        self._vlc_widget_on_top=False
        self._mouse_time=time.time()
        self._volume_increment= 3 # %
        self._die=False
    

    def _handle_embed(self, *args):
        #This makes that the player starts in the root_window
        self.player.set_xwindow(self.get_window().get_xid())
        return True     
        
    def _on_menu_video_subs_audio(self, widget, type, track):
        if type==0:
            state=self.player.audio_set_track(track)
        elif type==1:
            state=self.player.video_set_track(track)
        elif type==2:
            state=self.player.video_set_spu(track)

        return True
        
    def _on_mouse_button_press(self, widget, event):
        
        if event.type == Gdk.EventType._2BUTTON_PRESS:    
            if event.button==1: # left click
                self.fullscreen()
        
        elif event.type == Gdk.EventType.BUTTON_PRESS:
            
            if event.button==1: # left click

                if self._vlc_widget_on_top and self.is_playing():
                    self.player.pause()
                    turn_off_screensaver(False)
                else:
                    self.player.play()
                    turn_off_screensaver(True)
                    
            elif event.button==3:  # right click
                """
                    Audio, Sound and Subtitles Menu
                """
                self.menu=Gtk.Menu()


                # Full screen button
                #
                state=self.window_root.get_window().get_state()
                
                if Gdk.WindowState.FULLSCREEN & state:
                    menuitem=Gtk.ImageMenuItem("Un-Fullscreen")
                else:
                    menuitem=Gtk.ImageMenuItem("Fullscreen")
                menuitem.connect('activate', self.fullscreen)
                self.menu.append(menuitem)

                #   Quit
                #
                menuitem=Gtk.ImageMenuItem("Close")
                menuitem.connect('activate', self.quit)
                self.menu.append(menuitem)
                
                """
                    Audio Menu
                """
                menuitem=Gtk.ImageMenuItem("Audio")
                self.menu.append(menuitem)
                submenu=Gtk.Menu()
                menuitem.set_submenu(submenu)
                
                selected_track=self.player.audio_get_track()
                
                item=Gtk.CheckMenuItem("-1  Disable")
                item.connect('activate', self._on_menu_video_subs_audio, 0, -1)
                if selected_track==-1:
                    item.set_active(True)
                
                submenu.append(item)
                
                try:
                    tracks=[(audio[0], audio[1].decode('utf-8')) for audio in self.player.audio_get_track_description()]
                except Exception as e:
                    tracks=self.player.audio_get_track_description()
                    print(str(e))
                
                
                for track in tracks:
                    if not 'Disable' in track:
                        item=Gtk.CheckMenuItem(format_track(track))
                        item.connect('activate', self._on_menu_video_subs_audio, 0, track[0])
                        if selected_track == track[0]:
                            item.set_active(True)
                        submenu.append(item)
                
                
                """
                    Subtitles
                """
                menuitem=Gtk.ImageMenuItem("Subtitles")
                self.menu.append(menuitem)
                submenu=Gtk.Menu()
                menuitem.set_submenu(submenu)
                
                selected_track=self.player.video_get_spu()
                
                item=Gtk.CheckMenuItem("-1  Disable")
                item.connect('activate', self._on_menu_video_subs_audio, 2, -1)
                if selected_track==-1:
                    item.set_active(True)
                
                submenu.append(item)
                
                try:
                    tracks=[(video_spu[0], video_spu[1].decode('utf-8')) for video_spu in self.player.video_get_spu_description()]
                except Exception as e:
                    tracks=self.player.video_get_spu_description()
                    print(str(e))
                
                for track in tracks:
                    if not 'Disable' in track:
                        item=Gtk.CheckMenuItem(format_track(track))
                        item.connect('activate', self._on_menu_video_subs_audio, 2, track[0])
                        if selected_track == track[0]:
                            item.set_active(True)
                        submenu.append(item)
                
                self.menu.show_all()
                self.menu.popup(None, None, None, None, event.button, event.time)
                
                return True
                    
    def _on_motion_notify_event(self, widget, event, data=None):        
        if self.window_root.is_active():
            self._mouse_time=time.time()
        
    def _on_mouse_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self.volume_up()
            
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.volume_down()
                

    def set_subtitles_from_file(self, widget):
        if os.path.exists(GLOBAL_FILE_PATH):
            path=gtk_file_chooser(self.window_root, os.path.dirname(GLOBAL_FILE_PATH))
        else:
            path=gtk_file_chooser(self.window_root)
            
        if path:
            result=self.player.video_set_subtitle_file(path)
            
        return True

    def quit(self, widget=None):
        self._die=True
        
    def fullscreen(self, widget=None, data=None):
        if Gdk.WindowState.FULLSCREEN & self.window_root.get_window().get_state():
            self.window_root.unfullscreen()
        else:
            self.window_root.fullscreen()

    def volume_up(self):
        actual_volume=self.player.audio_get_volume()
        if actual_volume+self._volume_increment <= 100:
            self.player.audio_set_volume(actual_volume+self._volume_increment)
        else:
            self.player.audio_set_volume(100)
        
    def volume_down(self):
        actual_volume=self.player.audio_get_volume()
        if actual_volume >= self._volume_increment:
            self.player.audio_set_volume(actual_volume-self._volume_increment)
        else:
            self.player.audio_set_volume(0)
            
            
    def is_playing(self):
        if VLCStatePlaying == self.player.get_state():
            return True
            
        return False
    
    def is_paused(self):
        if VLCStatePaused == self.player.get_state():
            return True
            
        return False


class MediaPlayer(Gtk.Window):
    """ This class creates a media player built in a Gtk.Window """

    def __init__(self):
        
        super().__init__()
        
        """
            Variables
        """
        self._width, self._height = 600, 300
        self._stopped_position=0
        self._kill_player_on_quit=False
        self._update_scale_progress=True

        """
        
                G T K 
        
        """
        self._vlc_widget = VLCWidget(self)
        self._vlc_widget.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#000000'))

        overlay=Gtk.Overlay()
        self.add(overlay)
        overlay.add(self._vlc_widget)
        
        # Buttons box
        self._buttons_box=Gtk.VBox()
        self._buttons_box.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self._buttons_box.set_valign(Gtk.Align.CENTER)
        self._buttons_box.set_halign(Gtk.Align.START)
        
        self._button_play_pause=Gtk.ToolButton(Gtk.STOCK_MEDIA_PLAY)
        self._button_play_pause.connect('clicked', self._on_button_play_pause_clicked)
        self._button_play_pause.set_can_focus(False)
        
        self._button_stop=Gtk.ToolButton(Gtk.STOCK_MEDIA_STOP)
        self._button_stop.connect('clicked', self._on_button_player_stop)
        self._button_stop.set_can_focus(False)
        
        self._button_restart=Gtk.ToolButton(Gtk.STOCK_MEDIA_PREVIOUS)
        self._button_restart.connect('clicked', self._on_button_restart_the_video)
        self._button_restart.set_can_focus(False)
        
        self._button_end_video=Gtk.ToolButton(Gtk.STOCK_MEDIA_NEXT)
        self._button_end_video.connect('clicked', self._on_button_end_the_video)
        self._button_end_video.set_can_focus(False)
                    
        self._buttons_box.pack_start(self._button_restart, True, True, 0)
        self._buttons_box.pack_start(self._button_play_pause, True, True, 0)
        self._buttons_box.pack_start(self._button_stop, True, True, 0)
        self._buttons_box.pack_start(self._button_end_video, True, True, 0)

        overlay.add_overlay(self._buttons_box)
        
        # Scales Box        

        self._scales_box=Gtk.Box()
        self._scales_box.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self._scales_box.set_valign(Gtk.Align.END)
        self._scales_box.set_halign(Gtk.Align.CENTER)
        
        self._label_progress=Gtk.Label()
        self._label_progress.set_markup('<span font="{0}" color="white">00:00:00</span>'.format(self._height/29.0))
        self._label_progress.set_margin_right(5)
        self._label_progress.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        
        self._scale_progress=Gtk.Scale()
        self._scale_progress.set_range(0,1)
        self._scale_progress.set_size_request(self._width/2, self._height/29.0)
        self._scale_progress.set_draw_value(False)
        self._scale_progress.set_hexpand(True)
        self._scale_progress.set_can_focus(False)
        self._scale_progress.add_mark(0.25, Gtk.PositionType.TOP, None)
        self._scale_progress.add_mark(0.5, Gtk.PositionType.TOP, None)
        self._scale_progress.add_mark(0.75, Gtk.PositionType.TOP, None)
        self._scale_progress.connect('button-press-event', self._scale_button_press)
        self._scale_progress.connect('button-release-event', self._scale_button_release)

        self._label_lenght=Gtk.Label()
        self._label_lenght.set_markup('<span font="{0}" color="white">00:00:00</span>'.format(self._height/29.0))
        self._label_lenght.set_margin_right(5)
        self._label_lenght.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))     
        
        self._scale_volume=Gtk.VolumeButton()
        self._scale_volume.connect('value_changed', self._scale_volume_changed)
        
        self._scales_box.pack_start(self._label_progress, True, True, 3)
        self._scales_box.pack_start(self._scale_progress, True, True, 1)
        self._scales_box.pack_start(self._label_lenght, True, True, 3)
        self._scales_box.pack_start(self._scale_volume, True, True, 3)
        
        overlay.add_overlay(self._scales_box)   
        
        #   Extra volume label
        
        self._label_volume2=Gtk.Label()
        self._label_volume2.modify_bg(Gtk.StateFlags.NORMAL, Gdk.color_parse('#4D4D4D'))
        self._label_volume2.set_markup('<span font="{1}" color="white"> Vol: {0}% </span>'.format(0, self._height/30.0))
        self._label_volume2.set_valign(Gtk.Align.START)
        self._label_volume2.set_halign(Gtk.Align.END)
        overlay.add_overlay(self._label_volume2)
        
        self.connect('key-press-event', self._on_key_pressed)
        self.connect('delete-event', self._on_button_destroy_window) 
        self.set_size_request(self._width, self._height)
    
        """
            Init the threads
        """
        threading.Thread(target=self._THREAD_mouse_motion).start()
        threading.Thread(target=self._THREAD_player_activity).start()

    def _on_button_destroy_window(self, data=None, data2=None):
        self._vlc_widget.player.stop()
        turn_off_screensaver(False)
        
        if self._kill_player_on_quit:
            Gtk.main_quit()
        else:
            self._stopped_position=0
            self.hide() 
            return True # this prevents the window from being destroyed !!
    
    def _on_button_player_stop(self, data=None):
        self._stopped_position=self._vlc_widget.player.get_position()
        self._vlc_widget.player.stop()
        turn_off_screensaver(False)
        self.hide()
    
    def _on_button_play_pause_clicked(self, button, data=None):
        #
        # Update the icon of the "playing" button
        #
        if not self._vlc_widget.is_playing():
            self._button_play_pause.set_stock_id('gtk-media-pause')
            self._vlc_widget.player.play()
            turn_off_screensaver(True)
        else:
            self._button_play_pause.set_stock_id('gtk-media-play')
            self._vlc_widget.player.pause()
            turn_off_screensaver(False)
    
    def _THREAD_hide_label(self, label):
        time.sleep(1.5)
        Gdk.threads_enter()
        label.hide()
        Gdk.threads_leave()
        
    def _THREAD_mouse_motion(self):
        #
        #   Hide or display the toolboxes
        #
        self.thread_mouse_motion=True
        state='?'
        
        while self.thread_mouse_motion:
            
            movement_time=time.time()-self._vlc_widget._mouse_time
            
            if  state != 'hidden' and movement_time >= 3:
                state='hidden'
                Gdk.threads_enter()
                self._buttons_box.hide()
                self._scales_box.hide()
                Gdk.threads_leave()
            elif state != 'shown' and movement_time < 3:
                state='shown'
                Gdk.threads_enter()
                self._buttons_box.show()
                self._scales_box.show()
                self._label_volume2.show()
                Gdk.threads_leave()
    
            time.sleep(0.3)
            
            
    def _THREAD_player_activity(self):
        """
            This method scans the state of the player to update the tool buttons, volume, play-stop etc
        """
        
        self.thread_player_activity=True
        while self.thread_player_activity:

            time.sleep(0.2)
            
            # Stop the player?
            #
            if self._vlc_widget._die:
                self._on_button_destroy_window()
            
            vlc_is_playing=self._vlc_widget.is_playing()
            vlc_volume=self._vlc_widget.player.audio_get_volume()
            vlc_position=self._vlc_widget.player.get_position()
            scale_volume_value=int(self._scale_volume.get_value()*100)
            scale_progres_value=self._scale_progress.get_value()
                
            # Update the play-pause button
            if vlc_is_playing and self._button_play_pause.get_stock_id()=='gtk-media-play':
                Gdk.threads_enter()
                self._button_play_pause.set_stock_id('gtk-media-pause')
                Gdk.threads_leave()
            elif not vlc_is_playing and self._button_play_pause.get_stock_id()=='gtk-media-pause':
                Gdk.threads_enter()
                self._button_play_pause.set_stock_id('gtk-media-play')
                Gdk.threads_leave()
                        
            """
                Update the volume scale
            """
            if vlc_volume <= 100 and vlc_volume != scale_volume_value:
                
                Gdk.threads_enter()
                self._scale_volume.set_value(vlc_volume/100.000)
                Gdk.threads_leave()
                
                Gdk.threads_enter()
                self._label_volume2.set_markup('<span font="{1}" color="white"> Vol: {0}% </span>'.format(vlc_volume, self._height/30.0))
                Gdk.threads_leave()
                
                Gdk.threads_enter()
                self._label_volume2.show()
                Gdk.threads_leave()
            
                
            elif not self._scales_box.get_property('visible') and self._label_volume2.get_property('visible'):
                threading.Thread(target=self._THREAD_hide_label, args=[self._label_volume2]).start()
            
                                        
            """
                Update the progress scale
            """
            if self._update_scale_progress and scale_progres_value != vlc_position:
                Gdk.threads_enter()
                self._scale_progress.set_value(vlc_position)
                Gdk.threads_leave()
            
            """
                Verify if the window is on top
            """
            if get_active_window_title()==self.get_title():
                self._vlc_widget._vlc_widget_on_top=True
            else:
                self._vlc_widget._vlc_widget_on_top=False   

            """
                Update the time of the player
            """
            if vlc_is_playing:
                video_lenght=format_miliseconds_to_time(self._vlc_widget.player.get_length())+"   "
                
                Gdk.threads_enter()         
                self._label_lenght.set_markup('<span font="{1}" color="white">{0}</span>'.format(video_lenght, self._height/29.0))
                Gdk.threads_leave()
                
                video_time=format_miliseconds_to_time(self._vlc_widget.player.get_time())
                                
                Gdk.threads_enter() 
                self._label_progress.set_markup('<span font="{1}" color="white">{0}</span>'.format(video_time, self._height/29.0))
                Gdk.threads_leave()

                    
            """
                Update the size of the widgets
            """
            if self.get_property('visible'):
                width, height = self.get_size()
                if width != self._width or height != self._height:
                    self._width=width
                    self._height=height
                    
                    Gdk.threads_enter()
                    self._scale_progress.set_size_request(self._width/2,-1)
                    Gdk.threads_leave()
                    
                    Gdk.threads_enter()
                    self._label_volume2.set_markup('<span font="{1}" color="white"> Vol: {0}% </span>'.format(vlc_volume, self._height/30.0))
                    Gdk.threads_leave()     
                    
                    if not vlc_is_playing:
                        video_lenght=self._label_lenght.get_text().strip()
                        video_time=self._label_progress.get_text().strip()
                        
                    Gdk.threads_enter()
                    self._label_lenght.set_markup('<span font="{1}" color="white">{0}</span>'.format(video_lenght, self._height/29.0))      
                    Gdk.threads_leave() 
                    
                    Gdk.threads_enter()
                    self._label_progress.set_markup('<span font="{1}" color="white">{0}</span>'.format(video_time, self._height/29.0))
                    Gdk.threads_leave()

                    #Gdk.threads_enter()
                    #self._buttons_box.set_size_request(self._height/28.0, -1)
                    #Gdk.threads_leave()

            else:
                if vlc_is_playing:
                    self._vlc_widget.player.stop()
            
        
    def _on_key_pressed(self, widget, ev, data=None):
        esc_key=65307
        f11_key=65480
        space_bar=32
        enter_key=65293     
        arrow_up=65362                              
        arrow_down=65364
        arrow_right=65363
        arrow_left=65361

        key=ev.keyval
    
        # display the toolbox if the arrows are shown
        if key==arrow_left or key==arrow_right:
            self._vlc_widget._mouse_time=time.time()

        if key==esc_key:
            self.unfullscreen()
        elif key==f11_key:
            self.fullscreen()
        elif key==space_bar:
            self._on_button_play_pause_clicked(None, None)
        elif key==arrow_up:
            self._vlc_widget.volume_up()
        elif key==arrow_down:
            self._vlc_widget.volume_down()
            

    def _scale_volume_changed(self, widget, value):
        value=int(value*100)
        
        self._label_volume2.set_markup('<span font="{1}" color="white"> Vol: {0}% </span>'.format(value, self._height/30.0))
        if self._vlc_widget.player.audio_get_volume() != value:
            self._vlc_widget.player.audio_set_volume(value)

    def _scale_button_press(self, scale, event):
        self._update_scale_progress=False

    def _scale_button_release(self, scale, event):
        self._vlc_widget.player.set_position(self._scale_progress.get_value())
        self._update_scale_progress=True

    def _on_button_restart_the_video(self, data=None, data2=None):
        self._vlc_widget.player.set_position(0)
        
    def _on_button_end_the_video(self, data=None, data2=None):
        self._vlc_widget.player.set_position(1)
        self._stopped_position=0


    def _delayed_method(self, delay, method, arg=None):
        
        time.sleep(delay)
        
        Gdk.threads_enter()
        if arg==None:
            answer=method()
        else:
            answer=method(arg)
        Gdk.threads_leave()


    def _init_video_time(self, position, start_at):
            # It is necessary to give some time to the player to start playing 
            # so the following methods can be applied. I choosed 0.05 seconds
            time.sleep(0.05)
        
            video_lenght=self._vlc_widget.player.get_length()           
            start_at=str(start_at).split('.')           
            str_seconds=str(start_at[1])
            minuts=int(start_at[0])
            if len(str_seconds) == 1:
                seconds=int(str_seconds)*10
            else:
                seconds=int(str_seconds)
            start_at=minuts*60+seconds

            if video_lenght > 0 and start_at > 0:
                video_lenght=video_lenght/1000.000
                start_at_percent=start_at/video_lenght
            else:
                start_at_percent=0
            if start_at_percent > position:
                start_time=start_at_percent         
            elif position > 0:
                start_time=position
            else:
                start_time=0
                
                
            if start_time > 0:
                Gdk.threads_enter()
                self._vlc_widget.player.set_position(start_time)
                Gdk.threads_leave()

    def is_playing_or_paused(self):
        if self._vlc_widget.is_playing() or self._vlc_widget.is_paused():
            return True
            
        return False
        
    def die_on_quit(self):
        self._kill_player_on_quit=True
    
    def stop_threads(self):
        self.thread_player_activity=False
        self.thread_mouse_motion=False
    
    def get_stopped_position(self):
        return self._stopped_position

    def stop_position(self):
        self._vlc_widget.player.stop()

    def get_position(self):
        return self._vlc_widget.player.get_position()

    def get_state(self):
        return self._vlc_widget.player.get_state()

    def play_video(self, file_path, position=0, subtitles_track=-2, audio_track=-2, start_at=0.0, thread=False):

        if os.path.exists(file_path):
            
            self._stopped_position=position
            
            media=self._vlc_widget.vlc_instance.media_new(file_path)
            media.parse()
            
            turn_off_screensaver(True)
            
            if thread:
                Gdk.threads_enter()
                self._vlc_widget.player.set_media(media)
                Gdk.threads_leave()
                
                Gdk.threads_enter()
                self.set_title(media.get_meta(0))
                Gdk.threads_leave()
                
                Gdk.threads_enter()
                self._vlc_widget.player.play()
                Gdk.threads_leave()
                
                if not self.get_property('visible'):
                    Gdk.threads_enter()
                    self.show_all() 
                    Gdk.threads_leave()
            else:
                self._vlc_widget.player.set_media(media)
                self.set_title(media.get_meta(0))
                self._vlc_widget.player.play()
                if not self.get_property('visible'):
                    self.show_all() 
                    
            threading.Thread(target=self._init_video_time, args=[position, start_at]).start()       
                                
            if subtitles_track == -1 or subtitles_track >= 0:
                threading.Thread(target=self._delayed_method, args=[0.05, 
                                                                    self._vlc_widget.player.video_set_spu, 
                                                                    subtitles_track]
                                ).start()
            
            if audio_track > -2:
                threading.Thread(target=self._delayed_method, args=[0.05, 
                                                                    self._vlc_widget.player.audio_set_track, 
                                                                    audio_track]
                                ).start()
                
                
                

if __name__ == '__main__':
    
    GObject.threads_init()
    Gdk.threads_init()
 
    player=MediaPlayer()
    player.die_on_quit()
    
    player.play_video('/home/public/videos/English/Movies/Kill Bill II')
    
    Gtk.main()

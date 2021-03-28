#!/usr/bin/python3
#

#  Copyright (C) 2014-2016  Rafael Senties Martinelli 
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


import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit', '3.0')
from gi.repository import Gtk, GObject, Gdk, WebKit
import sys
import threading
import time
import webbrowser

from CCParser import CCParser

# local imports
from Paths import *
from MediaPlayer import *
import SeriesAndVideos
from Texts import *


def open_directory(path):
    os.system('''exo-open "{0}" '''.format(os.path.dirname(path)))

def gtk_get_first_selected_cell_from_selection(gtk_selection, column=0):
    
    model, treepaths = gtk_selection.get_selected_rows()

    if treepaths==[]:
        return None
    
    return model[treepaths[0]][column]
            

def gtk_set_first_selected_cell_from_selection(gtk_selection, column, value):
    
    model, treepaths = gtk_selection.get_selected_rows()

    if len(treepaths) > 0:
        model[treepaths[0]][column]=value
        

def gtk_remove_first_selected_row_from_liststore(gtk_selection):
    
    model, treepaths = gtk_selection.get_selected_rows()
    
    if len(treepaths) > 0:
        model.remove(model.get_iter(treepaths[0]))
    

def gtk_get_merged_cells_from_treepath(gtk_liststore, gtk_treepath, cell1, cell2):
    return '{}{}'.format(gtk_liststore[gtk_treepath][cell1], gtk_liststore[gtk_treepath][cell2])
    

def gtk_default_font_color():
    settings=Gtk.Settings.get_default()
    
    colors=settings.get_property('gtk-color-scheme')
    colors=colors.split('\n')
    
    for color in colors:
        if 'text' in color:
            text_color=color.split(':')[1].strip()
            return text_color
            
            if ';' in text_color:
                text_color=text_color.split(';',1)[0]
            
            break
            
    return '#000000'


def gtk_info(parent,text1,text2=None):

        dialog=Gtk.MessageDialog(   parent,
                                    Gtk.DialogFlags.MODAL,
                                    Gtk.MessageType.INFO,
                                    Gtk.ButtonsType.CLOSE,
                                    text1)
                                    
        dialog.set_default_response(Gtk.ResponseType.NONE)
        
        dialog.set_icon_from_file(ICON_LOGO_SMALL)

        if text2 != None:
            dialog.format_secondary_text(text2)
        
        response=dialog.run()
        dialog.destroy()


def gtk_folder_chooser(parent):

    window_choose_folder=Gtk.FileChooserDialog(TEXT_PROGRAM_NAME,
                                                parent,
                                                Gtk.FileChooserAction.SELECT_FOLDER,
                                                (Gtk.STOCK_CANCEL, 
                                                    Gtk.ResponseType.CANCEL,
                                                    Gtk.STOCK_OPEN, 
                                                    Gtk.ResponseType.OK))

    window_choose_folder.set_icon_from_file(ICON_LOGO_SMALL)
    
    window_choose_folder.set_current_folder(HOME_PATH)
    
    response=window_choose_folder.run()
    if response == Gtk.ResponseType.OK:
        folder_path=window_choose_folder.get_filename()
        window_choose_folder.destroy()
        
        if folder_path and os.path.exists(folder_path):
            default_folder_chooser_path=os.path.dirname(folder_path)
        
        return folder_path
    else:
        window_choose_folder.destroy()
        return False
        
        
        
def gtk_file_chooser(parent, mode='', path=''):

    window_choose_file=Gtk.FileChooserDialog(   TEXT_PROGRAM_NAME,
                                                parent,
                                                Gtk.FileChooserAction.OPEN,
                                                (Gtk.STOCK_CANCEL, 
                                                    Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN, 
                                                    Gtk.ResponseType.OK))
                                                    
    window_choose_file.set_default_response(Gtk.ResponseType.NONE)
    window_choose_file.set_icon_from_file(ICON_LOGO_SMALL)
    
    window_choose_file.set_transient_for(parent)

    if mode=='picture':
        filter=Gtk.FileFilter()
        filter.set_name('Picture')
        filter.add_pattern('*.jpeg')
        filter.add_pattern('*.jpg')
        filter.add_pattern('*.png')
        window_choose_file.add_filter(filter)   


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
        
def gtk_dialog_question(parent,text1,text2):

    dialog=Gtk.MessageDialog(   parent,
                                Gtk.DialogFlags.MODAL,
                                Gtk.MessageType.QUESTION,
                                Gtk.ButtonsType.YES_NO,
                                text1)
    
    
    dialog.set_icon_from_file(ICON_LOGO_SMALL)
    
    if text2 != None:
        dialog.format_secondary_text(text2)
    
    response=dialog.run()
    if response == Gtk.ResponseType.YES:
        dialog.hide()
        return True
        
    elif response == Gtk.ResponseType.NO:
        dialog.hide()
        return False

class CurrentMedia:
    def __init__(self, serie=None, video=None, random=None, mark=None):
        self.serie=serie
        self.video=video
        self.random=random
        self.mark=mark

class GUI(object):
    
    def __init__(self):
    
        """
            load items from glade
        """
        builder=Gtk.Builder()
        builder.add_from_file(GLADE_FILE)
        builder.connect_signals(self)

        glade_objects_ids=(
        
        'window_root', 
            'label_current_serie',                  'treeview_selection_episodes',      'progressbar',              'checkbox_hidden_items', 
            'eventbox_selected_serie_name',         'button_root_play_and_stop',        'treeview_episodes',        'treeview_series', 
            'treeview_selection_series',            'liststore_series',                 'liststore_episodes',       'spinbutton_audio',             'spinbutton_subtitles', 
            'spinbutton_start_at',                  'box_episodes', 'box_series',       'box_main',                 'box_serie_data', 
            'box_series_menu',                      'box_main', 'column_number',        'column_name',              'column_extension',             'column_play',              'column_oplayed', 
            'column_rplayed',                       'checkbutton_random',               'checkbutton_keep_playing', 'checkbox_hide_extensions',     'checkbox_hide_number', 
            'checkbox_hide_name',                   'checkbox_hide_extension',          'checkbox_hide_play',       'checkbox_hide_oplayed',        'checkbox_hide_rplayed', 
            'checkbox_hide_warning_missingserie',   'checkbox_hide_missing_series',
        
        'window_rename',
            'entry_rename', 'label_old_name',
            
        'window_about',
        'window_controlls',
        'window_files',
        'window_preferences',
        'window_finding_files',
        )

        for glade_object_id in glade_objects_ids:
            setattr(self, glade_object_id, builder.get_object(glade_object_id))

        """
            Media Player
        """
        self.current_media=CurrentMedia()
        self.media_player=MediaPlayer()
        self.media_player.set_icon_from_file(ICON_LOGO_SMALL)
        threading.Thread(target=self.THREAD_scan_media_player).start()
        
        
        """
            configuration
        """     

        # list of clases
        self.list_episodes_class=[]
            
        # font colors
        color = Gdk.RGBA()
        color.parse(gtk_default_font_color())
        color.to_string()   
        self.default_font_color=color
        
        color = Gdk.RGBA()
        color.parse('#FF0000')
        color.to_string()   
        self.hiden_font_color=color
                
        # extra

        self.window_root.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.window_root.connect('delete-event', self.quit_the_program)

        self.ccp=CCParser(CONFIGURATION_FILE,'vlist-player')
        
        # checkboxes
        self.checkbox_hide_number.set_active(self.ccp.get_bool('number'))
        self.checkbox_hide_name.set_active(self.ccp.get_bool('name'))
        self.checkbox_hide_extension.set_active(self.ccp.get_bool('extensions'))
        self.checkbox_hide_play.set_active(self.ccp.get_bool('play'))
        self.checkbox_hide_oplayed.set_active(self.ccp.get_bool('oplayed'))
        self.checkbox_hide_rplayed.set_active(self.ccp.get_bool('rplayed'))
        self.checkbox_hide_warning_missingserie.set_active(self.ccp.get_bool('warningMissingSerie'))
        self.checkbox_hidden_items.set_active(self.ccp.get_bool_defval('hidden', False))
        self.checkbox_hide_missing_series.set_active(self.ccp.get_bool_defval('hide-missing-series', False))

        """
            Display the window
        """
        self.window_root.show_all()

        if not self.ccp.get_bool_defval('fullmode', False):
            self.HIDE_episodes_menu(False)
        
        """
            load the existents lists
        """
        threading.Thread(target=self.LOAD_data_series).start()

    def LOAD_data_series(self):
        """
            Load the saved lists
        """ 
        if os.path.exists(FOLDER_LIST_PATH):
            data_files=[ f for f in os.listdir(FOLDER_LIST_PATH) if os.path.isfile(os.path.join(FOLDER_LIST_PATH,f)) ]
            data_files.sort()
            for data_file in data_files:
                if data_file.lower().endswith('.csv'):
                    data_path='{}/{}'.format(FOLDER_LIST_PATH, data_file)
                    
                    with open(data_path, mode='rt', encoding='utf-8') as f:
                        serie_info=f.readline().split('|')
                    
                    path=''
                    recursive=False
                    keep_playing=True
                    random=False
                    audio_track=-2
                    subtitles_track=-2
                    start_at=-2
                    
                    try: # support for versions <= 0.0~0
                        path=serie_info[0]
                        recursive=serie_info[1]     
                        try: # support for  versions < 0.1~7
                            random=serie_info[2]
                            keep_playing=serie_info[3]
                            try: # support for versions < 0.7~2
                                start_at=serie_info[4]
                                audio_track=serie_info[5]
                                subtitles_track=serie_info[6]
                            except Exception as e:
                                print("LOAD_data_series error(3):")
                                print(str(e))                                             
                        except Exception as e:
                            print("LOAD_data_series error(2):")
                            print(str(e))
                    except Exception as e:
                        print("LOAD_data_series error(1):")
                        print(str(e))
                            
                    if '/' in path:     
                        self.LOAD_serie_from_path(  path, 
                                                    data_path, 
                                                    recursive, 
                                                    random, 
                                                    keep_playing,
                                                    start_at,
                                                    audio_track, 
                                                    subtitles_track)


            """
                Load the last serie that has been played
            """
            current_serie_name=self.ccp.get_str('current_series')
            
            for i, row in enumerate(self.liststore_series):
                if row[1] == current_serie_name:
                    Gdk.threads_enter()
                    self.treeview_series.set_cursor(i)
                    Gdk.threads_leave()
                    break


    def THREAD_scan_media_player(self):
        self.thread_vlc_scan=True
        
        while self.thread_vlc_scan:
        
            if self.current_media.serie != None:
        
                position=self.media_player.get_position()
                stopped_position=self.media_player.get_stopped_position()
                serie=self.current_media.serie
            
                # If the player was stopped
                if stopped_position > 0:
                    serie.set_video_position(self.current_media.video,stopped_position)
            
                # If the current video got to the end..
                if round(position, 3) >= 0.999:
                    
                    self.current_media.serie.mark_episode(self.current_media.video,self.current_media.random,True)
                    
                    self.EPISODE_update()
                    
                    Gdk.threads_enter()
                    self.POPULATE_listore_episodes(True)
                    Gdk.threads_leave()
                    
                    
                    if self.checkbutton_keep_playing.get_active():
                        if self.current_media.video:
                            self.media_player.play_video(   self.current_media.video.get_path(),
                                                            self.current_media.video.get_position(),
                                                            serie.get_subtitles_track(), 
                                                            serie.get_audio_track(), 
                                                            serie.get_start_at(),
                                                            True)

                        else:
                            Gdk.threads_enter()
                            self.media_player.hide()
                            Gdk.threads_leave()
                            Gdk.threads_enter()
                            gtk_info(self.window_root,TEXT_END_OF_SERIE)
                            Gdk.threads_leave()
                    else:
                        Gdk.threads_enter()
                        self.media_player.stop_position()
                        Gdk.threads_leave()
                        Gdk.threads_enter()
                        self.media_player.hide()
                        Gdk.threads_leave()

            time.sleep(0.5)

    def POPULATE_listore_episodes(self, update_liststore):
            
        if self.treeview_selection_episodes.count_selected_rows() >= 0:
                    
            selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            serie=SeriesAndVideos.series_dictionary[selected_serie_name]

            #
            #    Update the series area
            #
            
            self.checkbutton_keep_playing.set_active(serie.get_keep_playing())
            self.checkbutton_random.set_active(serie.get_random())
            
            self.spinbutton_audio.set_value(serie.get_audio_track())
            self.spinbutton_subtitles.set_value(serie.get_subtitles_track())
            self.spinbutton_start_at.set_value(serie.get_start_at())

            if self.checkbutton_random.get_active():
                (played,total,percent)=serie.get_r_played_stats()
            else:
                (played,total,percent)=serie.get_o_played_stats()

            progress_text="{}/{}".format(played, total)
            
            self.label_current_serie.set_label(selected_serie_name)
            self.progressbar.set_fraction(percent)
            
            self.progressbar.set_text(progress_text)
            self.progressbar.set_show_text(True)

            #   Update the big image
            for children in self.eventbox_selected_serie_name.get_children():
                self.eventbox_selected_serie_name.remove(children)
            
            image=serie.get_big_image()
            self.eventbox_selected_serie_name.add(image)
            image.show()
            
            
            """
                update the episodes area
            """
            if update_liststore:
                self.liststore_episodes.clear()
                self.column_name.set_spacing(0)

                if os.path.exists(serie.get_path()):
                    
                    # inizialize the list
                    videos_list=[]
                    for video in serie.get_videos():
                        videos_list.append(None)
                                    
                    # sort it by id
                    for video in serie.get_videos():
                        try:
                            videos_list[video.get_id()-1]=video
                        except Exception as e:
                            print(str(e))
                            
                    
                    for video in videos_list:
                        if video:
                            
                            # get the color of the font
                            if video.get_display():
                                color=self.default_font_color
                            else:
                                color=self.hiden_font_color

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
                            print("Error loading the liststore_episodes. The serie '{}' has an empty video.".format(serie.get_name()))


    def HIDE_episodes_menu(self, write=True):
        
        (rx,ry)=self.window_root.get_size()
        state=self.box_episodes.get_visible()

        if state:
            bx=self.box_episodes.get_allocation().width 
            self.box_episodes.hide()
            self.window_root.resize(rx-bx-15,ry) # 15 is the border with
            self.box_main.set_child_packing(self.box_series, True, True, 0, Gtk.PackType.START)
        else:
            self.box_main.set_child_packing(self.box_series, False, False, 0, Gtk.PackType.START)
            self.box_episodes.show_all()
        
        if write:
            self.ccp.write('fullmode', not state)

    def EPISODE_open_dir(self, widget, video_name):
        
        serie=SeriesAndVideos.series_dictionary[gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        path=serie.get_path_from_video_name(video_name)

        if os.path.exists(path):
            open_directory(path)

    def EPISODE_update(self):
        serie=SeriesAndVideos.series_dictionary[gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        
        self.current_media.serie=serie
                
        if self.checkbutton_random.get_active():
            self.current_media.video=serie.get_r_episode()
        else:
            self.current_media.video=serie.get_o_episode()  
        
        self.current_media.random=self.checkbutton_random.get_active()

    def LOAD_serie_from_path(self,  path,
                                    data_path,
                                    recursive,
                                    random,
                                    keep_playing,
                                    start_at=0.0,
                                    audio_track=-2,
                                    subtitles_track=-2):

        new_serie=SeriesAndVideos.Serie(path,
                                        data_path,
                                        recursive,
                                        random,
                                        keep_playing,
                                        start_at,
                                        audio_track,
                                        subtitles_track,
                                        )
        
        if os.path.exists(new_serie.get_path()) or not self.checkbox_hide_missing_series.get_active():
            Gdk.threads_enter()
            self.liststore_series.append([new_serie.get_image(), new_serie.get_name()])
            Gdk.threads_leave()
        
        # select the row once a serie has been added
        for i, row in enumerate(self.liststore_series):
            if row[1]==new_serie.get_name():
                
                Gdk.threads_enter()
                self.treeview_series.set_cursor(i)
                Gdk.threads_leave()
                
                break

    def POPULATE_listore_series(self):

        # Populate
        #
        Gdk.threads_enter()
        self.liststore_series.clear()
        Gdk.threads_leave()
        
        for name in sorted(SeriesAndVideos.series_dictionary.keys()):
            serie=SeriesAndVideos.series_dictionary[name]
            
            if os.path.exists(serie.get_path()) or not self.checkbox_hide_missing_series.get_active():
                
                Gdk.threads_enter()
                self.liststore_series.append([serie.get_image(), serie.get_name()])
                Gdk.threads_leave()
            
        if len(self.liststore_series) <= 0:
            Gdk.threads_enter()
            self.eventbox_selected_serie_name.add(Gtk.Image.new_from_file(ICON_LOGO_BIG))
            Gdk.threads_leave()
            
        # Select the current serie
        #
        current_serie_name=self.ccp.get_str('current_series')

        for i, row in enumerate(self.liststore_series):
            if row[1]==current_serie_name:
                Gdk.threads_enter()
                self.treeview_series.set_cursor(i)
                Gdk.threads_leave()
                return
        
        Gdk.threads_enter()
        self.treeview_series.set_cursor(0) 
        Gdk.threads_leave()


    def SERIE_open(self, widget):
        serie=SeriesAndVideos.series_dictionary[gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        open_directory(serie.get_path())

    def SERIE_find_videos(self, widget, video_names):

        serie=SeriesAndVideos.series_dictionary[gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

        path=gtk_file_chooser(self.window_root)

        if path:
            if len(video_names)==1: # if the user only selected one video to find..
                found_videos=serie.find_video(video_names[0], path)             
                if found_videos:
                    gtk_info(self.window_root,TEXT_X_OTHER_VIDEOS_HAVE_BEEN_FOUND.format(found_videos),None)
                
            elif len(video_names)>1:
                found_videos=serie.find_videos(path)
                
                if found_videos:
                    gtk_info(self.window_root,TEXT_X_VIDEOS_HAVE_BEEN_FOUND.format(found_videos),None)
        
            self.POPULATE_listore_episodes(True)

    def SERIE_add_picture(self, widget):
        """
            Add a picture to a serie
        """
        file=gtk_file_chooser(self.window_root,'picture')
        if file:
            serie=SeriesAndVideos.series_dictionary[gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

            serie.set_image(file)
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 0, serie.get_image())
            self.POPULATE_listore_episodes(False)

    def SERIE_find(widget, self):
        
        path=gtk_folder_chooser(self.window_root)
        
        if path:
            serie=SeriesAndVideos.series_dictionary[gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]

            serie.find_serie(path)
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 0, serie.get_image())
            self.POPULATE_listore_episodes(True)


    def SERIE_reset(widget, self):
        
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        
        if gtk_dialog_question(self.window_root,TEXT_RESET_SERIE.format(selected_serie_name),None):
            serie=SeriesAndVideos.series_dictionary[selected_serie_name]
            serie.reset_data()
            self.POPULATE_listore_episodes(True)

    def SERIE_rename(self, widget):
        """
            change the name of a serie
        """
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        
        self.label_old_name.set_text(selected_serie_name)
        self.entry_rename.set_text(selected_serie_name)
        
        self.window_rename.show()


    def SERIE_delete(self, widget):
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        
        if gtk_dialog_question(self.window_root,TEXT_DELETE_SERIE.format(selected_serie_name),None):

            SeriesAndVideos.series_dictionary.pop(selected_serie_name)

            gtk_remove_first_selected_row_from_liststore(self.treeview_selection_series)

            if os.path.exists(SERIE_PATH.format(selected_serie_name)):
                os.remove(SERIE_PATH.format(selected_serie_name))

    def SERIE_ignore_episode(self, widget):

        (model, treepaths)=self.treeview_selection_episodes.get_selected_rows()
        
        if not treepaths==[]:
            selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            serie=SeriesAndVideos.series_dictionary[selected_serie_name]
            
            for treepath in treepaths:
                episode_name=gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
                serie.ignore_video(episode_name)

            self.POPULATE_listore_episodes(True)

    def SERIE_dont_ignore_episode(self, widget):

        (model, treepaths)=self.treeview_selection_episodes.get_selected_rows()
        
        if not treepaths==[]:
            selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            serie=SeriesAndVideos.series_dictionary[selected_serie_name]

            for treepath in treepaths:
                episode_name=gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
                serie.dont_ignore_video(episode_name)


            self.POPULATE_listore_episodes(True)

    def quit_the_program(self, widget, data=None):
                
        if self.media_player.get_property('visible'):
            self.window_root.hide()
            self.media_player.die_on_quit()
            return True
        else:
            self.thread_vlc_scan=False
            self.media_player.stop_threads()
            Gtk.main_quit()


    def on_spinbutton_audio_value_changed(self, spinbutton):
        value=spinbutton.get_value_as_int()
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        SeriesAndVideos.series_dictionary[selected_serie_name].set_audio_track(value)
        
    def on_spinbutton_subtitles_value_changed(self, spinbutton):
        value=spinbutton.get_value_as_int()
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        SeriesAndVideos.series_dictionary[selected_serie_name].set_subtitles_track(value)

    def on_spinbutton_start_at_value_changed(self, spinbutton):
        value=float(spinbutton.get_value())
        
        str_value=str(value).split('.')
        minuts=int(str_value[0])
        seconds=int(str_value[1])
        if seconds > 60:
            minuts+=1   
            spinbutton.set_value(minuts+0.00)

        serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        SeriesAndVideos.series_dictionary[serie_name].set_start_at(value)

    def on_checkbutton_random_toggled(self, radiobutton, data=None):
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        radiobutton_state=radiobutton.get_active()
        SeriesAndVideos.series_dictionary[selected_serie_name].set_random(radiobutton_state)
        self.POPULATE_listore_episodes(False)

    def on_checkbutton_keep_playing_toggled(self, radiobutton, data=None):
        serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        radiobutton_state=radiobutton.get_active()
        SeriesAndVideos.series_dictionary[serie_name].set_keep_playing(radiobutton_state)


    def on_checkbox_hide_number_toggled(self, widget, data=None):
        state=self.checkbox_hide_number.get_active()
        self.column_number.set_visible(not state)
        self.ccp.write('number', state)
        
    def on_checkbox_hide_name_toggled(self, widget, data=None):
        state=self.checkbox_hide_name.get_active()
        self.column_name.set_visible(not state)
        self.ccp.write('name', state)
        
    def on_checkbox_hide_extension_toggled(self, widget, data=None):    
        state=self.checkbox_hide_extension.get_active() 
        self.column_extension.set_visible(not state)
        self.ccp.write('extensions', state)

    def on_checkbox_hide_play_toggled(self, widget, data=None):
        state=self.checkbox_hide_play.get_active()
        self.column_play.set_visible(not state)
        self.ccp.write('play', state)

    def on_checkbox_hide_oplayed_toggled(self, widget, data=None):
        state=self.checkbox_hide_oplayed.get_active()
        self.column_oplayed.set_visible(not state)
        self.ccp.write('oplayed', state)
        
    def on_checkbox_hide_rplayed_toggled(self, widget, data=None):
        state=self.checkbox_hide_rplayed.get_active()
        self.column_rplayed.set_visible(not state)
        self.ccp.write('rplayed', state)

    def on_checkbox_hidden_items_toggled(self, button, data=None):
        self.ccp.write('hide-items', self.checkbox_hidden_items.get_active())
        self.POPULATE_listore_episodes(True)

    def on_checkbox_hide_warning_missingserie_toggled(self, button, data=None):
        self.ccp.write('warningMissingSerie', self.checkbox_hide_warning_missingserie.get_active())

    def on_checkbox_episodes_toggled(self, row, column):
        
        state=not self.liststore_episodes[row][column]
        
        self.liststore_episodes[row][column]=state
        
        serie=SeriesAndVideos.series_dictionary[gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)]
        episode_name='{}{}'.format(self.liststore_episodes[row][1], self.liststore_episodes[row][2])
        
        serie.change_checkbox_state(episode_name, column, state)
        
        self.POPULATE_listore_episodes(False)

        
    def on_button_close_preferences_clicked(self, button, data=None):
        self.window_preferences.hide()

    def on_button_close_controlls_clicked(self, button, data=None):
        self.window_controlls.hide()
        
    def on_button_close_files_clicked(self, button, data=None):
        self.window_files.hide()
        
    def on_button_cancel_rename_clicked(self, button, data=None):
        self.window_rename.hide()
    
    def on_button_close_window_list_clicked(self,button, data=None):
        self.window_list.hide()

    def on_treeview_episodes_drag_end(self, widget, data=None):

        # Get the new order
        new_order=[row[0] for row in self.liststore_episodes]
        
        # Update the treeview
        for i, row in enumerate(self.liststore_episodes, 1):
            row[0]=i        

        # Update the CSV file
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        serie=SeriesAndVideos.series_dictionary[selected_serie_name]
        serie.reorder(new_order)

            
    def on_button_okey_rename_clicked(self, button, data=None):
        
        current_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        new_name=self.entry_rename.get_text()
    
        if new_name in SeriesAndVideos.series_dictionary.keys():
            gtk_info(self.window_rename,TEXT_SERIE_NEWNAME_ALREADY_EXISTS.format(new_name),None)
                
        elif not current_name == new_name:
    
            serie=SeriesAndVideos.series_dictionary[current_name]
            serie.rename(new_name)
            SeriesAndVideos.series_dictionary.pop(current_name)
            SeriesAndVideos.series_dictionary[new_name]=serie
            gtk_set_first_selected_cell_from_selection(self.treeview_selection_series, 1, new_name)
            self.label_current_serie.set_label(new_name)
            
            self.EPISODE_update()
            
        self.window_rename.hide()

    
    def on_imagemenuitem_bugs_activate(self, button, data=None):
        webbrowser.open('https://github.com/rsm-gh/vlist-player/issues',new=2)
    
    def on_imagemenuitem_preferences_activate(self, button, data=None):
        self.window_preferences.show()

    def on_menuitem_list_from_folder_recursive_activate(self, button,data=None):
        path=gtk_folder_chooser(self.window_root)
        if path:
            serie_name=os.path.basename(path)
            
            for serie in SeriesAndVideos.series_dictionary.values():
                if serie.get_path()==path:
                    gtk_info(self.window_root,TEXT_SERIE_ALREADY_EXISTS,None)
                    return
                    
                    
                if serie.get_name()==serie_name:
                    gtk_info(self.window_root,TEXT_SERIE_NAME_ALREADY_EXISTS.format(serie_name),None)
                    return
            
            threading.Thread(target=self.LOAD_serie_from_path, args=[path,None,True,False,True]).start()


    def on_menuitem_checkbox_activated(self, widget, column, state):
        
        (model, treepaths)=self.treeview_selection_episodes.get_selected_rows()
        
        if not treepaths==[]:
        
            selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
            serie=SeriesAndVideos.series_dictionary[selected_serie_name]
            
            episode_names=[]
            for treepath in treepaths:

                episode_name=gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2)
                
                self.liststore_episodes[treepath][column]=state
                
                episode_names.append(episode_name)
                
            serie.change_checkbox_state(episode_names,column,state)     
            
            self.POPULATE_listore_episodes(True)

    def on_menuitem_list_from_folder_activate(self, button, data=None):
        path=gtk_folder_chooser(self.window_root)
        if path:
            
            serie_name=os.path.basename(path)
            
            for serie in SeriesAndVideos.series_dictionary.values():
                if serie.get_path()==path:
                    gtk_info(self.window_root,TEXT_SERIE_ALREADY_EXISTS,None)
                    return
                    
                if serie.get_name()==serie_name:
                    gtk_info(self.window_root,TEXT_SERIE_NAME_ALREADY_EXISTS.format(serie_name),None)
                    return
                    
            
            threading.Thread(target=self.LOAD_serie_from_path, args=[path,None,False,False,True]).start()
    
    def on_button_close_find_files_clicked(self, button, data=None):
        self.window_finding_files.hide()

    def on_imagemenuitem_finding_files_activate(self, button, data=None):
        self.window_finding_files.show()

    def on_imagemenuitem_about_activate(self, button, data=None):
        response=self.window_about.run()
        self.window_about.hide()

    def on_imagemenuitem_controls_activate(self, button, data=None):
        self.window_controlls.show()
        
    def on_imagemenuitem_files_activate(self, button, data=None):
        self.window_files.show()    

    def on_checkbox_hide_missing_series_toggled(self, button, data=None):
        self.ccp.write('hide-missing-series', self.checkbox_hide_missing_series.get_active())
        threading.Thread(target=self.POPULATE_listore_series).start()
        
    def on_window_root_button_press_event(self, widget, event):
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == 3: # right click
                self.HIDE_episodes_menu()

    def on_cellrenderertoggle_play_toggled(self, liststore, row):
        self.on_checkbox_episodes_toggled(int(row), 4)
        
    def on_cellrenderertoggle_oplayed_toggled(self, liststore, row):
        self.on_checkbox_episodes_toggled(int(row), 5)

    def on_cellrenderertoggle_rplayed_toggled(self, liststore, row):
        self.on_checkbox_episodes_toggled(int(row), 6)

    def on_treeview_episodes_press_event(self, treeview, event):
        (model, treepaths)=self.treeview_selection_episodes.get_selected_rows()

        if treepaths==[]:
            return
                
        selection_length=len(treepaths)
        
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        serie=SeriesAndVideos.series_dictionary[selected_serie_name]
        
        """
            Active or desactive the buttons move up and down
        """
        
        if event.button == 1 and selection_length==1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            episode_name=gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepaths[0], 1, 2)
            
            path=serie.get_path_from_video_name(episode_name)
                
            if path and os.path.exists(path):
                self.media_player.play_video(path, 0, serie.get_subtitles_track(), serie.get_audio_track(), serie.get_start_at())
            else:
                gtk_info(self.window_root,TEXT_CANT_PLAY_MEDIA_MISSING)
        
    
        elif event.button == 3: # right click

            # get the iter where the user is pointing
            try:
                pointing_treepath=self.treeview_episodes.get_path_at_pos(event.x, event.y)[0]
            except:
                return

            # if the iter is not in the selected iters, remove the previous selection
            model, treepaths = self.treeview_selection_episodes.get_selected_rows()
            
            if not pointing_treepath in treepaths:
                self.treeview_selection_episodes.unselect_all()
                self.treeview_selection_episodes.select_path(pointing_treepath)
            
            self.menu=Gtk.Menu()
            
            """
                Open the containing folder (only if the user selected one video)
            """
            if selection_length==1: 
        
                selected_episode_name=gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepaths[0], 1, 2)
                        
                menuitem=Gtk.ImageMenuItem(TEXT_FOLDER)
                self.menu.append(menuitem)
                menuitem.connect('activate', self.EPISODE_open_dir, selected_episode_name)
                img = Gtk.Image(stock=Gtk.STOCK_OPEN)
                menuitem.set_image(img)


            elif selection_length>1:
            
                for i, label in enumerate((TEXT_PLAY,TEXT_O_PLAYED,TEXT_R_PLAYED), 4):
                
                    # mark to check
                    menuitem=Gtk.ImageMenuItem(label)
                    self.menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, i, True)
                    img = Gtk.Image(stock=Gtk.STOCK_APPLY)                                      
                    menuitem.set_image(img)
                    
                    # mark to uncheck
                    menuitem=Gtk.ImageMenuItem(label)
                    self.menu.append(menuitem)
                    menuitem.connect('activate', self.on_menuitem_checkbox_activated, i, False)       
                    img = Gtk.Image(stock=Gtk.STOCK_MISSING_IMAGE)                              
                    menuitem.set_image(img)
                    
            
            """
                Menu "Fin videos"
            """ 
            list_of_names=[gtk_get_merged_cells_from_treepath(self.liststore_episodes, treepath, 1, 2) for treepath in treepaths]

            if serie.missing_videos(list_of_names):

                menuitem=Gtk.ImageMenuItem(TEXT_FIND)
                menuitem.connect('activate', self.SERIE_find_videos, list_of_names)
                self.menu.append(menuitem)
                img = Gtk.Image(stock=Gtk.STOCK_DIALOG_WARNING)
                menuitem.set_image(img)
            
            # ignore videos
            menuitem=Gtk.ImageMenuItem(TEXT_IGNORE)
            self.menu.append(menuitem)
            menuitem.connect('activate', self.SERIE_ignore_episode)
            img = Gtk.Image(stock=Gtk.STOCK_FIND_AND_REPLACE)
            menuitem.set_image(img)
            
            # don't ignore videos
            menuitem=Gtk.ImageMenuItem(TEXT_DONT_IGNORE)
            self.menu.append(menuitem)
            menuitem.connect('activate', self.SERIE_dont_ignore_episode)
            img = Gtk.Image(stock=Gtk.STOCK_FIND)
            menuitem.set_image(img)
            
            self.menu.show_all()
            self.menu.popup(None, None, None, None, event.button, event.time)
            

            return True
            

    def on_treeview_selection_series_changed(self, treeselection):
        if treeselection.count_selected_rows() > 0:
            self.POPULATE_listore_episodes(True)

    def on_eventbox_selected_serie_name_button_press_event(self, box, event, data=None):
        self.on_treeview_series_press_event(self.treeview_series, event, False)

    def on_treeview_series_press_event(self, treeview, event, inside_treeview=True):
        # check if some row is selected
        if self.treeview_selection_series.count_selected_rows() < 0:
            return
                
        selected_serie_name=gtk_get_first_selected_cell_from_selection(self.treeview_selection_series, 1)
        serie=SeriesAndVideos.series_dictionary[selected_serie_name]

                 
        if event.type == Gdk.EventType._2BUTTON_PRESS:
            if event.button == 1: # left click
                
                # check if the liststore is empty
                if len(self.liststore_episodes) <= 0 and not self.checkbox_hide_warning_missingserie.get_active():
                    gtk_info(self.window_root,TEXT_CANT_PLAY_SERIE_MISSING,None)

                """
                    Play a video of the serie
                """                
                self.ccp.write('current_series', selected_serie_name)
                
                if not self.media_player.is_playing_or_paused() or self.current_media.serie.get_name() != selected_serie_name:
                    self.EPISODE_update()
                    
                    if not self.current_media.video:
                        gtk_info(self.window_root,TEXT_END_OF_SERIE)
                        self.media_player.hide()
            
                    elif not os.path.exists(self.current_media.video.get_path()):
                        gtk_info(self.window_root,TEXT_CANT_PLAY_MEDIA_MISSING)
                        self.media_player.hide()
                    else:
                        self.media_player.play_video(   self.current_media.video.get_path(), 
                                                        self.current_media.video.get_position(),
                                                        serie.get_subtitles_track(), 
                                                        serie.get_audio_track(), 
                                                        serie.get_start_at(),
                                                        )
 
                        self.media_player.present()
                else:
                    self.media_player.present()

        
        elif event.type == Gdk.EventType.BUTTON_PRESS:
            
            if self.treeview_selection_series.count_selected_rows() >= 0 and event.button ==3:# right click

                # get the iter where the user is pointing
                pointing_treepath=self.treeview_series.get_path_at_pos(event.x, event.y)[0]

                # if the iter is not in the selected iters, remove the previous selection
                model, treepaths = self.treeview_selection_series.get_selected_rows()
                
                if not pointing_treepath in treepaths and inside_treeview:
                    self.treeview_selection_series.unselect_all()
                    self.treeview_selection_series.select_path(pointing_treepath)


                """ 
                    Right click menu
                """
                self.menu=Gtk.Menu()
            
                if os.path.exists(serie.get_path()):
                    
                    menuitem=Gtk.ImageMenuItem(TEXT_OPEN_FOLDER)
                    self.menu.append(menuitem)
                    menuitem.connect('activate', self.SERIE_open)
                    img = Gtk.Image(stock=Gtk.STOCK_OPEN)
                    menuitem.set_image(img)
                    
                    menuitem=Gtk.ImageMenuItem(TEXT_RENAME)
                    self.menu.append(menuitem)
                    menuitem.connect('activate', self.SERIE_rename)
                    img = Gtk.Image(stock=Gtk.STOCK_BOLD)
                    menuitem.set_image(img)
                    
                    menuitem=Gtk.ImageMenuItem(TEXT_RESET)
                    self.menu.append(menuitem)
                    menuitem.connect('activate', self.SERIE_reset)
                    img = Gtk.Image(stock=Gtk.STOCK_REFRESH)
                    menuitem.set_image(img)
                
                    menuitem=Gtk.ImageMenuItem(TEXT_ADD_PICTURE)
                    self.menu.append(menuitem)
                    menuitem.connect('activate', self.SERIE_add_picture)
                    img = Gtk.Image(stock=Gtk.STOCK_SELECT_COLOR)
                    menuitem.set_image(img)
                else:
                    menuitem=Gtk.ImageMenuItem(TEXT_FIND)
                    self.menu.append(menuitem)
                    menuitem.connect('activate', self.SERIE_find)
                    img = Gtk.Image(stock=Gtk.STOCK_DIALOG_WARNING)
                    menuitem.set_image(img)
                    
                menuitem=Gtk.ImageMenuItem(TEXT_DELETE)
                self.menu.append(menuitem)
                menuitem.connect('activate', self.SERIE_delete)
                img = Gtk.Image(stock=Gtk.STOCK_CANCEL)
                menuitem.set_image(img)
                
                self.menu.show_all()
                self.menu.popup(None, None, None, None, event.button, event.time)
                
                return True 


if __name__ == '__main__':

    GObject.threads_init()
    Gdk.threads_init()

    main=GUI()
    Gtk.main()

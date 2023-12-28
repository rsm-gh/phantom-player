#!/usr/bin/python3
#

#  Copyright (C) 2014-2015 Rafael Senties Martinelli.
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
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf, InterpType
import os
import csv
import shutil
import random
import magic

# local imports
from Paths import *



series_dictionary={}


magic_mimetype = magic.open(magic.MAGIC_MIME)
magic_mimetype.load()

def path_is_video(path, forgive_broken_links=False):
    if os.path.islink(path):
        if forgive_broken_links and not os.path.exists(os.path.realpath(path)):
            return True
        
        mimetype=magic_mimetype.file(os.path.realpath(path))
    else:
        mimetype=magic_mimetype.file(path)
    
    if 'video/' in mimetype:
        return True
        
    return False


def generate_list_from_videos_folder(dir_path, recursive):
        
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        if recursive:
            paths=[os.path.join(dp, filename) for dp, dn, filenames in os.walk(dir_path) for filename in filenames]
        else:
            paths=[os.path.join(dir_path, filename) for filename in os.listdir(dir_path)]

        return [path for path in sorted(paths) if path_is_video(path)]

    return []


class Serie(object):
    
    def __init__(self,  path, 
                        data_path, 
                        recursive, 
                        random, 
                        keep_playing, 
                        start_at=0,
                        audio_track=-2, 
                        subtitles_track=-2):
        
        self._path=path
        self._name=os.path.basename(path)
        
        self.set_recursive(recursive, False)            
        self.set_random(random, False)
        self.set_keep_playing(keep_playing, False)
        self.set_audio_track(audio_track, False)
        self.set_subtitles_track(subtitles_track, False)
        self.set_start_at(start_at, False)
                        
        # Variables
        self._videos_instances=[]
        self._nb_videos=0
        self._series_image_small_size=30
        self._series_image_big_size=160
        self._load_image()  
            
        # change the name of the serie in case it has been renamed.
        if data_path and os.path.exists(data_path):
            file_name=os.path.basename(data_path)
            if file_name[:-4] != self._name:
                self._name=file_name[:-4]
        
        
        if os.path.exists(SERIE_PATH.format(self._name)):
    
            """
                Get the number of rows of the file, this is important in case there be an error with the id's
            """
            number_of_rows=0
            if os.path.exists(SERIE_PATH.format(self._name)):
                with open(SERIE_PATH.format(self._name), mode='rt', encoding='utf-8') as f:
                    number_of_rows=len(f.readlines())
    

            """
                Load the videos (and their data) from the program files
            """
            with open(SERIE_PATH.format(self._name), mode='rt', encoding='utf-8') as f:
                rows=csv.reader(f,delimiter='|')
                next(f)
                for row in rows:
                    try:
                        path=row[1].strip()
                    except:
                        print("error getting the path")
                        path=False
                    
                    """
                        check for duplicates
                    """
                    if path and not any(path==video.get_path() for video in self._videos_instances) and path_is_video(path, True):
                        try:
                            id=int(row[0])
                        except:
                            print("error getting the id")
                            id=False
                            
                        if id:
                            
                            """
                                check if the Id has already been used
                            """
                            for video in self._videos_instances:
                                if id==video.get_id():
                                    #Send the video to the end
                                    number_of_rows+=1
                                    id=number_of_rows
                                    print("Incrementing duplicated id")
                            
                            try:
                                play=row[2]
                            except:
                                play='true'
                            
                            try:
                                o_played=row[3]
                            except:
                                o_played='false'
                            
                            try:
                                r_played=row[4]
                            except:
                                r_played='false'
                            
                            try:
                                position=float(row[5])
                            except:
                                position=0.0
                            
                            try:
                                display=row[6]
                            except:
                                display='true'
                            
                            
                            video=Video(path,id)
                            video.load_info(play,o_played,r_played,position,display)    
                            
                            self._videos_instances.append(video)
                            self._nb_videos+=1
    

        
        """
            Get the videos from the folder. This will find new videos.
        """
        for video_path in generate_list_from_videos_folder(self._path,self._recursive):
            if not any(video_path==video.get_path() for video in self._videos_instances):
                    
                self._nb_videos+=1
                new_video=Video(video_path,self._nb_videos)
                
                if os.path.exists(new_video.get_path()):
                    new_video.set_state_new()
                else:
                    # In case it is a broken link:
                    new_video.update_state()
                
                self._videos_instances.append(new_video)

                        
        self.clean_episodes()
        self.update_ids()   # this is in case there were videos with duplicated ids
        self._write_data()

        series_dictionary[self._name]=self


    def _write_data(self):
            
        if not os.path.exists(FOLDER_LIST_PATH):
             os.mkdir(FOLDER_LIST_PATH) 
        
        with open(SERIE_PATH.format(self._name), mode='wt', encoding='utf-8') as f:
            csv_list=csv.writer(f,delimiter='|')
            
            csv_list.writerow([ self._path,
                                self._recursive,
                                self._random,
                                self._keep_playing,
                                self._start_at,
                                self._audio_track,
                                self._subtitles_track,
                                ])
            
            
            for video in self._videos_instances:
                csv_list.writerow([ video.get_id(),
                                    video.get_path(),
                                    video.get_play(),
                                    video.get_o_played(),
                                    video.get_r_played(),
                                    video.get_position(),
                                    video.get_display(),
                                    ])


    def _load_image(self):
        """
            Set the default image
        """
        possible_image=self._path+'/.folder'.replace('//','/')
        if os.path.exists(possible_image):
            image_path=possible_image
        elif os.path.exists(possible_image+'.png'):
            image_path=possible_image+'.png'
        elif os.path.exists(possible_image+'.jpg'):
            image_path=possible_image+'.jpg'
        elif os.path.exists(possible_image+'.jpeg'):
            image_path=possible_image+'.jpeg'
        else:
            if os.path.exists(self._path):
                image_path=ICON_LOGO_MEDIUM
            else:
                image_path=ICON_ERROR_BIG
            
            
        self.pixbuf_small_video=Pixbuf.new_from_file_at_size(image_path,self._series_image_small_size,self._series_image_small_size)
        self.image_big=Gtk.Image.new_from_pixbuf(Pixbuf.new_from_file_at_size(image_path,self._series_image_big_size+60,self._series_image_big_size))


    def set_start_at(self, value, write=True):
        try:
            value=float(value)
        except Exception as e:
            print(self._name)
            print("set_start_at error:")
            print(str(e))
            value=0.0
        
        if value > 0:
            self._start_at=value
        else:
            self._start_at=0.0
        
        if write:
            self._write_data()
        
    def get_start_at(self):
        return self._start_at


    def find_serie(self, path):
        self._path=path
        self._load_image()
        self.find_videos(path)
        self.update_not_hiden_videos()
        self._write_data()

    def set_recursive(self, recursive, write=True):
        
        if recursive=='true' or recursive == 'True' or recursive == True:
            self._recursive=True
        else:
            self._recursive=False
        
        if write:
            self._write_data()
            
    def set_audio_track(self, value, write=True):
        try:
            value=int(value)
        except Exception as e:
            print(self._name)
            print("set_audio_track error:")
            print(str(e))
            value =-2
            
        if value == -1 or value >= 0:
            self._audio_track=value
        else:
            self._audio_track=-2
            
        if write:   
            self._write_data()
            
        
    def set_subtitles_track(self, value, write=True):
        try:
            value=int(value)
        except Exception as e:
            print(self._name)
            print("set_subtitles_track error:")
            print(str(e))
            value =-2
            
        if value == -1 or value >= 0:
            self._subtitles_track=value 
        else:
            self._subtitles_track=-2
        
        if write:
            self._write_data()
            

    def get_audio_track(self):
        return self._audio_track
        
    def get_subtitles_track(self):
        return self._subtitles_track

    def find_video(self, episode_name, new_path):
        """     
            Try to find videos other videos in case
            the name of a extension changed, or the start part
            of the episode.
            
            Ex 1:
                foo.ogg  -> foo
                faa.ogg  -> faa
            
                    or
                    
                videos-video700 -> video700
                videos-video800 -> video800

    Could this be more powerful and search other kind of sequence of strings?
            
            ex:
                video-VIDEO700 -> video-video700
                video-VIDEO800 -> video-video800
            
        """



        
        """
            change the path of the selected episode
        """
        for episode in self._videos_instances:
            if episode_name==episode.get_name():
                episode.set_path(new_path)
                break
                        
        # Find the pattern
        
        new_name=os.path.basename(new_path).strip()
        old_name=episode_name.strip()
        
        len_new_name=len(new_name)
        len_old_name=len(episode_name)
        
        found_videos=0
        if new_name in old_name or old_name in new_name:

            if len_new_name > len_old_name:
                patt=new_name.replace(old_name,'')
                
                # Check if there are other missing videos with the same pattern
                for video in self._videos_instances:
                    if not os.path.exists(video.get_path()):
                        video_name=video.get_name()
                        video_path=video.get_path()
                        basedir=os.path.dirname(video_path)+"/"
                        basedir.replace("//","/")
                        
                        if os.path.exists(basedir+patt+video_name):
                            video.set_path(basedir+patt+video_name)
                            found_videos+=1
                            
                        elif os.path.exists(video_path+patt):
                            video.set_path(video_path+patt)
                            found_videos+=1
            
            
            elif len_old_name > len_new_name:
                patt=old_name.replace(new_name,'')
                
                # Check if there are other missing videos with the same pattern
                for video in self._videos_instances:
                    if not os.path.exists(video.get_path()):
                        
                        possible_path=video.get_path().replace(patt,'')
                        
                        if os.path.exists(possible_path):
                            video.set_path(possible_path)
                            found_videos+=1
        
            
            self._write_data()
            
            if found_videos > 0:
                return found_videos
            else:
                return False
                
    def update_not_hiden_videos(self):
        self._nb_videos=len([0 for video in self._videos_instances if video.get_display()])
                
    def find_videos(self, path):
        
        path=path+'/'
        path.replace('//','/')
        
        video_counter=0
        for video in self._videos_instances:
            if not os.path.exists(video.get_path()):
                if os.path.exists(path+video.get_name()):
                    video_counter+=1
                    video.set_path(path+video.get_name())
                
                
        if video_counter > 0:
            self._write_data()
            
        return video_counter

            
    def ignore_video(self,del_video):
        """ Ignore a video from the serie by givin its name.
        """
    
        for video in self._videos_instances:
            if video.get_name()==del_video:
                
                if os.path.exists(video.get_path()):
                    video.set_display(False)
                else:
                    self._videos_instances.remove(video)
        
                self._nb_videos-=1
                self.update_ids()
                self._write_data()
                
                self.update_not_hiden_videos()
                
                break
                
    def dont_ignore_video(self,video_name):
        for video in self._videos_instances:
            if video.get_name()==video_name:

                video.set_display(True)

                self._nb_videos-=1
                self.update_ids()
                self._write_data()
                
                self.update_not_hiden_videos()
                
                break   
            

    def missing_videos(self,episodes_names):
        """Return if from the selected videos there is some one missing"""
        for episode_name in episodes_names:
            for episode in self._videos_instances:
                if episode.get_name()==episode_name:
                    if not os.path.exists(episode.get_path()):
                        return True
                    
        return False
        

    def clean_episodes(self):
        
        list=[]
        for video in self._videos_instances:
            if video and not os.path.exists(video.get_path()) and not video.get_display():
                '''Delete the hiden and unexisting videos'''
            else:
                list.append(video)
                
        self._videos_instances=list


    def get_path_from_video_name(self,name):
        for video in self._videos_instances:
            if video and video.get_name()==name:
                return video.get_path()
        
        return None

    def get_keep_playing(self):
        return self._keep_playing

    def set_keep_playing(self, value, write=True):
        
        if value=='true' or value == 'True' or value == True:
            self._keep_playing=True
        else:
            self._keep_playing=False
            
        if write:
            self._write_data()
            
        
    def get_random(self):
        return self._random
        
    def set_random(self, random, write=True):
        
        if random=='true' or random == 'True' or random == True:
            self._random=True
        else:
            self._random=False
        
        if write:
            self._write_data()

    def reorder(self, new_order_indexes):
        """ Choices are "up" or "down" """
        
        self._videos_instances=[self._videos_instances[i-1] for i in new_order_indexes]
        
        for i, video in enumerate(self._videos_instances, 1):
            video.set_id(i)
        
        self._write_data()


    def change_checkbox_state(self,episode_names,column,state):
        
        if isinstance(episode_names,str):
            episode_names=[episode_names]
        
        for episode_name in episode_names:
            for video in self._videos_instances:
                
                if video.get_name()==episode_name:

                    if column==4:
                        video.set_play(state)
                    elif column==5:
                        video.set_o_played(state)
                    elif column==6:
                        video.set_r_played(state)

                    break
        
        self._write_data()
        
        
    def mark_episode(self,episode,random,new_state):
        for video in self._videos_instances:
            if video==episode:
                if random: 
                    video.set_r_played(new_state)   
                else:
                    video.set_o_played(new_state)
        
                self._write_data()
                break       
        
    
    def reset_data(self):
        for video in self._videos_instances:
            video.set_play(True)
            video.set_o_played(False)
            video.set_r_played(False)
            video.set_position(0)
            
        self._write_data()
        
        
    def set_video_position(self,video_to_find,position):
        for video in self._videos_instances:
            if video_to_find==video:
                video.set_position(position)
                
                self._write_data()
                
                break
                        
    def update_ids(self):
        for i, video in enumerate(self._videos_instances, 1):
            video.set_id(i)
        
    def set_videos(self,list):
        self._videos_instances=list
    
    def set_name(self,new_name):
        self._name=new_name
        
    def rename(self,new_name):
        # update the data file
        if os.path.exists(SERIE_PATH.format(self._name)):
            os.rename(SERIE_PATH.format(self._name),SERIE_PATH.format(new_name))
        
        # update the class
        self._name=new_name
        
    def set_image(self,path):
        if os.path.exists(path):
            self.pixbuf_small_video=Pixbuf.new_from_file_at_size(path,self._series_image_small_size,self._series_image_small_size)
            self.image_big=Gtk.Image.new_from_pixbuf(Pixbuf.new_from_file_at_size(path,self._series_image_big_size+60,self._series_image_big_size))
            shutil.copy2(path,self._path+"/.folder")
            
    def get_image(self):
        return self.pixbuf_small_video
    
    def get_big_image(self):
        return self.image_big
    
    def get_name(self):
        return self._name

    def get_videos(self):
        return self._videos_instances
        
    def get_o_played_stats(self):
        """
            returns: played, total, percent
        """
        self.update_not_hiden_videos()
        
        i=0.00
        for video in self._videos_instances:
            if video.get_o_played() and video.get_display():
                i+=1.00
        
        if i > 0 and self._nb_videos > 0:
            return int(i),self._nb_videos,(i/self._nb_videos)
        else:
            return 0,self._nb_videos,0

    def get_r_played_stats(self):
        """
            returns: played,total,percent
        """
        self.update_not_hiden_videos()
        
        i=0.00
        for video in self._videos_instances:
            if video.get_r_played() and video.get_display():
                i+=1.00
        
        if i > 0 and self._nb_videos > 0:
            return int(i),self._nb_videos, (i/self._nb_videos)
        else:
            return 0,self._nb_videos,0

    def get_o_episode(self):
        for video in self._videos_instances:
            if not video.get_o_played() and video.get_play() and video.get_path() and video.get_display():
                return video
                
    def get_r_episode(self):
        for video in self._videos_instances:
            if not video.get_r_played() and video.get_play() and video.get_path() and video.get_display():
                while True:
                    random_ep=random.randint(0, self._nb_videos-1)
                    random_video=self._videos_instances[random_ep]
                    
                    if not random_video.get_r_played() and random_video.get_play() and random_video.get_path():
                        return random_video

        return False
                                    
    def get_nb_videos(self):
        return self._nb_videos
    
    def get_path(self):
        return self._path




class Video(object):
    
    def __init__(self,path,id):
        
        self.set_id(id)
        
        try:
            self._name=os.path.basename(path)
            self._dir_path=os.path.dirname(path)
            
            self.empty_name, self.extension = os.path.splitext(self._name)
            
            if len(self.extension) > 4: # it is probably not an extension..
                self.empty_name=self.empty_name+self.extension
                self.extension=''
            
        except Exception as e:
            print("wrong path")
            self._name='None'
            self._dir_path='None'
    
        self._path=path 
        self._play=True
        self._o_played=False
        self._r_played=False
        self._position=0
        self._display=True

        self.update_state()

    def update_state(self):
        if os.path.exists(self._path):
            self._state=Gtk.STOCK_APPLY
        else:
            self._state=Gtk.STOCK_DIALOG_WARNING
    
    def load_info(self,play,o_played,r_played,position,display):
    
        if play.strip().lower() =='false':
            self.set_play(False)
            
        if o_played.strip().lower() == 'true':
            self.set_o_played(True)
            
        if r_played.strip().lower() == 'true':
            self.set_r_played(True)
            
        if position > 0:
            self.set_position(position)
            
        if display.strip().lower() != 'true':
            self.set_display(False)

    def get_extension(self):
        return self.extension

    def get_empty_name(self):
        return self.empty_name
        
    def set_path(self,path):
        self._path=path
        self._name=os.path.basename(path)
        self.update_state()
        
    def set_state_new(self):
        self._state=Gtk.STOCK_ADD
        
    def set_state(self, pixbuf):
        self._state=pixbuf
    
    def get_position(self):
        return self._position
        
    def set_position(self,pos):
        if pos < 1 and pos >= 0:
            self._position=pos
        else:
            print(self._name,"wrong set_position")
            
    def get_display(self):
        return self._display
        
    def set_display(self,bool):
        self._display=bool
    
    def get_path(self):
        return self._path
            
    def get_name(self):
        return self._name
        
    def get_state(self):
        return self._state
        
    def get_play(self):
        return self._play
        
    def get_o_played(self):
        return self._o_played

    def get_r_played(self):
        return self._r_played
        
    def set_r_played(self,bool):
        self._r_played=bool
        
    def set_o_played(self,bool):
        self._o_played=bool
        
    def set_play(self,bool):
        self._play=bool
        
    def set_id(self,integer):
        if int(integer) < 0:
            print("video id error "+self._name)
        else:
            self.id=int(integer)
        
    def get_id(self):
        return self.id



if __name__ == '__main__':

    for video in generate_list_from_videos_folder('/home/public/videos/', True):
        print(video)

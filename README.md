![root window](https://github.com/rsm-gh/vlist-player/raw/master/root_window.png)

[player image missing]

GNU/Linux Video list player. Make lists of videos (tv, series, movies) and play them in order, random, etc..


## Installation

The software doesn't needs to be installed to used, if the dependencies are satisfied, you can simply launch vListPlayer.py. Anyways if you wish to install it, just execute the 'setup' file as root.


## Interested by the Python-VLC player ?

 - The graphical interphase that vlist-player is using to play videos is made with pyVLC, Python3 and GTK+. 
 If you are interested about this or you want to use it for your own project, you can copy the following files in to
a folder:
```
    /usr/share/vlist-player/vlc.py              # pyVLC
    /usr/share/vlist-player/MediaPlayer.py      # Graphical Interphase
    
    /usr/share/vlist-player/Texts.py            # Neded by CustomGtk.py, It sets the english texts
    /usr/share/vlist-player/Paths.py            # Neded by CustomGtk.py, It probably sets the starting path
```
 It is easy to the remove the dependencies: Texts.py, Paths.py , In reallity the only important files are the fist two that I mentioned.
 
 
 - How to use MediaPlayer.py?
 
    + The really easy way:
        Open the file, and go to the bottom, you will see:
        
            `player.play_video('/home/public/videos/English/Movies/Kill Bill II')`
   
   
        Just replace the path with the video you need and launch the script.
        
        
    + The full way:
        
        MediaPlayer.py was created to be controlled from another script/class/object. If you want to understand how I 
        do it just take a look to vListPlayer.py.
        
            `When doing: self.media_player = MediaPlayer()`
        
        I create a new instance, and then I'm able to use it with methods like: play_video, get_state(), hide(), etc.
   

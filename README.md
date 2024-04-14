
> **NOTE: THE PLAYER IS CURRENTLY UNDER DEVELOPMENT. The first stable version is not yet released**


![Player Window](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/preview.png)  
<sub><sup>*The Desktop theme defines the look and the icons of the player.</sup></sub>

**Phantom Player** is conceived to reproduce and organize lists of videos from a hard-drive,
and it will be particularly useful if you're still downloading torrents.

Some of its major features are:

+ Play lists of videos in order or randomly (without repeating videos).
+ Remember the last played playlist, and the videos progress.
+ Organize the play order.
+ Hide videos or files.
+ Automatically discover new videos.
+ Set a start/end time to skip the introduction/credits.
+ Set the default audio/subtitle track.
+ Turn off the screensaver while playing.
+ Keep playing mode.
+ Fullscreen mode.

**When organizing the playlists and videos, the software will never modify 
any of the hard-drive content.*

## How to Install

1. Download the [stable branch](https://github.com/rsm-gh/phantom-player/archive/master.zip).
2. Install the dependencies:
    * Debian based distributions: `apt-get install python3 python3-vlc python3-pil libgtk-3-0 gir1.2-webkit2-3.0`.
    * ArchLinux: `pacman -Suy python python-pillow python-magic webkit2gtk` and from AUR `python-vlc`.

3. Execute the setup file.

**If the dependencies are satisfied, the software can be directly executed, the installation is not mandatory.*  
***When the stable version is released, there will be some packages for popular distributions & windows.* 

## Controls

### Playlist List
+ Select a playlist with single left-click.
+ Start playing a playlist with a double left-click.
+ Open the playlist settings with a right-click.

### Videos List
+ Play a video with a double left-click.
+ Open the video's menu with a right-click.
+ Order the videos with drag and drop.

### Media Player
+ Turn to fullscreen with the F11 key or with the button from the media player.
+ Turn off the fullscreen with the Esc key or with the button from the media player.
+ Change the volume with the mouse wheel or the up/down arrows**.
+ Toggle Play/Pause with a left-click**, the space bar** or the enter key**.
+ Change the subtitles or the audio track with the button from the media player.
+ Resize the player by grabbing the separator with and moving it up or down.

**The media player controls only work if a video is loaded.*  
***Only in fullscreen mode.*  

## Extra
### Find missing Videos

When a video is missing, the text will be displayed in red*, 
you can then find it by using `right-click menu > find`.

There are two different method functions that you can use to perform this action:

A) By selecting a single row:
	
You will be asked to select a file, and the player will try to find the rest of the 
missing videos in the same directory.

This will work even if some files are renamed with easy patterns, for example:

```
foo-700 -> lol-700
foo-701 -> lol-701

700-faa -> 700.fifu
701-faa -> 701.fifu

foo-700 -> 700
foo-700 -> 701
```
				
B) By selecting multiple rows:
	
You will be asked to select a directory, and the player will try to find all the missing videos 
by matching their exact name.

**The font-colors depend on your Desktop theme.*

### Development documentation

Please check `/usr/share/doc/phantom-player`.


![Player Window](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/preview.png)  
**Your Desktop theme will define the icons and look of the player.*

**Phantom Player** is a Media Player that allows organizing and reproducing lists of videos with comfort.
It gives the feeling of having a streaming platform with the content of a hard drive.

Some of its major features are:
+ Play lists of videos in order or randomly (without repeating videos).
+ Organize the play order (without affecting the data on your hard drive).
+ Hide videos or files (without affecting the data on your hard drive).
+ Automatically discover new videos.
+ Start playing lists & videos where you left off.
+ Set a default time to skip the intro of videos (handy for the playlist intro).
+ Set the default audio or subtitle track.
+ Turn off the screensaver while playing.
+ Keep playing mode.
+ Fullscreen mode.

*Note: This software is great for reproducing lists of videos that have been downloaded 
from torrents. It allows hiding the unnecessary stuff, having multiple sources, keep seeding, 
discover new downloaded videos, and reproduce everything with comfort !*

## How to Install

1. Download the [stable branch](https://github.com/rsm-gh/phantom-player/archive/master.zip).
2. Install the dependencies:
    * Debian based distributions: `apt-get install python3 python3-vlc libgtk-3-0 gir1.2-webkit2-3.0`.
    * ArchLinux: `pacman -Suy python python-vlc gtk3`.

3. Execute the setup file.

**If the dependencies are satisfied, the software can be directly launched, the installation is not mandatory.*  
***Currently I'm working to create the version 2.0. When I finish, I'll create some packages for popular distributions & windows.*  

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
+ Toggle Pause/Play with a left-click or the space bar**.
+ Change the subtitles or the audio track with the button from the media player.

***Only in fullscreen mode.*  
**The media player controls only work if a video is loaded.*  

## Extra
### Searching missing Videos

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
	
You will be asked to select a directory, and the player will try to find the missing videos 
by matching their exact name.

**The font-colors depend on your Desktop theme.*

### Location of the program files
+ Configuration File: `~/.config/phantom-player.ini`
+ Playlist Files: `~/.local/share/phantom-player/<playlist name>.csv`

### Playlist files

Each playlist is stored in a CSV file that uses a "|" as separator. 

The first line will contain the playlist properties:
```
Random | Keep Playing | Start At | Audio Track | Subtitles Track
```
Then, the playlist paths will be listed as:
```
Path | Recursive
```
And finally, there will be one line per video:
```
Number | Absolute Path | Play | O-Played | R-Played | Position | Ignore
```
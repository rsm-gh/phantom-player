![Playlists Window](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/preview-playlists.png)  
![Videos Window](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/preview-videos.png)  
<sub><sup>*The Desktop theme defines the look and the icons of the player.</sup></sub>

**Phantom Player** is conceived to reproduce and organize lists of videos from a hard-drive.  

Some of its major features are:
+ Play lists of videos in order or randomly (without repeating videos).
+ Remember the last played playlist, and the videos progress.
+ Organize the play order.
+ Hide videos or files.
+ Automatically discover new/renamed/moved videos.
+ Set a start/end time to skip the introduction/credits.
+ Set the default audio/subtitle track.
+ Turn off the screensaver while playing.
+ Keep playing mode.
+ Rename videos.
+ and more...


### Reproducing videos directly form the hard-drive.
It is possible to simply play a video directly from the hard-drive:
1) With the desktop interface `right-click > open with > Phantom-Player`
2) With a command `phantom-player --open-file='/path/to/file'`

*If the video is in a playlist, the playlist will be selected.

### Reproducing videos from torrents
When it comes to torrents, the most important is to do not modify the data
in order to continue seeding.  

With this software you can:
+ Add a parent directory and create a recursive playlist.
+ Add multiple directories to a play list.

And the software will filter only the fully downloaded video files,
display them nicely in the interface, and give you a streaming platform feeling.   

Also, if there are multiple seasons, or you have many episodes to download,
it will automatically discover the new videos.

### Organizing videos of a hard-drive
The software is great for organizing data from a hard-drive.  

For example, you can add the root directory of the hard-drive as a playlist path, and set it as recursive. 
The software will then scan the whole hard-drive and create a playlist with all the videos.
This will allow you to:
+ Identify all the videos (and their paths).
+ Identify the duplicated videos.
+ Rename the videos.

## How to Install

> **NOTE: THE PLAYER IS CURRENTLY UNDER DEVELOPMENT,
> and the first stable version is not yet released** [more info](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/DevNotes.md).

1. Download the [stable branch](https://github.com/rsm-gh/phantom-player/archive/master.zip).
2. Install the dependencies:
    * Debian based distributions: `apt-get install python3 python3-vlc python3-pil libgtk-3-0 gir1.2-webkit2-3.0`.
    * ArchLinux: `pacman -Suy python python-pillow python-magic webkit2gtk` and from AUR `python-vlc`.

3. Execute the setup file.

**If the dependencies are satisfied, the software can be directly executed, the installation is not mandatory.*  
***When the stable version be released, there will be some packages for popular distributions & windows.* 

## User Manual

The user manual is in progress. For the moment, here you can find some details 
about the controls & behaviour.

### Playlists menu
+ Select a playlist with a single left-click.

+ Keyboard shortcuts:
  + `ctrl+o` to open a file.
  + `ctrl+a` display the about dialog.
  + `ctrl+f` find/filter playlists by name.
  + `ctrl+h` hide/display missing playlists.
  + `ctrl+n` create a new playlist.

### Videos menu
+ Play a video with a double left-click.
+ Open a video's menu with a right-click.
+ Order the videos with drag and drop.
+ Modify the columns to display, by doing a middle-click in the videos-list header.
+ Resize the player by grabbing the separator with and moving it up or down.
+ Keyboard shortcuts:
  + `back` to return to the playlists' menu.
  + `ctrl+s` open the settings menu.
  + `ctrl+u` mark video as un-viewed (0% progress).
  + `ctrl+v` mark video as viewed (100% progress).
  + `ctrl+d` delete videos.
  + `ctrl+h` hide/show missing videos.
  + `ctrl+i` ignore/un-ignore videos.
  + `ctrl+o` open the video location.
  + `ctrl+r` rename videos.

#### Media Player
+ Controls:
    + Change the volume with the mouse wheel.
  + Fullscreen only:
      + Toggle Play/Pause with a left-click.

+ Keyboard shortcuts:
  + `F11` to set fullscreen. 
  + Fullscreen only:
    + `Esc` to quit fullscreen. 
    + `up/down arrows` to change the volume.
    + `space bar` or `enter key` to toggle play/pause.

**The media player controls only work if a video is loaded.*

## Extra

+ All paths (and video names) containing the pipe "|" character will be excluded from the software.
+ If a video has a "*.srt" file with the same name and same location, it will be used as default subtitles.
+ "*.part" files will always be excluded since they break the hashing system.
+ It is not possible to remove videos while the playlist is loading/discovering videos.
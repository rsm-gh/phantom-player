![Playlists Window](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/preview-playlists.png)  
![Videos Window](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/preview-videos.png)  
<sub><sup>*The Desktop theme defines the look and the icons of the player.</sup></sub>

**Phantom Player** is conceived to reproduce and organize lists of videos from a hard-drive. Some of its major features are:
+ Play lists of videos in order or randomly (without repeating videos).
+ Remember the last played playlist, and the videos progress.
+ Organize the play order.
+ Hide videos or files.
+ Automatically discover new/renamed videos.
+ Set a start/end time to skip the introduction/credits.
+ Set the default audio/subtitle track.
+ Turn off the screensaver while playing.
+ Keep playing mode.
+ and more...

Beside the media playing, this software will be particularly useful for:
+ Reproducing videos that are coming from torrents.
+ Discover the videos from a hard-drive and organize them.


> **NOTE: THE PLAYER IS CURRENTLY UNDER DEVELOPMENT,
> and the first stable version is not yet released.**  
> The remaining work can be read [here](https://github.com/rsm-gh/phantom-player/blob/master/usr/share/doc/phantom-player/DevNotes.md).

## How to Install

1. Download the [stable branch](https://github.com/rsm-gh/phantom-player/archive/master.zip).
2. Install the dependencies:
    * Debian based distributions: `apt-get install python3 python3-vlc python3-pil libgtk-3-0 gir1.2-webkit2-3.0`.
    * ArchLinux: `pacman -Suy python python-pillow python-magic webkit2gtk` and from AUR `python-vlc`.

3. Execute the setup file.

**If the dependencies are satisfied, the software can be directly executed, the installation is not mandatory.*  
***When the stable version is released, there will be some packages for popular distributions & windows.* 

## Controls

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

+ All paths (and video names) containing the pipe "|" character will be excluded from the software.
+ If a video has a "*.srt" file with the same name and same location, it will be used as default subtitles.
+ "*.part" files will always be excluded since they break the hashing system.
+ It is not possible to remove videos while the playlist is loading/discovering videos.

### Development documentation

Please check `/usr/share/doc/phantom-player`.

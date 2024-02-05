
![Player Window](https://github.com/rsm-gh/vlist-player/blob/master/usr/share/doc/vlist-player/preview.png)

`vlist-player` is a software to play lists of videos with comfort, some of its major features are:
+ Play lists of videos in order or randomly (without repeating episodes).
+ Keep playing mode.
+ Start playing videos where you left off.
+ Automatically discover new videos.
+ Organize the play order (without affecting the data on your hard drive).
+ Hide/Skip some videos or files (without affecting the data on your hard drive).
+ Turn off the screensaver while playing.
+ Set a default time to skip the intro of videos (handy for the series intro).
+ Set the default audio or subtitle track.
+ Fullscreen mode.

## How to Install

1. Download the [stable branch](https://github.com/rsm-gh/vlist-player/archive/master.zip).
2. Install the dependencies:
    * Debian based distributions: `apt-get install python3 python3-vlc libgtk-3-0 gir1.2-webkit2-3.0`.
    * ArchLinux: `pacman -Suy python python-vlc gtk3`.

3. Execute the setup file.

**Currently I'm working to create the version 2.0. When I finish, I'll create some packages for popular distributions & windows.*  
***If the dependencies are satisfied, the software can be directly launched, the installation is not mandatory.*

## Controls

### Series List
+ Select a series with single left-click.
+ Start playing a series with a double left-click.
+ Open the series menu with a right-click.

### Episodes List
+ Play an episode with a double left-click.
+ Open the episode's menu with a right-click.
+ Order the episodes with drag and drop.
+ Check the play columns to select if an episode should be play / play in order mode / play in random mode.

### Media Player
+ Toggle the fullscreen with a double left-click, or use the esc key to quit**.
+ Change the volume with the mouse wheel or the up/down arrows**.
+ Toggle Pause/Play with a left-click or the space bar**.
+ Change the subtitles or the audio track from the right-click menu.

**The media player controls will only work if a video is loaded.*  
***Only in fullscreen mode.*

## Extra
### Searching missing Episodes

When an episode is missing, an error icon will appear, you can then find files by using `right-click menu > find`.

There are two different find functions that you can use:

A) When you select a single file:
	
You will be asked to find a file, and once you have selected it, the vlist-player will try to find the rest of the missing episodes in the same folder.
This will work even if you have renamed the files with some easy patterns at the begging or the end of the file names. Examples:

```
foo-700 -> lol-700
foo-701 -> lol-701

700-faa -> 700.fifu
701-faa -> 701.fifu

foo-700 -> 700
foo-700 -> 701
```
				
B) When you select multiple files:
	
You will be asked to select a directory, and once you select it will try to find the missing episodes by mathing their name. If the names have modifications, it won't find them.

### Location of the program files
+ Configuration File: `~/.config/vlist-player.ini`
+ Series Files: `~/.local/share/vlist-player/<series name>.csv`

### Series files

They use the CSV format with a "|" as separator. If some of the files that you want to add have this character, they will be rejected.

The first line will contain:
```
Absolute Path | Recursive | Random | Keep Playing | Start At | Audio Track | Subtitles Track
```
Then each episode will be added in a separate line:
```
Number | Absolute Path | Play | O-Played | R-Played | Position | Hide
```
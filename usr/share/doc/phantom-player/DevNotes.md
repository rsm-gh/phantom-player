

## Phantom-Player

### Remaining Work:
+ Manage multiple paths into the playlist settings menu.
+ Apply the "load video/discover" methods of the settings dialog into a thread.
+ Finish the option "end at"
+ Discover videos in the background, once all the series are loaded? To speed up the startup.
+ Settings dialog, paths, display how may valid videos, how many missing videos in the liststore.

### Bugs:
+ When searching in the playlist liststore, empty the videos if no playlist is selected.
+ Problems saving the Path settings?
+ When selecting multiple videos to re-order with drag-and-drop, only the fist one is moved.

### Features to add:
+ Create the "delete video" option (instead of clean)
+ Create a dialog to rename videos.
+ Create a dialog to find videos?
+ Add a 'still there?' dialog, based on time? episodes nb? activity? time of the day?
+ Hash videos to simplify the finding?

## MediaPlayerWidget

### Remaining Work:
+ `set_video(play=False)` currently does nothing, but it should set a video and load a frame image without starting to play it.
+ `player.set_track()` returns a status. It would be good to read the status and display a message in case of error.
+ Start/Stop the thread `__on_thread_player_activity` depending on the VLC status?

### Features to add:
+ When the media changes, display a label. I think it can be done with the VLC API.
+ When using the +/- signs of the volume button, only change of 1.

### Bugs:
+ Test/Fix (when cancel) the option to choose the subtitles' file...
+ Fixes to the menu of the subtitles & audio tracks?
+ Sometimes when clicking very fast the progress scale, the video position is not modified. Despite multiple ways of trying to fix this, I haven't found a solution.
+ It is necessary to connect the Scale of the Volume button, to avoid hiding the GUI when pressed.
    I haven't found a solution for this, because the press signals connect to the button and not the scale.
+ VolumeButton: it should get hidden when clicking out of the button. Is this a problem of GTK?

### Patches:

+ Patch 001: `media.get_duration()` is not correctly parsed if the video was not played. This is strange, 
  because the VLC API says that `parse()` is synchronous, and it should work.  
    To fix it, all the properties depending on the media duration are loaded in `self.__on_thread_player_activity()`

+ Patch 002: `self.__vlc_widget.player.get_media()` is always returning `None`. Why?  
    To fix it, I created `self.__media`.


### Remarks:

Please read the patches before reading this section.

+ The player uses `set_position()` instead of `set_time()` because the VLC API says that `time` is not supported for all the formats. This makes the code more complex, but it works well. Some remarks are:
    + Saving/Applying the position is pretty easy.
    + `start_at`, `end_at`, and `end_position` are more complex because they depend on the media duration:
        + `start_at` and `end_at` must be saved in `time` format, because it is an input given by the user and, it must be a constant across all media.
        + `end_position` is used to detect when a video has ended. Normally it should be `1`,
           but the value may change based on a numeric approach. For example, for a very long video, it may be `.9999999`, and for a shorter `.9`.

### To investigate
+ Is it possible to remove the thread `on_thread_player_activity` and replaced by VLC signals?
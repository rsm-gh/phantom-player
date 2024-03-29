
### Location of the program files
+ Configuration File: `~/.config/phantom-player.ini`
+ Playlist Files: `~/.local/share/phantom-player/<playlist name>.csv`

### Playlist files

Each playlist is stored in a CSV file that uses a "|" as separator. 

The first line will contain the playlist properties:
```
Random (Boolean) | Keep Playing (Boolean) | Start At (Integer) | Audio Track (Integer) | Subtitles Track (Integer) | Icon Extension (String) | Last Played Video Hash (String)
```
Then, the playlist paths will be listed as:
```
Path (System Path) | Recursive (Boolean) | Startup Discover (Boolean)
```
And finally, there will be one line per video:
```
Absolute Path (System Path) | Name (String) | Position (Double) | Ignore (Boolean)
```
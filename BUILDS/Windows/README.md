
## Run

To run the software on Windows:

1) Install [MSYS2](https://www.msys2.org/).
2) Install VLC x64 at `C:\Program Files\VideoLan`.
2) From an MSYS console install:
```
pacman -S mingw-w64-ucrt-x86_64-gtk3 \
          mingw-w64-ucrt-x86_64-python \
          mingw-w64-ucrt-x86_64-python-pip \
          mingw-w64-ucrt-x86_64-python-gobject \
          mingw-w64-ucrt-x86_64-python-pillow \
          mingw-w64-ucrt-x86_64-file
```
3) From an MSYS UCRT64 console install:
```
python -m pip install python-vlc python-magic PyGObject-stubs
```

4) From an MSYS UCRT64 console run `main.py`


## Build

1) Install VLC (x64), the installation directory should be `C:\Program Files\VideoLAN`.
2) From an MSYS UCRT64 console compile the software by using PyInstaller with `decompressed.spec`.
3) Generate an installer with [InstallForge](https://installforge.net/).


### Post-Install script

It is necessary to execute: `".\VLC\vlc-cache-gen.exe" .\VLC\plugins` to fix the following error:

```
[000002687265e9f0] main libvlc error: stale plugins cache: modified \PhantomPlayer\_internal\VLC\plugins\video_filter\libtransform_plugin.dll
[000002687265e9f0] main libvlc error: stale plugins cache: modified \PhantomPlayer\_internal\VLC\plugins\video_filter\libvhs_plugin.dll
etc...
```

It is important to fix this error, because it will also slow down the startup.


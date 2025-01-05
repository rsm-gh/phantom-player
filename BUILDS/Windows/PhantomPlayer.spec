# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    [r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\test\MediaPlayer.py"],
    pathex=[
	r"C:\msys64\ucrt64\bin", 
	r"C:\msys64\ucrt64\lib\python3.11\site-packages"
    ],
    binaries=[],
    datas=[
	(r"C:\msys64\ucrt64\bin\libvlc.dll","."),
        (r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\console_printer.py","."),
        (r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\system_utils.py","."),
	(r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\vlc_utils.py","."),
	(r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\Texts.py","."),
        (r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\Paths.py","."),
        (r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\settings.py","."),
	(r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\model\Video.py","model"),	        
	(r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\model\Playlist.py","model"),
        (r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\model\PlaylistPath.py","model"),
        (r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\view\gtk_utils.py","view"),
	(r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\view\GtkVlc.py","view"),
        (r"C:\Users\rafae\Desktop\phantom-player\usr\share\phantom-player\view\GtkPlayer.py","view"),
    ],
    hiddenimports=["PIL","PIL.Image","cairo","vlc"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhantomPlayer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhantomPlayer',
)

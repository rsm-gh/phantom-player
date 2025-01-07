# -*- mode: python ; coding: utf-8 -*-

import os

_SPEC_ROOT = os.path.abspath(SPECPATH)
_SRC = os.path.dirname(os.path.dirname(_SPEC_ROOT))

_UCRT=r"C:\msys64\ucrt64"
_UCRT_BIN=os.path.join(_UCRT, "bin")

a = Analysis([os.path.join(_SRC, r"usr\share\phantom-player\main.py")],
    pathex=[
	    _UCRT_BIN,
        os.path.join(_SRC, r"usr\share\phantom-player"),
    ],
    binaries=[],
    datas=[
        (os.path.join(_UCRT, r"lib\python3.11\site-packages\magic"), "magic"),
        (_UCRT_BIN, "."),
        (os.path.join(_UCRT_BIN, "libvlc.dll"), "."),
        (os.path.join(_UCRT_BIN, "libmagic-1.dll"), "."),
        (os.path.join(_SRC, r"usr\share\phantom-player\view\main-window.glade"), "view"),
        (os.path.join(_SRC, r"usr\share\phantom-player\view\settings-window.glade"), "view"),
        (os.path.join(_SRC, r"usr\share\phantom-player\view\single-rename.glade"), "view"),
        (os.path.join(_SRC, r"usr\share\phantom-player\view\img\movie-icon-big.png"), "view\img"),
        (os.path.join(_SRC, r"usr\share\phantom-player\view\img\movie-icon-medium.png"), "view\img"),
        (os.path.join(_SRC, r"usr\share\phantom-player\view\img\movie-icon-small.png"), "view\img"),
    ],
    hiddenimports=[],
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

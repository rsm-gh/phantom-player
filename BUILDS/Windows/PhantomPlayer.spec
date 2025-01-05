# -*- mode: python ; coding: utf-8 -*-

#
# MIT License
#
# Copyright (c) 2025 Rafael Senties Martinelli.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os

_SPEC_ROOT = os.path.abspath(SPECPATH)
_SRC = os.path.dirname(os.path.dirname(_SPEC_ROOT))
_UCRT_BIN=r"C:\msys64\ucrt64\bin"

a = Analysis([os.path.join(_SRC, r"usr\share\phantom-player\main.py")],
    pathex=[
	    _UCRT_BIN,
        os.path.join(_SRC, r"usr\share\phantom-player"),
    ],
    binaries=[],
    datas=[
        (os.path.join(_UCRT_BIN, "libvlc.dll"), "."),
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

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['GUI/app.py'],
    pathex=['.','E:/Application_miniconda3/envs/only_install_ui/Lib/site-packages'],
    binaries=[],
    datas=[
        ('RESOURCE/IMAGE/*.png', 'RESOURCE/IMAGE'),
        ('RESOURCE/SCRIPTS/*.tcl', 'RESOURCE/SCRIPTS'),
    ],
    hiddenimports=['serial'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='eda_tools_ui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='eda_tools_ui'
)
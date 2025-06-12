a = Analysis(
    ['CLI/vccm_cli.py'], 
    pathex=['.'],
    binaries=[],
    datas=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=None,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='bit_tool',  # 输出文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='bit_tool'
)

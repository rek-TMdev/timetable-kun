# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path.cwd()
APP_DIR = ROOT / "src" / "app"
ICON_DIR = ROOT / "assets" / "icons"

a_main = Analysis(
    [str(APP_DIR / "time_manager_main.py")],
    pathex=[str(APP_DIR)],
    binaries=[],
    datas=[
        (str(ICON_DIR / "時間割くんアイコン.ico"), "."),
        (str(APP_DIR / "svgs"), "svgs"),
    ],
    hiddenimports=[
        "PySide6.QtSvg",
        "PySide6.QtCore",
        "PySide6.QtWidgets",
        "PySide6.QtGui",
        "darkdetect",
        "openpyxl",
        "tutorial_manager",
        "config_manager",
        "theme_manager",
        "file_io_manager",
        "profile_manager",
        "timetable_worker",
        "timetable_logic",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_main = PYZ(a_main.pure)
exe_main = EXE(
    pyz_main,
    a_main.scripts,
    [],
    exclude_binaries=True,
    name="TimeManager",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ICON_DIR / "時間割くんアイコン.ico"),
)

a_splash = Analysis(
    [str(APP_DIR / "time_manager_launcher.py")],
    pathex=[str(APP_DIR)],
    binaries=[],
    datas=[
        (str(ICON_DIR / "時間割くんアイコン起動中.ico"), "."),
    ],
    hiddenimports=["PySide6.QtCore", "PySide6.QtWidgets", "PySide6.QtGui"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz_splash = PYZ(a_splash.pure)
exe_splash = EXE(
    pyz_splash,
    a_splash.scripts,
    [],
    exclude_binaries=True,
    name="時間割くん-v1.0.5",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(ICON_DIR / "時間割くんアイコン.ico"),
)

coll = COLLECT(
    exe_main,
    a_main.binaries,
    a_main.zipfiles,
    a_main.datas,
    exe_splash,
    a_splash.binaries,
    a_splash.zipfiles,
    a_splash.datas,
    strip=False,
    upx=True,
    upx_strip=False,
    name="時間割くん",
)

# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

ROOT = Path.cwd()
DRIVER_DIR = ROOT / "src" / "driver"
CHECKER_DIR = ROOT / "src" / "checker"
ICON_DIR = ROOT / "assets" / "icons"
SVGS_DIR = ROOT / "src" / "app" / "svgs"

a_drv_main = Analysis(
    [str(DRIVER_DIR / "config_editor_main.py")],
    pathex=[str(DRIVER_DIR)],
    datas=[
        (str(ICON_DIR / "時間割くんドライバアイコン.ico"), "."),
        (str(SVGS_DIR), "svgs"),
    ],
    hiddenimports=[
        "PySide6.QtSvg",
        "darkdetect",
        "pykakasi",
        "openpyxl",
        "deep_translator",
        "tkinter",
        "hashlib",
        "copy",
    ],
    noarchive=False,
)
pyz_drv_main = PYZ(a_drv_main.pure)
exe_drv_main = EXE(
    pyz_drv_main,
    a_drv_main.scripts,
    [],
    exclude_binaries=True,
    name="ConfigEditor",
    console=False,
    icon=str(ICON_DIR / "時間割くんドライバアイコン.ico"),
)

a_drv_launcher = Analysis(
    [str(DRIVER_DIR / "config_editor_launcher.py")],
    pathex=[str(DRIVER_DIR)],
    datas=[
        (str(ICON_DIR / "時間割くんドライバアイコン起動中.ico"), "."),
    ],
    hiddenimports=["PySide6.QtCore", "subprocess", "pathlib"],
    noarchive=False,
)
pyz_drv_launcher = PYZ(a_drv_launcher.pure)
exe_drv_launcher = EXE(
    pyz_drv_launcher,
    a_drv_launcher.scripts,
    [],
    exclude_binaries=True,
    name="時間割くんドライバ-v3.0",
    console=False,
    icon=str(ICON_DIR / "時間割くんドライバアイコン.ico"),
)

a_chk_main = Analysis(
    [str(CHECKER_DIR / "timetable_checker_main.py")],
    pathex=[str(CHECKER_DIR)],
    datas=[
        (str(ICON_DIR / "時間割くんチェッカーアイコン.ico"), "."),
    ],
    hiddenimports=["PySide6.QtSvg", "darkdetect", "openpyxl", "concurrent.futures", "shutil", "tkinter"],
    noarchive=False,
)
pyz_chk_main = PYZ(a_chk_main.pure)
exe_chk_main = EXE(
    pyz_chk_main,
    a_chk_main.scripts,
    [],
    exclude_binaries=True,
    name="TimetableChecker",
    console=False,
    icon=str(ICON_DIR / "時間割くんチェッカーアイコン.ico"),
)

a_chk_launcher = Analysis(
    [str(CHECKER_DIR / "timetable_checker_launcher.py")],
    pathex=[str(CHECKER_DIR)],
    datas=[
        (str(ICON_DIR / "時間割くんチェッカーアイコン起動中.png"), "."),
    ],
    hiddenimports=["PySide6.QtCore", "subprocess", "pathlib"],
    noarchive=False,
)
pyz_chk_launcher = PYZ(a_chk_launcher.pure)
exe_chk_launcher = EXE(
    pyz_chk_launcher,
    a_chk_launcher.scripts,
    [],
    exclude_binaries=True,
    name="時間割くんチェッカー-v1.4",
    debug=False,
    console=False,
    icon=str(ICON_DIR / "時間割くんチェッカーアイコン.ico"),
)

coll = COLLECT(
    exe_drv_main,
    a_drv_main.binaries,
    a_drv_main.zipfiles,
    a_drv_main.datas,
    exe_drv_launcher,
    a_drv_launcher.binaries,
    a_drv_launcher.zipfiles,
    a_drv_launcher.datas,
    exe_chk_main,
    a_chk_main.binaries,
    a_chk_main.zipfiles,
    a_chk_main.datas,
    exe_chk_launcher,
    a_chk_launcher.binaries,
    a_chk_launcher.zipfiles,
    a_chk_launcher.datas,
    strip=False,
    upx=True,
    upx_strip=False,
    name="時間割くんツール",
)

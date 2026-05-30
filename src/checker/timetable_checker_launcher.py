"""
timetable_checker_launcher.py - Timetable Checkerランチャー

スプラッシュスクリーンを表示し、TimetableCheckerメインアプリケーションを起動します。
"""
from launcher_utils import LauncherConfig, run_launcher


def main():
    """Timetable Checkerランチャーのエントリーポイント"""
    config = LauncherConfig(
        ipc_ready_filename="timetablechecker_ready.tmp",
        main_app_name="TimetableChecker.exe",
        splash_image_filename="時間割くんチェッカーアイコン起動中.png"
    )
    return run_launcher(config)


if __name__ == '__main__':
    main()
"""
config_editor_launcher.py - Config Editorランチャー

スプラッシュスクリーンを表示し、ConfigEditorメインアプリケーションを起動します。
"""
from launcher_utils import LauncherConfig, run_launcher


def main():
    """Config Editorランチャーのエントリーポイント"""
    config = LauncherConfig(
        ipc_ready_filename="configeditor_ready.tmp",
        main_app_name="ConfigEditor.exe",
        splash_image_filename="時間割くんドライバアイコン起動中.ico"
    )
    return run_launcher(config)


if __name__ == '__main__':
    main()
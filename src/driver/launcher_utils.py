"""
launcher_utils.py - 共通ランチャーロジックモジュール

3つのランチャー（ConfigEditor, ConfigEditorTutorial, TimetableChecker）で
共通して使用されるスプラッシュスクリーン表示とIPC通信ロジックを提供します。
"""
import sys
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer


@dataclass
class LauncherConfig:
    """ランチャーの設定を保持するデータクラス"""
    ipc_ready_filename: str
    main_app_name: str
    splash_image_filename: str


def get_ipc_filepath(ipc_ready_filename: str) -> Path:
    """IPC用一時ファイルのパスを取得"""
    return Path(tempfile.gettempdir()) / ipc_ready_filename


def run_launcher(config: LauncherConfig) -> int:
    """
    スプラッシュスクリーンを表示し、メインアプリケーションを起動する。
    
    IPC通信（一時ファイル）を使用してメインアプリの準備完了を待機し、
    準備完了後またはタイムアウト後にランチャーを終了する。
    
    Args:
        config: ランチャー設定（IPCファイル名、アプリ名、スプラッシュ画像）
    
    Returns:
        終了コード（0: 正常終了、1: エラー）
    """
    app = QApplication(sys.argv)

    # --- パス解決 ---
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
        app_dir = Path(sys.executable).parent
    else:
        base_path = Path(__file__).resolve().parent
        app_dir = base_path

    # --- 定数 ---
    main_app_path = app_dir / config.main_app_name
    # メインアプリの起動完了待ち最大時間（フォールバック）
    MAX_WAIT_MS = 30000
    # IPCファイル確認間隔
    POLL_INTERVAL_MS = 100

    # --- IPC準備: 既存の準備完了ファイルを削除 ---
    ipc_filepath = get_ipc_filepath(config.ipc_ready_filename)
    if ipc_filepath.exists():
        try:
            ipc_filepath.unlink()
        except Exception:
            pass

    # --- QSplashScreenの生成と表示 ---
    splash_image_path = base_path / config.splash_image_filename
    splash_pixmap = QPixmap(str(splash_image_path))
    
    if not splash_pixmap.isNull():
        splash = QSplashScreen(splash_pixmap)
        splash.show()
        app.processEvents()

        # --- メインアプリケーションの起動 ---
        try:
            print(f"Launching main application: {main_app_path}")
            subprocess.Popen([str(main_app_path)])
        except FileNotFoundError:
            print(f"FATAL ERROR: Main application not found at '{main_app_path}'")
            splash.showMessage(
                f"Error: {config.main_app_name}が見つかりません。", 
                Qt.AlignCenter | Qt.AlignBottom, 
                Qt.red
            )
            QTimer.singleShot(MAX_WAIT_MS, app.quit)
        else:
            # --- IPCポーリング: メインアプリの準備完了を待つ ---
            elapsed_ms = [0]
            
            def check_ready():
                if ipc_filepath.exists():
                    print("Main application is ready. Closing launcher.")
                    try:
                        ipc_filepath.unlink()
                    except Exception:
                        pass
                    app.quit()
                    return
                
                elapsed_ms[0] += POLL_INTERVAL_MS
                
                if elapsed_ms[0] >= MAX_WAIT_MS:
                    print("Timeout waiting for main application. Closing launcher anyway.")
                    app.quit()
                    return
                
                QTimer.singleShot(POLL_INTERVAL_MS, check_ready)
            
            QTimer.singleShot(POLL_INTERVAL_MS, check_ready)
        
        return app.exec()

    else:
        # --- スプラッシュ画像が見つからない場合のフォールバック ---
        print(f"ERROR: Splash image not found at '{splash_image_path}'. Launching main app directly.")
        try:
            subprocess.Popen([str(main_app_path)])
        except FileNotFoundError:
            print(f"FATAL ERROR: Main application not found at '{main_app_path}'")
        return 1

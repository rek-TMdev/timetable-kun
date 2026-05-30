import sys
import subprocess
import tempfile
import os
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer
from pathlib import Path

# IPC用の一時ファイル名（本体アプリと共有）
IPC_READY_FILENAME = "timemanager_ready.tmp"

def get_ipc_filepath():
    """IPC用一時ファイルのパスを取得"""
    return Path(tempfile.gettempdir()) / IPC_READY_FILENAME

def main():
    """
    専用ランチャーとしてスプラッシュ画面を表示し、メインアプリを起動する。
    メインアプリの準備完了はIPC用の一時ファイルで検知する。
    """
    app = QApplication(sys.argv)

    # --- パス解決 ---
    # ソース実行時と配布版の両方でリソース基準パスを決定する。
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # 配布版exeとして実行中
        base_path = Path(sys._MEIPASS)
        # メインアプリのexeはランチャーと同じディレクトリに置く想定
        app_dir = Path(sys.executable).parent
    else:
        # .pyスクリプトとして実行中
        base_path = Path(__file__).resolve().parent
        app_dir = base_path

    # --- 定数 ---
    MAIN_APP_NAME = "TimeManager.exe"
    MAIN_APP_PATH = app_dir / MAIN_APP_NAME
    # メインアプリの起動完了待ち最大時間（フォールバック）
    MAX_WAIT_MS = 30000
    # IPCファイル確認間隔
    POLL_INTERVAL_MS = 100

    # --- IPC準備: 既存の準備完了ファイルを削除 ---
    ipc_filepath = get_ipc_filepath()
    if ipc_filepath.exists():
        try:
            ipc_filepath.unlink()
        except Exception:
            pass

    # --- QSplashScreenの生成と表示 ---
    splash_image_path = base_path / "時間割くんアイコン起動中.ico"
    splash_pixmap = QPixmap(str(splash_image_path))
    
    if not splash_pixmap.isNull():
        splash = QSplashScreen(splash_pixmap)
        splash.show()
        app.processEvents()

        # --- メインアプリケーションの起動 ---
        try:
            print(f"Launching main application: {MAIN_APP_PATH}")
            subprocess.Popen([MAIN_APP_PATH])
        except FileNotFoundError:
            # メインアプリが見つからない場合はスプラッシュ画面にエラーを表示
            print(f"FATAL ERROR: Main application not found at '{MAIN_APP_PATH}'")
            splash.showMessage(f"Error: {MAIN_APP_NAME}が見つかりません。", Qt.AlignCenter | Qt.AlignBottom, Qt.red)
            # エラーを確認できるようスプラッシュ画面を一定時間残す
            QTimer.singleShot(MAX_WAIT_MS, app.quit)
        else:
            # --- IPCポーリング: メインアプリの準備完了を待つ ---
            elapsed_ms = [0]  # クロージャ内で更新できるようlistで保持
            
            def check_ready():
                # 準備完了ファイルの有無を確認
                if ipc_filepath.exists():
                    print("Main application is ready. Closing launcher.")
                    # 準備完了ファイルを削除
                    try:
                        ipc_filepath.unlink()
                    except Exception:
                        pass
                    app.quit()
                    return
                
                # 経過時間を更新
                elapsed_ms[0] += POLL_INTERVAL_MS
                
                # タイムアウト判定
                if elapsed_ms[0] >= MAX_WAIT_MS:
                    print("Timeout waiting for main application. Closing launcher anyway.")
                    app.quit()
                    return
                
                # ポーリングを継続
                QTimer.singleShot(POLL_INTERVAL_MS, check_ready)
            
            # ポーリングを開始
            QTimer.singleShot(POLL_INTERVAL_MS, check_ready)
        
        sys.exit(app.exec())

    else:
        # --- スプラッシュ画像が見つからない場合のフォールバック ---
        print(f"ERROR: Splash image not found at '{splash_image_path}'. Launching main app directly.")
        try:
            subprocess.Popen([MAIN_APP_PATH])
        except FileNotFoundError:
            print(f"FATAL ERROR: Main application not found at '{MAIN_APP_PATH}'")
        sys.exit(1)


if __name__ == '__main__':
    main()

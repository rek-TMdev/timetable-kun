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
    This script is a dedicated launcher. It shows a splash screen
    and then launches the main application.
    Uses a temporary file for IPC to detect when main app is ready.
    """
    app = QApplication(sys.argv)

    # --- Path Resolution ---
    # Determines the base path for resources, whether running from source or bundled.
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a bundled executable
        base_path = Path(sys._MEIPASS)
        # The main app executable is expected to be in the same directory as this launcher
        app_dir = Path(sys.executable).parent
    else:
        # Running as a .py script
        base_path = Path(__file__).resolve().parent
        app_dir = base_path

    # --- Constants ---
    MAIN_APP_NAME = "TimeManager.exe"
    MAIN_APP_PATH = app_dir / MAIN_APP_NAME
    # Maximum time to wait for main app (fallback timeout)
    MAX_WAIT_MS = 30000
    # Polling interval for IPC file check
    POLL_INTERVAL_MS = 100

    # --- IPC Setup: Delete any existing ready file ---
    ipc_filepath = get_ipc_filepath()
    if ipc_filepath.exists():
        try:
            ipc_filepath.unlink()
        except Exception:
            pass

    # --- Create and show the QSplashScreen ---
    splash_image_path = base_path / "時間割くんアイコン起動中.ico"
    splash_pixmap = QPixmap(str(splash_image_path))
    
    if not splash_pixmap.isNull():
        splash = QSplashScreen(splash_pixmap)
        splash.show()
        app.processEvents()

        # --- Launch the Main Application ---
        try:
            print(f"Launching main application: {MAIN_APP_PATH}")
            subprocess.Popen([MAIN_APP_PATH])
        except FileNotFoundError:
            # If the main app is not found, show an error on the splash screen
            print(f"FATAL ERROR: Main application not found at '{MAIN_APP_PATH}'")
            splash.showMessage(f"Error: {MAIN_APP_NAME}が見つかりません。", Qt.AlignCenter | Qt.AlignBottom, Qt.red)
            # Keep the splash screen open longer so the user can see the error
            QTimer.singleShot(MAX_WAIT_MS, app.quit)
        else:
            # --- IPC Polling: Wait for main app to signal readiness ---
            elapsed_ms = [0]  # Using list to allow mutation in closure
            
            def check_ready():
                # Check if the ready file exists
                if ipc_filepath.exists():
                    print("Main application is ready. Closing launcher.")
                    # Clean up the ready file
                    try:
                        ipc_filepath.unlink()
                    except Exception:
                        pass
                    app.quit()
                    return
                
                # Update elapsed time
                elapsed_ms[0] += POLL_INTERVAL_MS
                
                # Timeout check
                if elapsed_ms[0] >= MAX_WAIT_MS:
                    print("Timeout waiting for main application. Closing launcher anyway.")
                    app.quit()
                    return
                
                # Continue polling
                QTimer.singleShot(POLL_INTERVAL_MS, check_ready)
            
            # Start polling
            QTimer.singleShot(POLL_INTERVAL_MS, check_ready)
        
        sys.exit(app.exec())

    else:
        # --- Fallback if splash image is not found ---
        print(f"ERROR: Splash image not found at '{splash_image_path}'. Launching main app directly.")
        try:
            subprocess.Popen([MAIN_APP_PATH])
        except FileNotFoundError:
            print(f"FATAL ERROR: Main application not found at '{MAIN_APP_PATH}'")
        sys.exit(1)


if __name__ == '__main__':
    main()

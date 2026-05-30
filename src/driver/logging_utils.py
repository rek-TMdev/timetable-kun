"""
logging_utils.py - 共有ロギングインフラストラクチャ

時間割くんツール群で使用するファイルベースのロギング機能を提供します。
ログは %APPDATA%/時間割くんツール/logs/ に保存されます。
"""
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_log_directory() -> Path:
    """
    ログディレクトリのパスを取得します。
    
    Returns:
        Path: ログディレクトリのパス (%APPDATA%/時間割くんツール/logs/)
    """
    if sys.platform == 'win32':
        appdata = os.getenv('APPDATA')
        if appdata:
            log_dir = Path(appdata) / "時間割くんツール" / "logs"
        else:
            log_dir = Path.home() / ".時間割くんツール" / "logs"
    else:
        log_dir = Path.home() / ".時間割くんツール" / "logs"
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Warning: Could not create log directory: {e}")
    
    return log_dir


def setup_logger(app_name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    アプリケーション用のロガーをセットアップします。
    
    ファイルハンドラ（RotatingFileHandler）とコンソールハンドラの両方を設定します。
    ログファイルは日付付きで作成され、最大5MBで3世代までバックアップされます。
    
    Args:
        app_name: アプリケーション名（ログファイル名のプレフィックスに使用）
        log_level: ログレベル（デフォルト: logging.INFO）
    
    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    
    Example:
        >>> logger = setup_logger("timetable_checker")
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(app_name)
    
    # 既に設定済みの場合は再設定しない
    if logger.handlers:
        return logger
    
    logger.setLevel(log_level)
    
    # ログフォーマット
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ファイルハンドラ（RotatingFileHandler）
    log_dir = get_log_directory()
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{app_name}_{today}.log"
    
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        print(f"Warning: Could not create file handler: {e}")
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_exception(logger: logging.Logger, exc: Exception, context: str = "") -> None:
    """
    例外を構造化された形式でログに記録します。
    
    Args:
        logger: ロガーインスタンス
        exc: 記録する例外
        context: 追加のコンテキスト情報（オプション）
    """
    if context:
        logger.error(f"{context}: {type(exc).__name__}: {exc}", exc_info=True)
    else:
        logger.error(f"{type(exc).__name__}: {exc}", exc_info=True)

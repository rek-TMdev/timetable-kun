"""
backup.py - 自動バックアップ機能

設定ファイルの自動バックアップを管理します。
保存時にバックアップを作成し、世代管理を行います。
"""
from __future__ import annotations
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class BackupInfo:
    """バックアップ情報を表すデータクラス"""
    path: Path
    created_at: datetime
    size_bytes: int
    
    @property
    def age_seconds(self) -> float:
        """作成からの経過秒数"""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def formatted_date(self) -> str:
        """フォーマット済み日時"""
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")
    
    @property
    def formatted_size(self) -> str:
        """フォーマット済みサイズ"""
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.1f} MB"


class BackupManager:
    """
    自動バックアップを管理するクラス。
    
    使用方法:
    1. BackupManagerをインスタンス化
    2. create_backup()で保存前にバックアップを作成
    3. list_backups()で既存のバックアップを確認
    4. restore_backup()でバックアップから復元
    """
    
    # バックアップファイルのサフィックスフォーマット
    BACKUP_SUFFIX_FORMAT = ".backup_{timestamp}"
    TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
    
    def __init__(
        self, 
        backup_dir: Optional[str | Path] = None,
        max_backups: int = 10,
        same_directory: bool = True
    ):
        """
        Args:
            backup_dir: バックアップ保存先ディレクトリ（Noneの場合は元ファイルと同じディレクトリ）
            max_backups: 保持する最大バックアップ数
            same_directory: Trueの場合、元ファイルと同じディレクトリにバックアップを作成
        """
        self.backup_dir = Path(backup_dir) if backup_dir else None
        self.max_backups = max_backups
        self.same_directory = same_directory
    
    def create_backup(self, file_path: str | Path) -> Optional[BackupInfo]:
        """
        ファイルのバックアップを作成する。
        
        Args:
            file_path: バックアップするファイルのパス
            
        Returns:
            作成されたBackupInfo、失敗時はNone
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        # バックアップのパスを決定
        backup_path = self._get_backup_path(file_path)
        
        # ディレクトリが存在しない場合は作成
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.copy2(file_path, backup_path)
            
            # 古いバックアップを削除
            self._cleanup_old_backups(file_path)
            
            stat = backup_path.stat()
            return BackupInfo(
                path=backup_path,
                created_at=datetime.now(),
                size_bytes=stat.st_size
            )
        except Exception as e:
            print(f"バックアップ作成エラー: {e}")
            return None
    
    def _get_backup_path(self, file_path: Path) -> Path:
        """バックアップファイルのパスを生成"""
        timestamp = datetime.now().strftime(self.TIMESTAMP_FORMAT)
        backup_name = f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"
        
        if self.same_directory or self.backup_dir is None:
            return file_path.parent / backup_name
        else:
            return self.backup_dir / backup_name
    
    def _get_backup_pattern(self, file_path: Path) -> str:
        """バックアップファイルのパターンを取得"""
        return f"{file_path.stem}.backup_*{file_path.suffix}"
    
    def list_backups(self, file_path: str | Path) -> List[BackupInfo]:
        """
        指定ファイルのバックアップ一覧を取得する。
        
        Args:
            file_path: 元ファイルのパス
            
        Returns:
            BackupInfoのリスト（新しい順）
        """
        file_path = Path(file_path)
        pattern = self._get_backup_pattern(file_path)
        
        if self.same_directory or self.backup_dir is None:
            search_dir = file_path.parent
        else:
            search_dir = self.backup_dir
        
        if not search_dir.exists():
            return []
        
        backups = []
        for backup_file in search_dir.glob(pattern):
            try:
                stat = backup_file.stat()
                # タイムスタンプをファイル名から解析
                timestamp_str = self._extract_timestamp(backup_file.stem, file_path.stem)
                if timestamp_str:
                    created_at = datetime.strptime(timestamp_str, self.TIMESTAMP_FORMAT)
                else:
                    created_at = datetime.fromtimestamp(stat.st_mtime)
                
                backups.append(BackupInfo(
                    path=backup_file,
                    created_at=created_at,
                    size_bytes=stat.st_size
                ))
            except Exception:
                continue
        
        # 新しい順にソート
        backups.sort(key=lambda x: x.created_at, reverse=True)
        return backups
    
    def _extract_timestamp(self, backup_stem: str, original_stem: str) -> Optional[str]:
        """バックアップファイル名からタイムスタンプを抽出"""
        prefix = f"{original_stem}.backup_"
        if backup_stem.startswith(prefix):
            return backup_stem[len(prefix):]
        return None
    
    def _cleanup_old_backups(self, file_path: Path):
        """古いバックアップを削除"""
        backups = self.list_backups(file_path)
        
        if len(backups) > self.max_backups:
            for old_backup in backups[self.max_backups:]:
                try:
                    old_backup.path.unlink()
                except Exception as e:
                    print(f"古いバックアップの削除に失敗: {e}")
    
    def restore_backup(self, backup_path: str | Path, target_path: str | Path) -> bool:
        """
        バックアップから復元する。
        
        Args:
            backup_path: 復元するバックアップファイルのパス
            target_path: 復元先のパス
            
        Returns:
            成功時True
        """
        backup_path = Path(backup_path)
        target_path = Path(target_path)
        
        if not backup_path.exists():
            return False
        
        try:
            # 現在のファイルもバックアップしてから復元
            if target_path.exists():
                self.create_backup(target_path)
            
            shutil.copy2(backup_path, target_path)
            return True
        except Exception as e:
            print(f"復元エラー: {e}")
            return False
    
    def delete_backup(self, backup_path: str | Path) -> bool:
        """
        バックアップを削除する。
        
        Args:
            backup_path: 削除するバックアップファイルのパス
            
        Returns:
            成功時True
        """
        backup_path = Path(backup_path)
        
        try:
            backup_path.unlink()
            return True
        except Exception as e:
            print(f"バックアップ削除エラー: {e}")
            return False
    
    def delete_all_backups(self, file_path: str | Path) -> int:
        """
        指定ファイルの全バックアップを削除する。
        
        Args:
            file_path: 元ファイルのパス
            
        Returns:
            削除したバックアップの数
        """
        backups = self.list_backups(file_path)
        deleted = 0
        
        for backup in backups:
            if self.delete_backup(backup.path):
                deleted += 1
        
        return deleted


def create_backup(file_path: str | Path, max_backups: int = 10) -> Optional[BackupInfo]:
    """
    簡易バックアップ作成関数。
    
    Args:
        file_path: バックアップするファイルのパス
        max_backups: 保持する最大バックアップ数
        
    Returns:
        作成されたBackupInfo、失敗時はNone
    """
    manager = BackupManager(max_backups=max_backups)
    return manager.create_backup(file_path)

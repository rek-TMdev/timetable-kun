"""
ConfigManager - 設定ファイルの読み込み・保存を管理するクラス

Application クラスから設定関連の責務を分離するために作成。
このクラスはUIに依存しないコア機能を提供します。
"""
import json
import os
import sys
from pathlib import Path
from typing import Optional, Any


class ConfigManager:
    """
    アプリケーション設定の読み込み・保存を管理するクラス。
    
    責務:
    - ユーザー設定ファイル（AppData/時間割くん/config.json）の読み書き
    - 学校設定ファイル（*.json）の読み込み
    - 設定値の取得（GENERAL_SETTINGS優先のフォールバック）
    
    Note:
        UI操作を伴う設定ファイル選択ダイアログなどはApplicationクラスに残し、
        このクラスはファイルI/Oと設定値の管理のみを行います。
    """
    
    def __init__(self, base_path: Path):
        """
        ConfigManagerを初期化します。
        
        Args:
            base_path: アプリケーションのベースパス（リソース配置先）
        """
        self.base_path = base_path
        self.config: dict = {}
        self.config_path: Optional[Path] = None
        self.user_settings: dict = {}
    
    def get_user_settings_path(self) -> Path:
        """
        ユーザー設定ファイルのパスを取得します。
        
        凍結実行ファイル（PyInstaller）の場合は_internal（sys._MEIPASS）に保存し、
        開発環境ではbase_path直下に保存します。
        
        Returns:
            ユーザー設定ファイルへのパス
        """
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # ビルド後は _internal フォルダ (sys._MEIPASS) に配置
            return Path(sys._MEIPASS) / "config.json"
        return self.base_path / "config.json"
    
    def load_user_settings(self) -> dict:
        """
        ユーザー設定ファイルを読み込みます。
        
        ファイルが存在しない、または破損している場合は空の辞書を返します。
        
        Returns:
            ユーザー設定の辞書
        """
        path = self.get_user_settings_path()
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.user_settings = json.load(f)
                    return self.user_settings
            except (json.JSONDecodeError, IOError):
                self.user_settings = {}
                return {}
        self.user_settings = {}
        return {}
    
    def save_user_settings(self, settings: dict) -> bool:
        """
        ユーザー設定をファイルに保存します。
        
        Args:
            settings: 保存する設定の辞書
            
        Returns:
            保存が成功した場合はTrue、失敗した場合はFalse
        """
        path = self.get_user_settings_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            self.user_settings = settings
            return True
        except IOError as e:
            print(f"ユーザー設定の保存に失敗しました: {e}")
            return False
    
    def reset_user_settings(self) -> None:
        """
        ユーザー設定ファイルを削除してリセットします。
        """
        path = self.get_user_settings_path()
        if path.exists():
            try:
                os.remove(path)
            except OSError as e:
                print(f"ユーザー設定のリセットに失敗しました: {e}")
        self.user_settings = {}
    
    def load_config(self, config_path: Path) -> dict:
        """
        指定されたパスから設定ファイルを読み込みます。
        
        Args:
            config_path: 設定ファイルへのパス
            
        Returns:
            設定の辞書
            
        Raises:
            FileNotFoundError: ファイルが見つからない場合
            json.JSONDecodeError: JSONの解析に失敗した場合
            ValueError: 設定ファイルの形式が不正な場合
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 学校設定ファイルの検証
        validation_errors = self.validate_school_config(self.config)
        if validation_errors:
            raise ValueError(f"設定ファイルの形式が不正です:\n" + "\n".join(validation_errors))
        
        self.config_path = config_path
        return self.config
    
    def validate_school_config(self, config: dict) -> list[str]:
        """
        学校設定ファイルの構造を検証します。
        
        Args:
            config: 読み込んだ設定辞書
            
        Returns:
            エラーメッセージのリスト（空の場合は有効）
        """
        errors = []
        
        if not isinstance(config, dict):
            errors.append("設定ファイルのルート要素が辞書ではありません")
            return errors
        
        # 必須キーのチェック（学校設定ファイルに必要な基本キー）
        required_keys = ["YEARS_HIERARCHY"]
        for key in required_keys:
            if key not in config:
                errors.append(f"必須キー '{key}' が見つかりません")
        
        # YEARS_HIERARCHYの構造チェック
        if "YEARS_HIERARCHY" in config:
            hierarchy = config["YEARS_HIERARCHY"]
            if not isinstance(hierarchy, dict):
                errors.append("'YEARS_HIERARCHY' は辞書である必要があります")
            elif not hierarchy:
                errors.append("'YEARS_HIERARCHY' が空です（学年データが必要です）")
        
        # GENERAL_SETTINGSのチェック（存在する場合）
        if "GENERAL_SETTINGS" in config:
            gs = config["GENERAL_SETTINGS"]
            if not isinstance(gs, dict):
                errors.append("'GENERAL_SETTINGS' は辞書である必要があります")
        
        return errors
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得します。
        
        以下の優先順位で検索:
        1. user_settings（特定のユーザー設定キーの場合）
        2. GENERAL_SETTINGS内
        3. トップレベルのconfig
        
        Args:
            key: 設定キー
            default: キーが見つからない場合のデフォルト値
            
        Returns:
            設定値、または見つからない場合はdefault
        """
        # ユーザー設定ファイルに保存される設定キー
        user_setting_keys = [
            "TIMETABLE_ORDER", "RUN_TUTORIAL_ON_STARTUP", "APP_FONT_SIZE",
            "APP_THEME", "MAX_MEMORY_LIMIT", "last_opened_config"
        ]
        
        # ユーザー設定キーはuser_settingsを優先
        if key in user_setting_keys and key in self.user_settings:
            return self.user_settings[key]
        
        general_settings = self.config.get("GENERAL_SETTINGS", {})
        if key in general_settings:
            return general_settings.get(key, default)
        return self.config.get(key, default)
    
    def get_last_opened_config_path(self) -> Optional[Path]:
        """
        前回開いた設定ファイルのパスを取得します。
        
        Returns:
            前回開いた設定ファイルのパス、または存在しない場合はNone
        """
        if "last_opened_config" in self.user_settings:
            path_str = self.user_settings["last_opened_config"]
            if path_str:
                path = Path(path_str)
                if path.is_file():
                    return path
        return None
    
    def find_config_files(self) -> list[dict]:
        """
        利用可能な設定ファイルを検索します。
        
        base_pathとカレントディレクトリから*.jsonファイルを検索し、
        有効な設定ファイルのリストを返します。
        
        Returns:
            設定ファイル情報のリスト（path, school, date を含む辞書）
        """
        search_dirs = {
            str(Path(self.base_path).resolve()),
            str(Path(os.getcwd()).resolve())
        }
        possible_paths = set()
        
        for directory in search_dirs:
            try:
                for filename in os.listdir(directory):
                    # .tm.json と config.json を除外
                    if (filename.endswith('.json') and 
                        not filename.endswith('.tm.json') and 
                        not filename.endswith('config.json')):
                        possible_paths.add(os.path.join(directory, filename))
            except OSError:
                continue
        
        valid_configs = []
        seen_paths = set()
        
        for path_str in possible_paths:
            path = Path(path_str).resolve()
            if path in seen_paths or not path.is_file():
                continue
            seen_paths.add(path)
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    valid_configs.append({
                        "path": str(path),
                        "school": data.get("SCHOOL_NAME", "（学校名未設定）"),
                        "date": data.get("LAST_UPDATE_DAY", "（更新日時なし）")
                    })
            except (json.JSONDecodeError, IOError):
                continue
        
        return valid_configs
    
    def validate_config_file(self, path: Path) -> bool:
        """
        設定ファイルが有効なJSONかどうかを検証します。
        
        Args:
            path: 検証するファイルへのパス
            
        Returns:
            有効な場合はTrue、無効な場合はFalse
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, IOError, FileNotFoundError):
            return False

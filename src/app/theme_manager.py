"""
ThemeManager - テーマ・スタイリングを管理するクラス

Application クラスからテーマ関連の責務を分離するために作成。
ダークモード判定、テーマカラー管理、SVGアイコン生成を担当します。
"""
import os
import re
import sys
from pathlib import Path
from typing import Optional

import darkdetect
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QIcon


def is_windows_light_theme() -> bool:
    """Windowsでライトテーマを使用しているかを判定します。"""
    if sys.platform != "win32":
        return True
    try:
        import winreg
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 1
    except (ImportError, FileNotFoundError, OSError):
        return True


class ThemeManager:
    """
    テーマ・スタイリングの管理を行うクラス。
    
    責務:
    - ダークモード/ライトモードの判定
    - テーマカラーの管理（設定ファイルから読み込み）
    - SVGアイコンの色変換と生成
    
    Note:
        このクラスはUIに依存しない純粋なテーマロジックを提供します。
        スタイルシートの適用はApplicationクラスに残します。
    """
    
    # デフォルトのテーマカラー (Light)
    DEFAULT_THEME_COLORS_LIGHT = {
        "duplicate_subject": "#FFD699",
        "prerequisite_missing": "#FF9999",
        "no_together_conflict": "#7CAAFA",
        "user_locked_subject": "#D8E6FF",
        "user_locked_conflict": "#E0E0E0"
    }

    # デフォルトのテーマカラー (Dark)
    DEFAULT_THEME_COLORS_DARK = {
        "duplicate_subject": "#CC8800",
        "prerequisite_missing": "#CC4444",
        "no_together_conflict": "#4477CC",
        "user_locked_subject": "#335588",
        "user_locked_conflict": "#666666"
    }
    
    def __init__(self, base_path: Path, config: dict = None):
        """
        ThemeManagerを初期化します。
        
        Args:
            base_path: アプリケーションのベースパス（SVGファイル配置先）
            config: 設定辞書（THEME_COLORSを含む）
        """
        self.base_path = base_path
        self.config = config or {} # 設定を保持
        self.theme_colors = {}
        self._is_dark = None  # キャッシュ
        
        # configから初期テーマ設定を読み込む（現在はSystemを優先）
        self._manual_theme_mode = self.config.get("APP_THEME", "System")
        
        self.reload_theme_colors()

    def set_theme_mode(self, mode: str) -> None:
        """
        テーマモードを手動設定します。
        
        Args:
            mode: "Light", "Dark", "System" のいずれか
        """
        self._manual_theme_mode = mode
        self.refresh_theme()

    def get_theme_mode(self) -> str:
        """現在のテーマモード設定を取得します。"""
        return self._manual_theme_mode or "System"
    
    def is_dark_theme(self) -> bool:
        """
        現在のテーマがダークモードかどうかを判定します。
        
        設定（APP_THEME） > OSの設定 の優先順位で判定します。
        
        Returns:
            ダークモードの場合True、ライトモードの場合False
        """
        if self._is_dark is not None:
            return self._is_dark
        
        # 1. 手動設定のチェック
        if self._manual_theme_mode == "Dark":
            self._is_dark = True
            return True
        if self._manual_theme_mode == "Light":
            self._is_dark = False
            return False
        
        # 2. System (OS設定) のチェック
        ini_theme = darkdetect.theme()
        
        if ini_theme == "Dark":
            self._is_dark = True
            return True
        if ini_theme == "Light":
            self._is_dark = False
            return False
        
        # テーマが不明な場合はOS設定にフォールバック
        os_is_light = is_windows_light_theme()
        self._is_dark = not os_is_light
        return self._is_dark
    
    def refresh_theme(self) -> None:
        """テーマ判定のキャッシュをクリアして再判定し、色をリロードします。"""
        self._is_dark = None
        self.reload_theme_colors()
    
    def reload_theme_colors(self) -> None:
        """現在のテーマに基づいてテーマカラーを再読み込みします。"""
        self._load_theme_colors(self.config)

    def _load_theme_colors(self, config: dict) -> None:
        """
        設定ファイルからテーマカラーを読み込みます。
        
        ダーク/ライトモードに応じた色を選択し、
        見つからない場合はデフォルト値を使用します。
        
        Args:
            config: 設定辞書
        """
        config_colors = config.get("THEME_COLORS", {})
        use_dark = self.is_dark_theme()
        
        defaults = self.DEFAULT_THEME_COLORS_DARK if use_dark else self.DEFAULT_THEME_COLORS_LIGHT

        for key, default_val in defaults.items():
            # モード別キー（key_dark / key_light）を優先
            mode_key = f"{key}_dark" if use_dark else f"{key}_light"
            if mode_key in config_colors:
                self.theme_colors[key] = config_colors[mode_key]
            elif key in config_colors:
                # 汎用キーにフォールバック（後方互換性）
                self.theme_colors[key] = config_colors[key]
            else:
                self.theme_colors[key] = default_val
    
    def get_theme_color(self, key: str, default: str = None) -> str:
        """
        テーマカラーを取得します。
        
        Args:
            key: カラーキー（duplicate_subject, prerequisite_missing等）
            default: キーが見つからない場合のデフォルト値
            
        Returns:
            カラーの16進値（例: "#FFD699"）
        """
        if default:
            return self.theme_colors.get(key, default)
            
        # デフォルト値がない場合は定数からルックアップ
        fallback = self.DEFAULT_THEME_COLORS_DARK.get(key) if self.is_dark_theme() else self.DEFAULT_THEME_COLORS_LIGHT.get(key)
        return self.theme_colors.get(key, fallback or "#FFFFFF")
    
    def get_all_theme_colors(self) -> dict:
        """
        すべてのテーマカラーを辞書として取得します。
        
        Returns:
            テーマカラーの辞書
        """
        return self.theme_colors.copy()
    
    def get_icon_color(self) -> str:
        """
        現在のテーマに適したアイコン色を取得します。
        
        Returns:
            ダークモードの場合は白（#FFFFFF）、ライトモードの場合は黒（#1F1F1F）
        """
        return "#FFFFFF" if self.is_dark_theme() else "#1F1F1F"
    
    def create_icon_from_svg(self, svg_path: str, color_hex: str = None) -> Optional[QIcon]:
        """
        SVGファイルから指定色のアイコンを作成します。
        
        Args:
            svg_path: SVGファイルへのパス（絶対パスまたは相対パス）
            color_hex: 使用する色（16進値）。省略時はテーマに応じた色を使用
            
        Returns:
            QIcon オブジェクト、作成に失敗した場合はNone
        """
        try:
            from PySide6.QtSvg import QSvgRenderer
        except ImportError:
            return None
        
        # 相対パスの場合はbase_pathからの相対として解決
        if not os.path.isabs(svg_path):
            svg_path = os.path.join(self.base_path, svg_path)
        
        if not os.path.exists(svg_path):
            print(f"SVG file not found: {svg_path}")
            return None
        
        # 色を決定
        if color_hex is None:
            color_hex = self.get_icon_color()
        
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_data = f.read()
        
        # デフォルト色（#1f1f1f）を指定色に置換
        colored_svg_data = re.sub('#1f1f1f', color_hex, svg_data, flags=re.IGNORECASE)
        
        renderer = QSvgRenderer(colored_svg_data.encode('utf-8'))
        if not renderer.isValid():
            print(f"Invalid SVG data for: {svg_path}")
            return None
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)

# config_editor package
"""
Config Editor パッケージ

config_editor_main.pyのMainWindowをリファクタリングするためのモジュール群を提供します。

主要コンポーネント:
- TabManager: タブの統一管理
- UndoManager: Undo/Redo機能
- ConfigValidator: スキーマ検証
- ExcelImporter/ExcelExporter: Excel I/O
- SearchWidget: 検索機能

使用例:
    from config_model import ConfigModel
    from config_editor import TabManager, UndoManager
    from config_editor.schema import ConfigValidator, validate_config
    from config_editor.excel_io import ExcelImporter, ExcelExporter
"""

from .tab_manager import TabManager
from .undo_manager import UndoManager

__all__ = ['TabManager', 'UndoManager']

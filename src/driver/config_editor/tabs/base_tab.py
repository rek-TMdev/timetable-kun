"""
base_tab.py - タブウィジェットの基底クラス

全ての設定タブクラスが継承する抽象基底クラスを定義します。
共通のインターフェースを提供することで、MainWindowとの一貫した連携を保証します。
"""
from __future__ import annotations
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Optional

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal

if TYPE_CHECKING:
    from config_model import ConfigModel


class BaseTab(QWidget):
    """
    全ての設定タブウィジェットの基底クラス。
    
    サブクラスは以下のメソッドをオーバーライドする必要があります：
    - _setup_ui(): UIコンポーネントを構築
    - populate(): config_modelからデータを読み込んでUIを更新
    - collect_to_config(): UIの状態をconfig_dictに収集
    """
    
    # データが変更されたことを通知するシグナル
    data_changed = Signal()
    
    def __init__(self, config_model: "ConfigModel", parent: Optional[QWidget] = None):
        """
        Args:
            config_model: 設定データを管理するConfigModelインスタンス
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self.config_model = config_model
        self._main_layout = QVBoxLayout(self)
        self._setup_ui()
        self._connect_signals()
    
    @abstractmethod
    def _setup_ui(self):
        """
        UIコンポーネントを構築する。
        
        サブクラスはこのメソッドでウィジェットを作成し、
        self._main_layout に追加する必要があります。
        """
        pass
    
    def _connect_signals(self):
        """
        シグナルとスロットを接続する。
        
        サブクラスはこのメソッドをオーバーライドして、
        UIイベントハンドラを接続できます。
        """
        pass
    
    @abstractmethod
    def populate(self):
        """
        config_modelのデータでUIを更新する。
        
        このメソッドは以下のタイミングで呼び出されます：
        - ファイルが読み込まれた時
        - データが外部から更新された時
        """
        pass
    
    @abstractmethod
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """
        UIの状態をconfig_dictに収集する。
        
        このメソッドは保存時に呼び出され、UIの現在の状態を
        config_dictに反映させます。
        
        Args:
            config_dict: 設定データを格納する辞書
        """
        pass
    
    def mark_modified(self):
        """データが変更されたことをマークし、シグナルを発火する。"""
        self.config_model.mark_modified()
        self.data_changed.emit()
    
    def get_master_subjects(self) -> list:
        """利便性メソッド: 教科マスタリストを取得"""
        return self.config_model.get_master_subjects()

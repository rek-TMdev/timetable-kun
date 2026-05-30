"""
tab_manager.py - タブ管理クラス

MainWindowの分離されたタブクラスを管理し、統一されたインターフェースを提供します。
このクラスを使用することで、既存のconfig_editor_main.pyを段階的にリファクタリングできます。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Callable

from PySide6.QtWidgets import QStackedWidget, QListWidget, QListWidgetItem

if TYPE_CHECKING:
    from config_model import ConfigModel
    from config_editor.tabs.base_tab import BaseTab


class TabManager:
    """
    タブクラスを管理し、MainWindowとの橋渡しを行うマネージャクラス。
    
    使い方:
    1. TabManagerをインスタンス化
    2. register_tab()で各タブを登録
    3. initialize()でタブを初期化
    4. populate_all()でデータを読み込み
    5. collect_all()で保存時にデータを収集
    """
    
    def __init__(
        self, 
        stacked_widget: QStackedWidget, 
        tab_list: QListWidget,
        config_model: "ConfigModel"
    ):
        """
        Args:
            stacked_widget: タブのコンテンツを表示するQStackedWidget
            tab_list: タブ選択用のQListWidget
            config_model: 設定データを管理するConfigModel
        """
        self.stacked_widget = stacked_widget
        self.tab_list = tab_list
        self.config_model = config_model
        
        self._tabs: List[Dict[str, Any]] = []
        self._tab_instances: Dict[str, "BaseTab"] = {}
    
    def register_tab(
        self, 
        tab_class: type,
        display_name: str,
        key: str,
        icon_creator: Optional[Callable] = None,
        base_path: str = "",
        **kwargs
    ):
        """
        タブを登録する。
        
        Args:
            tab_class: タブクラス（BaseTabのサブクラス）
            display_name: リストに表示する名前
            key: タブを識別するためのキー
            icon_creator: アイコン作成関数（オプション）
            base_path: アプリのベースパス（オプション）
            **kwargs: タブクラスに渡す追加の引数
        """
        self._tabs.append({
            "class": tab_class,
            "display_name": display_name,
            "key": key,
            "icon_creator": icon_creator,
            "base_path": base_path,
            "kwargs": kwargs
        })
    
    def initialize(self):
        """
        登録されたタブをインスタンス化し、ウィジェットに追加する。
        """
        for tab_info in self._tabs:
            tab_class = tab_info["class"]
            key = tab_info["key"]
            display_name = tab_info["display_name"]
            
            # タブインスタンスを作成
            tab_instance = tab_class(
                config_model=self.config_model,
                icon_creator=tab_info["icon_creator"],
                base_path=tab_info["base_path"],
                **tab_info["kwargs"]
            )
            
            # ウィジェットに追加
            self.stacked_widget.addWidget(tab_instance)
            self.tab_list.addItem(display_name)
            
            # インスタンスを保存
            self._tab_instances[key] = tab_instance
    
    def get_tab(self, key: str) -> Optional["BaseTab"]:
        """キーでタブインスタンスを取得"""
        return self._tab_instances.get(key)
    
    def populate_all(self):
        """
        全てのタブにデータを読み込む。
        """
        for tab in self._tab_instances.values():
            try:
                tab.populate()
            except Exception as e:
                print(f"Error populating tab: {e}")
    
    def collect_all(self, config_dict: Dict[str, Any]):
        """
        全てのタブからデータを収集する。
        
        Args:
            config_dict: 収集先の設定辞書
        """
        for tab in self._tab_instances.values():
            try:
                tab.collect_to_config(config_dict)
            except Exception as e:
                print(f"Error collecting from tab: {e}")
    
    def connect_tab_selection(self):
        """
        タブリストの選択変更をスタックウィジェットに接続する。
        """
        self.tab_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
    
    def get_all_tabs(self) -> Dict[str, "BaseTab"]:
        """全てのタブインスタンスを取得"""
        return self._tab_instances.copy()
    
    def on_data_changed(self, callback: Callable):
        """
        データ変更時のコールバックを全タブに接続する。
        
        Args:
            callback: 呼び出すコールバック関数
        """
        for tab in self._tab_instances.values():
            tab.data_changed.connect(callback)

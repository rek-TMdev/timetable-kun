"""
search_widget.py - インクリメンタルサーチウィジェット

リストやテーブルをフィルタリングするための検索ウィジェットを提供します。
"""
from __future__ import annotations
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QListWidget
)
from PySide6.QtCore import Qt, Signal, QTimer


class SearchWidget(QWidget):
    """
    インクリメンタルサーチウィジェット。
    
    入力テキストに基づいてリストをフィルタリングします。
    遅延検索（debounce）機能付き。
    """
    
    # シグナル
    search_changed = Signal(str)  # 検索テキスト変更時
    cleared = Signal()  # クリア時
    
    def __init__(
        self, 
        parent: Optional[QWidget] = None,
        placeholder: str = "検索...",
        debounce_ms: int = 200
    ):
        super().__init__(parent)
        self._debounce_ms = debounce_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._emit_search)
        
        self._setup_ui(placeholder)
    
    def _setup_ui(self, placeholder: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input)
        
        self.clear_button = QPushButton("×")
        self.clear_button.setFixedWidth(30)
        self.clear_button.clicked.connect(self.clear)
        layout.addWidget(self.clear_button)
    
    def _on_text_changed(self, text: str):
        """テキスト変更時（debounce）"""
        self._timer.stop()
        self._timer.start(self._debounce_ms)
    
    def _emit_search(self):
        """検索シグナルを発火"""
        self.search_changed.emit(self.search_input.text())
    
    def clear(self):
        """検索をクリア"""
        self.search_input.clear()
        self.cleared.emit()
    
    def text(self) -> str:
        """現在の検索テキスト"""
        return self.search_input.text()
    
    def set_text(self, text: str):
        """検索テキストを設定"""
        self.search_input.setText(text)


class FilterableListWidget(QWidget):
    """
    検索機能付きリストウィジェット。
    
    SearchWidgetとQListWidgetを組み合わせて、
    インクリメンタルサーチ機能を提供します。
    """
    
    # シグナル（QListWidgetのシグナルを転送）
    item_selected = Signal(str)  # アイテム選択時
    item_double_clicked = Signal(str)  # ダブルクリック時
    
    def __init__(
        self, 
        parent: Optional[QWidget] = None,
        placeholder: str = "検索..."
    ):
        super().__init__(parent)
        self._all_items: list = []
        self._setup_ui(placeholder)
    
    def _setup_ui(self, placeholder: str):
        from PySide6.QtWidgets import QVBoxLayout
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 検索ウィジェット
        self.search_widget = SearchWidget(self, placeholder)
        self.search_widget.search_changed.connect(self._filter_items)
        self.search_widget.cleared.connect(self._show_all)
        layout.addWidget(self.search_widget)
        
        # リスト
        self.list_widget = QListWidget()
        self.list_widget.currentTextChanged.connect(self._on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(
            lambda item: self.item_double_clicked.emit(item.text())
        )
        layout.addWidget(self.list_widget)
    
    def _filter_items(self, search_text: str):
        """アイテムをフィルタリング"""
        if not search_text:
            self._show_all()
            return
        
        search_lower = search_text.lower()
        self.list_widget.clear()
        
        for item in self._all_items:
            if search_lower in item.lower():
                self.list_widget.addItem(item)
    
    def _show_all(self):
        """全アイテムを表示"""
        self.list_widget.clear()
        self.list_widget.addItems(self._all_items)
    
    def _on_selection_changed(self, text: str):
        """選択変更時"""
        if text:
            self.item_selected.emit(text)
    
    def set_items(self, items: list):
        """アイテムを設定"""
        self._all_items = list(items)
        self._show_all()
    
    def add_item(self, item: str):
        """アイテムを追加"""
        self._all_items.append(item)
        if not self.search_widget.text() or self.search_widget.text().lower() in item.lower():
            self.list_widget.addItem(item)
    
    def remove_item(self, item: str):
        """アイテムを削除"""
        if item in self._all_items:
            self._all_items.remove(item)
            items = self.list_widget.findItems(item, Qt.MatchExactly)
            for i in items:
                self.list_widget.takeItem(self.list_widget.row(i))
    
    def current_item(self) -> Optional[str]:
        """現在選択中のアイテム"""
        item = self.list_widget.currentItem()
        return item.text() if item else None
    
    def select_item(self, item: str):
        """アイテムを選択"""
        items = self.list_widget.findItems(item, Qt.MatchExactly)
        if items:
            self.list_widget.setCurrentItem(items[0])
    
    def clear(self):
        """全てクリア"""
        self._all_items = []
        self.list_widget.clear()
        self.search_widget.clear()
    
    def count(self) -> int:
        """アイテム数を取得"""
        return len(self._all_items)
    
    def items(self) -> list:
        """全アイテムを取得"""
        return list(self._all_items)

"""
year_settings_tab.py - 学年設定タブ

学年設定とアンカー機能を管理するタブ。
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, 
    QInputDialog, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel

# アンカー表示用の定数
ANCHOR_MARKER = " ⚓"


class YearSettingsTab(BaseTab):
    """
    学年設定タブ。
    
    学年（課程→年次など）の構造と、
    アンカー（選択確定ポイント）を設定します。
    """
    
    # シグナル
    hierarchy_changed = Signal()
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._current_editing_text: Optional[str] = None
        self._anchors: Set[str] = set()  # パスで管理するアンカーのセット
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        # メインの水平レイアウト（左：ツリー、右：ボタン）
        main_h_layout = QHBoxLayout()
        
        # 左側：ツリーエリア
        tree_container = QVBoxLayout()
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.tree_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree_widget.setHeaderLabel("学年 / 課程")
        tree_container.addWidget(self.tree_widget)
        
        # アンカーの説明ラベル
        anchor_info = QLabel("⚓ アンカー: 選択時に階層選択を終了")
        anchor_info.setStyleSheet("color: gray; font-size: 11px;")
        tree_container.addWidget(anchor_info)
        
        main_h_layout.addLayout(tree_container, stretch=1)
        
        # 右側：ボタンを縦に配置
        v_button_layout = QVBoxLayout()
        
        self.add_item_button = QPushButton("追加")
        self.remove_button = QPushButton("削除")
        self.anchor_button = QPushButton("アンカー")
        self.apply_button = QPushButton("適用")
        
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_item_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.anchor_button.setIcon(self._icon_creator(os.path.join(svg_path, "anchor.svg")))
                self.apply_button.setIcon(self._icon_creator(os.path.join(svg_path, "apply.svg")))
            except Exception:
                pass
        
        v_button_layout.addWidget(self.add_item_button)
        v_button_layout.addWidget(self.remove_button)
        v_button_layout.addWidget(self.anchor_button)
        v_button_layout.addStretch()  # 上部に寄せる
        v_button_layout.addWidget(self.apply_button)
        
        main_h_layout.addLayout(v_button_layout)
        
        self._main_layout.addLayout(main_h_layout)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree_widget.itemChanged.connect(self._on_item_changed)
        
        self.add_item_button.clicked.connect(self.add_item)
        self.remove_button.clicked.connect(self.remove_item)
        self.anchor_button.clicked.connect(self.toggle_anchor)
        self.apply_button.clicked.connect(self.apply_hierarchy)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_item_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.anchor_button.setIcon(self._icon_creator(os.path.join(svg_path, "anchor.svg")))
                self.apply_button.setIcon(self._icon_creator(os.path.join(svg_path, "apply.svg")))
            except Exception:
                pass

    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        # アンカーを読み込み
        self._anchors = set(self.config_model.get_hierarchy_anchors())
        
        # 階層ツリー（マーカーが残っている場合はクリーンアップ）
        self.tree_widget.clear()
        hierarchy = self.config_model.get_years_hierarchy()
        hierarchy = self._clean_hierarchy_keys(hierarchy)
        self._add_tree_items(self.tree_widget, hierarchy, [])
        self.tree_widget.expandAll()
    
    def _clean_hierarchy_keys(self, data: dict) -> dict:
        """階層キーからアンカーマーカーを除去（互換性のため）"""
        result = {}
        for key, children in data.items():
            clean_key = key
            # マーカー（" ⚓"）を除去
            if key.endswith(ANCHOR_MARKER):
                clean_key = key[:-len(ANCHOR_MARKER)]
            # 念のため、末尾のアンカー絵文字自体もチェック
            elif key.endswith("⚓"):
                clean_key = key[:-1].rstrip()
            result[clean_key] = self._clean_hierarchy_keys(children) if children else {}
        return result
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集"""
        # 階層
        hierarchy = self._build_hierarchy_from_tree()
        config_dict["YEARS_HIERARCHY"] = hierarchy
        
        # アンカー
        config_dict["HIERARCHY_ANCHORS"] = list(self._anchors)
    
    # =========================================================================
    # ツリー操作
    # =========================================================================
    
    def _get_item_path(self, item: QTreeWidgetItem) -> str:
        """アイテムのフルパスを取得（アンカーマーカーを除去）"""
        path_parts = []
        current = item
        while current:
            text = current.text(0)
            # アンカーマーカーを除去
            if text.endswith(ANCHOR_MARKER):
                text = text[:-len(ANCHOR_MARKER)]
            path_parts.insert(0, text)
            current = current.parent()
        return "_".join(path_parts)
    
    def _add_tree_items(self, parent, data: dict, path: List[str]):
        """再帰的にツリーアイテムを追加"""
        for text, children_data in sorted(data.items()):
            current_path = path + [text]
            path_key = "_".join(current_path)
            
            # アンカーが設定されているかチェック
            display_text = text
            if path_key in self._anchors:
                display_text = text + ANCHOR_MARKER
            
            item = QTreeWidgetItem(parent, [display_text])
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            
            # アンカー設定されている場合は太字に
            if path_key in self._anchors:
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
            
            self._add_tree_items(item, children_data, current_path)
    
    def _build_hierarchy_from_tree(self) -> dict:
        """ツリーから階層構造を構築"""
        result = {}
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            text = self._get_clean_text(item)
            result[text] = self._build_hierarchy_from_item(item)
        return result
    
    def _build_hierarchy_from_item(self, item: QTreeWidgetItem) -> dict:
        """再帰的にアイテムから階層を構築"""
        result = {}
        for i in range(item.childCount()):
            child = item.child(i)
            text = self._get_clean_text(child)
            result[text] = self._build_hierarchy_from_item(child)
        return result
    
    def _get_clean_text(self, item: QTreeWidgetItem) -> str:
        """アンカーマーカーを除去したテキストを取得"""
        text = item.text(0)
        # マーカー（" ⚓"）を除去
        if text.endswith(ANCHOR_MARKER):
            return text[:-len(ANCHOR_MARKER)]
        # 念のため、末尾のアンカー絵文字自体もチェック
        if text.endswith("⚓"):
            return text[:-1].rstrip()
        return text
    
    def _on_item_double_clicked(self, item, column):
        """ダブルクリック時：編集開始"""
        self._current_editing_text = item.text(column)
    
    def _on_item_changed(self, item, column):
        """アイテム変更時：リネーム処理"""
        if self._current_editing_text is None:
            return
        
        new_text = item.text(column)
        if self._current_editing_text == new_text:
            return
        
        # 禁止文字のチェック（アンカーマーカーを除いたテキストで）
        clean_new_text = new_text.replace(ANCHOR_MARKER, "").replace("⚓", "")
        for char in ["_"]:  # ⚓は表示用なのでここでは_のみチェック
            if char in clean_new_text:
                QMessageBox.warning(
                    self, "入力エラー", 
                    f"項目名に「{char}」を含めることはできません。\n"
                    "（この文字はシステムで予約されています）"
                )
                item.setText(column, self._current_editing_text)  # 元に戻す
                self._current_editing_text = None
                return
        
        self._current_editing_text = None
        self.mark_modified()
    
    # 禁止文字（パス区切りとアンカーマーカーで使用）
    FORBIDDEN_CHARS = ["_", "⚓"]
    
    def add_item(self):
        """項目を追加"""
        text, ok = QInputDialog.getText(self, "項目を追加", "新しい項目名を入力してください:")
        if not ok or not text:
            return
        
        # 禁止文字のチェック
        for char in self.FORBIDDEN_CHARS:
            if char in text:
                QMessageBox.warning(
                    self, "入力エラー", 
                    f"項目名に「{char}」を含めることはできません。\n"
                    "（この文字はシステムで予約されています）"
                )
                return
        
        selected = self.tree_widget.selectedItems()
        
        if selected:
            # 選択アイテムの下に追加
            parent = selected[0]
            item = QTreeWidgetItem(parent, [text])
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
            parent.setExpanded(True)
        else:
            # トップレベルに追加
            item = QTreeWidgetItem(self.tree_widget, [text])
            item.setFlags(item.flags() | Qt.ItemIsEditable | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled)
        
        self.mark_modified()
    
    def remove_item(self):
        """選択項目を削除"""
        selected = self.tree_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "エラー", "削除する項目を選択してください。")
            return
        
        reply = QMessageBox.question(
            self, "確認",
            "選択した項目を削除しますか？子項目も含めて削除されます。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        for item in selected:
            # アンカーも削除
            path_key = self._get_item_path(item)
            self._anchors.discard(path_key)
            
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                index = self.tree_widget.indexOfTopLevelItem(item)
                self.tree_widget.takeTopLevelItem(index)
        
        self.mark_modified()
    
    def toggle_anchor(self):
        """選択項目のアンカーを設定/解除"""
        selected = self.tree_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "エラー", "アンカーを設定する項目を選択してください。")
            return
        
        for item in selected:
            path_key = self._get_item_path(item)
            text = self._get_clean_text(item)
            
            if path_key in self._anchors:
                # アンカーを解除
                self._anchors.discard(path_key)
                item.setText(0, text)
                font = item.font(0)
                font.setBold(False)
                item.setFont(0, font)
            else:
                # アンカーを設定
                self._anchors.add(path_key)
                item.setText(0, text + ANCHOR_MARKER)
                font = item.font(0)
                font.setBold(True)
                item.setFont(0, font)
        
        self.mark_modified()
    
    def apply_hierarchy(self):
        """設定を適用"""
        hierarchy = self._build_hierarchy_from_tree()
        self.config_model.update_years_hierarchy(hierarchy)
        self.config_model.update_hierarchy_anchors(list(self._anchors))
        self.hierarchy_changed.emit()
        QMessageBox.information(self, "完了", "階層設定を適用しました。")

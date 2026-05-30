"""
prerequisite_tab.py - 前提教科設定タブ

教科の履修に必要な前提教科を設定するタブウィジェットです。
例：「数学Ⅲ」を履修するには「数学Ⅱ」「数学B」が必要、など。
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class PrerequisiteTab(BaseTab):
    """
    前提教科設定タブ。
    
    親教科とその前提となる教科（子教科）のペアを設定します。
    親教科を履修するためには、子教科を全て履修している必要があります。
    """
    
    # シグナル
    prerequisite_added = Signal(str, str)  # 前提教科追加時（parent, child）
    selection_changed = Signal()
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._current_parent: Optional[str] = None
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        h_layout = QHBoxLayout()
        self._main_layout.addLayout(h_layout)
        
        # === 左ペイン: 親教科リスト ===
        left_pane = QWidget()
        left_pane.setFixedWidth(250)
        left_layout = QVBoxLayout(left_pane)
        
        left_layout.addWidget(QLabel("<b>前提教科ルール</b>"))
        
        self.parent_list = QListWidget()
        left_layout.addWidget(self.parent_list)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("追加")
        self.remove_button = QPushButton("削除")
        
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        left_layout.addLayout(button_layout)
        
        h_layout.addWidget(left_pane)
        
        # === 右ペイン: 詳細 ===
        self.details_pane = QWidget()
        self.details_pane.setVisible(False)
        details_layout = QVBoxLayout(self.details_pane)
        
        self.parent_label = QLabel("")
        font = self.parent_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.parent_label.setFont(font)
        details_layout.addWidget(self.parent_label)
        
        details_layout.addWidget(QLabel("以下の教科を前提とします:"))
        
        # 教科選択エリア
        subjects_layout = QHBoxLayout()
        
        # 割り当て済み
        assigned_layout = QVBoxLayout()
        assigned_layout.addWidget(QLabel("前提となる教科"))
        self.assigned_list = QListWidget()
        self.assigned_list.setSelectionMode(QListWidget.ExtendedSelection)
        assigned_layout.addWidget(self.assigned_list)
        subjects_layout.addLayout(assigned_layout)
        
        # 移動ボタン
        move_layout = QVBoxLayout()
        move_layout.addStretch()
        self.move_to_button = QPushButton("← 追加")
        self.move_from_button = QPushButton("削除 →")
        move_layout.addWidget(self.move_to_button)
        move_layout.addWidget(self.move_from_button)
        move_layout.addStretch()
        subjects_layout.addLayout(move_layout)
        
        # 利用可能
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("選択可能な教科"))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.ExtendedSelection)
        available_layout.addWidget(self.available_list)
        subjects_layout.addLayout(available_layout)
        
        details_layout.addLayout(subjects_layout)
        h_layout.addWidget(self.details_pane)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.parent_list.currentRowChanged.connect(self._on_parent_selected)
        self.add_button.clicked.connect(self.add_rule)
        self.remove_button.clicked.connect(self.remove_rule)
        self.move_to_button.clicked.connect(self.move_to_prereq)
        self.move_from_button.clicked.connect(self.move_from_prereq)
    
        self.move_from_button.clicked.connect(self.move_from_prereq)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        current_selection = (
            self.parent_list.currentItem().text()
            if self.parent_list.currentItem() else None
        )
        
        self.parent_list.blockSignals(True)
        self.parent_list.clear()
        
        prereqs = self.config_model.get_prerequisites()
        sorted_parents = sorted(prereqs.keys())
        
        for parent in sorted_parents:
            item = QListWidgetItem(parent)
            children = prereqs.get(parent, [])
            item.setData(Qt.UserRole, children)
            self.parent_list.addItem(item)
        
        # 選択を復元
        if current_selection and current_selection in sorted_parents:
            for i, parent in enumerate(sorted_parents):
                if parent == current_selection:
                    self.parent_list.setCurrentRow(i)
                    break
        
        self.parent_list.blockSignals(False)
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集"""
        prereqs = {}
        
        for i in range(self.parent_list.count()):
            item = self.parent_list.item(i)
            parent_name = item.text()
            children = item.data(Qt.UserRole) or []
            if children:
                prereqs[parent_name] = sorted(children)
        
        if prereqs:
            config_dict["PREREQUISITE_SUBJECTS"] = prereqs
        elif "PREREQUISITE_SUBJECTS" in config_dict:
            del config_dict["PREREQUISITE_SUBJECTS"]
    
    # =========================================================================
    # Event Handlers
    # =========================================================================
    
    def _on_parent_selected(self, index: int):
        """親教科選択時のハンドラ"""
        if index < 0:
            self.details_pane.setVisible(False)
            self._current_parent = None
            return
        
        parent_item = self.parent_list.item(index)
        self._current_parent = parent_item.text()
        self.details_pane.setVisible(True)
        self.parent_label.setText(f"親教科: [ {self._current_parent} ]")
        
        # 割り当て済みリスト
        assigned = parent_item.data(Qt.UserRole) or []
        self.assigned_list.clear()
        self.assigned_list.addItems(sorted(assigned))
        
        # 利用可能リスト
        master_subjects = self.config_model.get_master_subjects()
        available = [s for s in master_subjects if s not in assigned and s != self._current_parent]
        self.available_list.clear()
        self.available_list.addItems(sorted(available))
        
        self.selection_changed.emit()
    
    # =========================================================================
    # Public Methods
    # =========================================================================
    
    def add_rule(self):
        """新しい前提教科ルールを追加"""
        existing = {
            self.parent_list.item(i).text()
            for i in range(self.parent_list.count())
        }
        
        master_subjects = self.config_model.get_master_subjects()
        available = [s for s in master_subjects if s not in existing]
        
        if not available:
            QMessageBox.information(self, "情報", "すべての教科が既に追加されています。")
            return
        
        parent, ok = QInputDialog.getItem(
            self, "親教科の追加",
            "前提教科を設定する親教科を選択してください:",
            sorted(available), 0, False
        )
        
        if ok and parent:
            item = QListWidgetItem(parent)
            item.setData(Qt.UserRole, [])
            self.parent_list.addItem(item)
            self.parent_list.setCurrentItem(item)
            self.mark_modified()
    
    def remove_rule(self):
        """選択されたルールを削除"""
        current_item = self.parent_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "エラー", "削除する親教科を選択してください。")
            return
        
        parent = current_item.text()
        reply = QMessageBox.question(
            self, "確認",
            f"親教科「{parent}」とその前提教科設定を削除しますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.parent_list.takeItem(self.parent_list.row(current_item))
            self.details_pane.setVisible(False)
            self._current_parent = None
            self.mark_modified()
    
    def move_to_prereq(self):
        """教科を前提教科リストに追加"""
        selected = self.available_list.selectedItems()
        if not selected:
            return
        
        for item in selected:
            self.assigned_list.addItem(item.text())
        
        rows = sorted([self.available_list.row(item) for item in selected], reverse=True)
        for row in rows:
            self.available_list.takeItem(row)
        
        self._save_to_item()
        self.mark_modified()
        
        if selected:
            self.prerequisite_added.emit(self._current_parent, selected[0].text())
    
    def move_from_prereq(self):
        """教科を前提教科リストから削除"""
        for item in self.assigned_list.selectedItems():
            self.available_list.addItem(item.text())
            self.assigned_list.takeItem(self.assigned_list.row(item))
        
        self._save_to_item()
        self.mark_modified()
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    def _save_to_item(self):
        """現在の状態をアイテムのUserRoleに保存"""
        current_item = self.parent_list.currentItem()
        if not current_item:
            return
        
        children = [
            self.assigned_list.item(i).text()
            for i in range(self.assigned_list.count())
        ]
        current_item.setData(Qt.UserRole, children)

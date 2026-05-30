"""
no_together_tab.py - 同時選択不可設定タブ

同時に履修できない教科のグループを設定するタブウィジェットです。
例：「古典基礎」と「古典探究」は同時に選択できない、など。
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class NoTogetherTab(BaseTab):
    """
    同時選択不可設定タブ。
    
    同時に履修できない教科のグループを管理します。
    グループ内のいずれか1つの教科のみを選択可能とする制約を設定できます。
    """
    
    # シグナル
    group_added = Signal()
    subject_added_to_group = Signal()
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._current_group_index: int = -1
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        h_layout = QHBoxLayout()
        self._main_layout.addLayout(h_layout)
        
        # === 左ペイン: グループリスト ===
        left_pane = QWidget()
        left_pane.setFixedWidth(300)
        left_layout = QVBoxLayout(left_pane)
        
        left_layout.addWidget(QLabel("<b>同時選択不可グループ一覧</b>"))
        
        self.groups_list = QListWidget()
        left_layout.addWidget(self.groups_list)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_group_button = QPushButton("グループを追加")
        self.delete_group_button = QPushButton("グループを削除")
        
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_group_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.delete_group_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
        
        button_layout.addWidget(self.add_group_button)
        button_layout.addWidget(self.delete_group_button)
        left_layout.addLayout(button_layout)
        
        h_layout.addWidget(left_pane)
        
        # === 右ペイン: 詳細 ===
        self.details_pane = QWidget()
        self.details_pane.setVisible(False)
        details_layout = QVBoxLayout(self.details_pane)
        
        self.group_label = QLabel("")
        font = self.group_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.group_label.setFont(font)
        details_layout.addWidget(self.group_label)
        
        # 教科選択エリア
        subjects_layout = QHBoxLayout()
        
        # グループ内の教科
        assigned_layout = QVBoxLayout()
        assigned_layout.addWidget(QLabel("グループ内の教科"))
        self.assigned_list = QListWidget()
        self.assigned_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
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
        
        # 利用可能な教科
        available_layout = QVBoxLayout()
        available_layout.addWidget(QLabel("選択可能な教科"))
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        available_layout.addWidget(self.available_list)
        subjects_layout.addLayout(available_layout)
        
        details_layout.addLayout(subjects_layout)
        h_layout.addWidget(self.details_pane)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.groups_list.currentRowChanged.connect(self._on_group_selected)
        self.add_group_button.clicked.connect(self.add_group)
        self.delete_group_button.clicked.connect(self.delete_group)
        self.move_to_button.clicked.connect(self.move_to_group)
        self.move_from_button.clicked.connect(self.move_from_group)
    
        self.move_from_button.clicked.connect(self.move_from_group)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_group_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.delete_group_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        self.groups_list.blockSignals(True)
        self.groups_list.clear()
        self.details_pane.setVisible(False)
        
        groups = self.config_model.get_no_together_groups()
        
        for i, group in enumerate(groups):
            item_text = ", ".join(sorted(group)) if group else "(空のグループ)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, group)
            self.groups_list.addItem(item)
        
        self.groups_list.blockSignals(False)
        
        if self.groups_list.count() > 0:
            self.groups_list.setCurrentRow(0)
        else:
            self._on_group_selected(-1)
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集"""
        all_groups = []
        
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item:
                group_data = item.data(Qt.UserRole)
                if group_data:  # 空でないグループのみ
                    all_groups.append(sorted(group_data))
        
        if all_groups:
            config_dict["NO_TOGETHER_SUBJECTS"] = all_groups
        elif "NO_TOGETHER_SUBJECTS" in config_dict:
            del config_dict["NO_TOGETHER_SUBJECTS"]
    
    # =========================================================================
    # イベントハンドラ
    # =========================================================================
    
    def _on_group_selected(self, index: int):
        """グループ選択時のハンドラ"""
        self._current_group_index = index
        
        if index < 0:
            self.details_pane.setVisible(False)
            return
        
        item = self.groups_list.item(index)
        if not item:
            return
        
        self.details_pane.setVisible(True)
        self.group_label.setText(f"グループ {index + 1} の編集")
        
        # グループ内の教科
        group_subjects = item.data(Qt.UserRole) or []
        self.assigned_list.clear()
        self.assigned_list.addItems(sorted(group_subjects))
        
        # 利用可能な教科
        master_subjects = self.config_model.get_master_subjects()
        available = [s for s in master_subjects if s not in group_subjects]
        self.available_list.clear()
        self.available_list.addItems(sorted(available))
    
    # =========================================================================
    # 公開メソッド
    # =========================================================================
    
    def add_group(self):
        """新しいグループを追加"""
        item = QListWidgetItem("(空のグループ)")
        item.setData(Qt.UserRole, [])
        self.groups_list.addItem(item)
        self.groups_list.setCurrentItem(item)
        self.mark_modified()
        self.group_added.emit()
    
    def delete_group(self):
        """選択されたグループを削除"""
        current_item = self.groups_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "エラー", "削除するグループを選択してください。")
            return
        
        reply = QMessageBox.question(
            self, "確認",
            "選択したグループを削除しますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.groups_list.takeItem(self.groups_list.row(current_item))
            self.mark_modified()
    
    def move_to_group(self):
        """教科をグループに追加"""
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
        self.subject_added_to_group.emit()
    
    def move_from_group(self):
        """教科をグループから削除"""
        selected = self.assigned_list.selectedItems()
        if not selected:
            return
        
        texts = [item.text() for item in selected]
        rows = sorted([self.assigned_list.row(item) for item in selected], reverse=True)
        
        for text in texts:
            self.available_list.addItem(text)
        
        for row in rows:
            self.assigned_list.takeItem(row)
        
        self._save_to_item()
        self.available_list.sortItems()
        self.mark_modified()
    
    # =========================================================================
    # 内部メソッド
    # =========================================================================
    
    def _save_to_item(self):
        """現在の状態をアイテムのUserRoleに保存"""
        current_item = self.groups_list.currentItem()
        if not current_item:
            return
        
        subjects = [
            self.assigned_list.item(i).text()
            for i in range(self.assigned_list.count())
        ]
        current_item.setData(Qt.UserRole, subjects)
        
        # 表示テキストも更新
        display_text = ", ".join(sorted(subjects)) if subjects else "(空のグループ)"
        current_item.setText(display_text)

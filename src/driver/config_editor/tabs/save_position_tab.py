"""
save_position_tab.py - 保存位置設定タブ

Excelファイルへの保存時のセル位置を設定するタブ。
各スロットに対応するセル位置（A1, B2など）を指定できます。
"""
from __future__ import annotations
import os
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class SavePositionTab(BaseTab):
    """
    保存位置設定タブ。
    
    Excel出力時の各スロットのセル位置を設定します。
    年次ごとにスロットとセル位置のマッピングを管理します。
    """
    
    # シグナル
    leaf_selection_changed = Signal()
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._current_year: Optional[str] = None
        self._cascading_combos: List[QComboBox] = []
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        # 年次選択
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("設定対象:"))
        self._combo_layout = QHBoxLayout()
        selector_layout.addLayout(self._combo_layout)
        selector_layout.addStretch()
        self._main_layout.addLayout(selector_layout)
        
        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["スロット名", "セル位置"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self._main_layout.addWidget(self.table)
        
        # ガイダンス
        guidance = QLabel('案内: セル位置は "A1" や "B2,C3" のように、カンマ区切りで入力してください。')
        guidance.setWordWrap(True)
        self._main_layout.addWidget(guidance)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("行を追加")
        self.delete_button = QPushButton("選択行を削除")
        self.fill_button = QPushButton("連番を記入")
        
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.delete_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.fill_button.setIcon(self._icon_creator(os.path.join(svg_path, "list_number.svg")))
            except Exception:
                pass
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.fill_button)
        self._main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.add_button.clicked.connect(self.add_row)
        self.delete_button.clicked.connect(self.delete_row)
        self.fill_button.clicked.connect(self.auto_fill)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.delete_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.fill_button.setIcon(self._icon_creator(os.path.join(svg_path, "list_number.svg")))
            except Exception:
                pass

    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        self._initialize_selectors()
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集"""
        self._save_current_to_config(config_dict)
    
    # =========================================================================
    # 年次選択
    # =========================================================================
    
    def _initialize_selectors(self):
        """年次選択コンボボックスを初期化"""
        # 既存のコンボボックスをクリア
        for combo in self._cascading_combos:
            self._combo_layout.removeWidget(combo)
            combo.deleteLater()
        self._cascading_combos.clear()
        
        # 最上位の階層
        hierarchy = self.config_model.get_years_hierarchy()
        top_items = sorted(hierarchy.keys())
        
        first_combo = QComboBox()
        first_combo.addItem("(未選択)")
        first_combo.addItems(top_items)
        first_combo.currentIndexChanged.connect(lambda: self._update_selectors(level=1))
        self._cascading_combos.append(first_combo)
        self._combo_layout.addWidget(first_combo)
        
        self._update_selectors(level=1)
    
    def _update_selectors(self, level: int):
        """指定レベル以降のコンボボックスを更新"""
        # 既存の下位コンボを削除
        while len(self._cascading_combos) > level:
            combo = self._cascading_combos.pop()
            self._combo_layout.removeWidget(combo)
            combo.deleteLater()
        
        # パスを構築
        path = []
        for i in range(level):
            combo = self._cascading_combos[i]
            if combo.currentIndex() > 0:
                path.append(combo.currentText())
            else:
                self._on_selection_changed()
                return
        
        # 子ノードを取得
        hierarchy = self.config_model.get_years_hierarchy()
        node = hierarchy
        for key in path:
            node = node.get(key, {})
        
        children = list(node.keys()) if node else []
        
        if children:
            new_combo = QComboBox()
            new_combo.addItem("(未選択)")
            new_combo.addItems(sorted(children))
            new_combo.currentIndexChanged.connect(
                lambda state, l=level + 1: self._update_selectors(level=l)
            )
            self._cascading_combos.append(new_combo)
            self._combo_layout.addWidget(new_combo)
        
        self._on_selection_changed()
    
    def _on_selection_changed(self):
        """年次選択変更時のハンドラ"""
        path = []
        for combo in self._cascading_combos:
            if combo.currentIndex() > 0:
                path.append(combo.currentText())
            else:
                break
        
        year_key = "_".join(path) if path else None
        
        # リーフノードかチェック
        is_leaf = False
        if year_key:
            hierarchy = self.config_model.get_years_hierarchy()
            node = hierarchy
            for key in path:
                node = node.get(key, {})
            if not node:
                is_leaf = True
        
        self.table.setEnabled(is_leaf)
        if is_leaf:
            self.leaf_selection_changed.emit()
        
        if self._current_year != year_key:
            self._save_current_to_model()
            self._current_year = year_key
            self._populate_table()
    
    def _populate_table(self):
        """テーブルにデータを読み込む"""
        self.table.setRowCount(0)
        if not self._current_year:
            return
        
        year_suffix = self._current_year
        save_pos_data = self.config_model.get_setting(f"SAVE_POSITION{year_suffix}", {})
        all_slots = sorted(self.config_model.get_setting(f"ALL_SLOTS{year_suffix}", []))
        used_slots = set(save_pos_data.keys())
        
        for slot, pos_list in sorted(save_pos_data.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            combo = QComboBox()
            for s in all_slots:
                display = f"{s} (使用中)" if s in used_slots and s != slot else s
                combo.addItem(display)
            combo.setCurrentText(slot)
            self.table.setCellWidget(row, 0, combo)
            
            cell_str = ",".join(pos_list[0]) if pos_list and pos_list[0] else ""
            self.table.setItem(row, 1, QTableWidgetItem(cell_str))
    
    def _save_current_to_model(self):
        """現在のテーブル状態をモデルに保存"""
        if not self._current_year:
            return
        
        year_suffix = self._current_year
        key = f"SAVE_POSITION{year_suffix}"
        new_data = {}
        
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            pos_item = self.table.item(row, 1)
            
            if combo and pos_item:
                slot = combo.currentText().replace(" (使用中)", "")
                if slot:
                    pos_list = [p.strip() for p in pos_item.text().split(',') if p.strip()]
                    new_data[slot] = [pos_list]
        
        if new_data:
            self.config_model.set_setting(key, new_data)
        else:
            # 空の場合は削除
            current = self.config_model.get_setting(key)
            if current:
                self.config_model.set_setting(key, None)
    
    def _save_current_to_config(self, config_dict: Dict[str, Any]):
        """現在のテーブル状態をconfig_dictに保存"""
        if not self._current_year:
            return
        
        year_suffix = self._current_year
        key = f"SAVE_POSITION{year_suffix}"
        new_data = {}
        
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            pos_item = self.table.item(row, 1)
            
            if combo and pos_item:
                slot = combo.currentText().replace(" (使用中)", "")
                if slot:
                    pos_list = [p.strip() for p in pos_item.text().split(',') if p.strip()]
                    new_data[slot] = [pos_list]
        
        if new_data:
            config_dict[key] = new_data
        elif key in config_dict:
            del config_dict[key]
    
    # =========================================================================
    # 公開メソッド
    # =========================================================================
    
    def add_row(self):
        """行を追加"""
        if not self._current_year:
            return
        
        year_suffix = self._current_year
        all_slots = sorted(self.config_model.get_setting(f"ALL_SLOTS{year_suffix}", []))
        
        if not all_slots:
            QMessageBox.warning(
                self, "スロット未定義",
                f'「{year_suffix}」のスロットが「スロットレイアウト設定」で定義されていません。'
            )
            return
        
        # 使用中のスロットを取得
        used_slots = set()
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 0)
            if combo:
                slot = combo.currentText().replace(' (使用中)', '')
                used_slots.add(slot)
        
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        combo = QComboBox()
        for s in all_slots:
            display = f"{s} (使用中)" if s in used_slots else s
            combo.addItem(display)
        
        self.table.setCellWidget(row_position, 0, combo)
        self.table.setItem(row_position, 1, QTableWidgetItem(""))
        self.mark_modified()
    
    def delete_row(self):
        """選択行を削除"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
            self.mark_modified()
    
    def auto_fill(self):
        """連番を自動記入"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "行が選択されていません", "連番記入の開始点となる行を選択してください。")
            return
        
        start_row = self.table.row(selected[0])
        start_item = self.table.item(start_row, 1)
        
        if not start_item or not start_item.text():
            QMessageBox.warning(self, "開始セルが空です", "連番記入の開始点となる行の「セル位置」列に値がありません。")
            return
        
        start_text = start_item.text()
        
        for i in range(start_row + 1, self.table.rowCount()):
            increment = i - start_row
            
            parts = start_text.split(',')
            new_parts = []
            
            for part in parts:
                part = part.strip()
                match = re.match(r'^([A-Z]+)(\d+)$', part, re.IGNORECASE)
                if match:
                    prefix = match.group(1)
                    try:
                        number = int(match.group(2))
                        new_number = number + increment
                        new_parts.append(f"{prefix}{new_number}")
                    except ValueError:
                        new_parts.append(part)
                else:
                    new_parts.append(part)
            
            new_text = ",".join(new_parts)
            
            current_item = self.table.item(i, 1)
            if not current_item:
                current_item = QTableWidgetItem(new_text)
                self.table.setItem(i, 1, current_item)
            else:
                current_item.setText(new_text)
        
        self.mark_modified()

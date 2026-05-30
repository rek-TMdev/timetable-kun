"""
layout_tab.py - スロットレイアウト設定タブ

時間割のスロットレイアウト（表形式）と固定教科設定を管理するタブ。
MainWindowの実装に完全準拠。
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class LayoutTab(BaseTab):
    """
    スロットレイアウト設定タブ。
    
    年次ごとのスロットレイアウト（テーブル形式）を設定します。
    各セルにスロット名を入力し、固定教科を割り当てることができます。
    """
    
    # シグナル
    layout_changed = Signal()
    slot_selected = Signal(str)  # 選択されたスロット名
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._cascading_combos: List[QComboBox] = []
        self._current_year: Optional[str] = None
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        main_layout = QHBoxLayout()
        self._main_layout.addLayout(main_layout)
        
        # === 左側: テーブルエリア ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        main_layout.addWidget(left_widget, 3)
        
        # 年次選択
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("設定対象:"))
        self.combo_layout = QHBoxLayout()
        selector_layout.addLayout(self.combo_layout)
        selector_layout.addStretch()
        left_layout.addLayout(selector_layout)
        
        # レイアウトテーブル
        self.table = QTableWidget()
        left_layout.addWidget(self.table)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("行を追加")
        self.add_col_btn = QPushButton("列を追加")
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs", "plus.svg")
                icon = self._icon_creator(svg_path)
                self.add_row_btn.setIcon(icon)
                self.add_col_btn.setIcon(icon)
            except Exception:
                pass
        button_layout.addWidget(self.add_row_btn)
        button_layout.addWidget(self.add_col_btn)
        left_layout.addLayout(button_layout)
        
        # === 右側: 固定教科設定パネル ===
        self.fixed_panel = QGroupBox("固定教科設定")
        self.fixed_panel.setEnabled(False)
        panel_layout = QFormLayout(self.fixed_panel)
        main_layout.addWidget(self.fixed_panel, 1)
        
        self.slot_label = QLabel("(セルを選択してください)")
        self.subject_selector = QComboBox()
        
        panel_layout.addRow("選択中スロット:", self.slot_label)
        panel_layout.addRow("教科:", self.subject_selector)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.table.itemSelectionChanged.connect(self._on_slot_selected)
        self.add_row_btn.clicked.connect(self._add_row)
        self.add_col_btn.clicked.connect(self._add_column)
        self.subject_selector.currentIndexChanged.connect(self._on_subject_changed)
    
        self.subject_selector.currentIndexChanged.connect(self._on_subject_changed)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs", "plus.svg")
                icon = self._icon_creator(svg_path)
                self.add_row_btn.setIcon(icon)
                self.add_col_btn.setIcon(icon)
            except Exception:
                pass
    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        self._initialize_selectors()
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集（親ウィンドウで処理）"""
        pass
    
    # =========================================================================
    # 年次選択
    # =========================================================================
    
    def _initialize_selectors(self):
        """年次選択コンボボックスを初期化"""
        for combo in self._cascading_combos:
            self.combo_layout.removeWidget(combo)
            combo.deleteLater()
        self._cascading_combos.clear()
        
        hierarchy = self.config_model.get_years_hierarchy()
        top_items = sorted(hierarchy.keys())
        
        first_combo = QComboBox()
        first_combo.addItem("(未選択)")
        first_combo.addItems(top_items)
        first_combo.currentIndexChanged.connect(lambda: self._update_selectors(level=1))
        self._cascading_combos.append(first_combo)
        self.combo_layout.addWidget(first_combo)
        
        self._update_selectors(level=1)
    
    def _update_selectors(self, level: int):
        """下位コンボボックスを更新"""
        while len(self._cascading_combos) > level:
            combo = self._cascading_combos.pop()
            self.combo_layout.removeWidget(combo)
            combo.deleteLater()
        
        path = []
        for i in range(level):
            combo = self._cascading_combos[i]
            if combo.currentIndex() > 0:
                path.append(combo.currentText())
            else:
                self._on_year_changed()
                return
        
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
            self.combo_layout.addWidget(new_combo)
        
        self._on_year_changed()
    
    def _on_year_changed(self):
        """年次選択変更時"""
        path = []
        for combo in self._cascading_combos:
            if combo.currentIndex() > 0:
                path.append(combo.currentText())
            else:
                break
        
        year_key = "_".join(path) if path else None
        
        if self._current_year != year_key:
            self._current_year = year_key
            self._load_table()
    
    # =========================================================================
    # テーブル操作
    # =========================================================================
    
    def _load_table(self):
        """テーブルにレイアウトを読み込む"""
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        
        if not self._current_year:
            return
        
        # config_modelからレイアウトデータを取得
        layout = self.config_model.get_setting(f"table_layout{self._current_year}", [])
        
        if not layout:
            return
        
        max_cols = max(len(row) for row in layout) if layout else 0
        self.table.setRowCount(len(layout))
        self.table.setColumnCount(max_cols)
        
        for i, row in enumerate(layout):
            for j, cell in enumerate(row):
                item = QTableWidgetItem(cell)
                item.setData(Qt.UserRole, cell)  # 元のスロット名を保存
                self.table.setItem(i, j, item)
    
    def _add_row(self):
        """行を追加"""
        self.table.insertRow(self.table.rowCount())
        self.mark_modified()
    
    def _add_column(self):
        """列を追加"""
        self.table.insertColumn(self.table.columnCount())
        self.mark_modified()
    
    def _on_slot_selected(self):
        """スロット選択時"""
        selected = self.table.selectedItems()
        if not selected:
            self.fixed_panel.setEnabled(False)
            self.slot_label.setText("(セルを選択してください)")
            self.subject_selector.clear()
            return
        
        item = selected[0]
        slot_name = item.data(Qt.UserRole)
        
        if not slot_name:
            self.fixed_panel.setEnabled(False)
            self.slot_label.setText("(名前のないスロット)")
            self.subject_selector.clear()
            return
        
        self.fixed_panel.setEnabled(True)
        self.slot_label.setText(slot_name)
        self.slot_selected.emit(slot_name)
        
        # 教科コンボボックスを更新
        self.subject_selector.blockSignals(True)
        self.subject_selector.clear()
        subjects = ["(未選択)"] + self.config_model.get_master_subjects()
        self.subject_selector.addItems(subjects)
        
        # 固定教科が設定されている場合は選択
        fixed_slots = self.config_model.get_setting(f"FIXED_SLOTS{self._current_year}", {})
        current_fixed = fixed_slots.get(slot_name)
        if current_fixed and current_fixed in subjects:
            self.subject_selector.setCurrentText(current_fixed)
        
        self.subject_selector.blockSignals(False)
    
    def _on_subject_changed(self, index: int):
        """固定教科変更時"""
        self.mark_modified()

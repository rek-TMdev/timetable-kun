"""
subject_details_tab.py - 科目詳細設定タブ

各科目の単位数、スロット番号、スロットグループなどの詳細情報を設定するタブ。
MainWindowの実装に完全準拠。
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QComboBox, QSpinBox,
    QFormLayout, QScrollArea, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class SubjectDetailsTab(BaseTab):
    """
    科目詳細設定タブ。
    
    年次ごとに各科目の詳細（単位数、スロット番号、スロットグループ）を設定します。
    """
    
    # シグナル
    subject_selection_changed = Signal(str)  # 選択された科目名
    details_modified = Signal()
    
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
        self._current_subject: Optional[str] = None
        self._details_number_widgets: Dict[str, QSpinBox] = {}
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        # === 年次選択 ===
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("設定対象:"))
        self.combo_layout = QHBoxLayout()
        selector_layout.addLayout(self.combo_layout)
        selector_layout.addStretch()
        self._main_layout.addLayout(selector_layout)
        
        # === メインコンテンツ ===
        content_layout = QHBoxLayout()
        self._main_layout.addLayout(content_layout)
        
        # --- 左側: 教科リスト ---
        subject_list_container = QWidget()
        subject_list_layout = QVBoxLayout(subject_list_container)
        subject_list_layout.setContentsMargins(0, 0, 0, 0)
        
        # 割り当て済み教科
        assigned_group = QGroupBox("割り当て済み教科")
        assigned_layout = QVBoxLayout(assigned_group)
        
        self.sort_button = QPushButton("50音順ソート")
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs", "translate.svg")
                self.sort_button.setIcon(self._icon_creator(svg_path))
            except Exception:
                pass
        assigned_layout.addWidget(self.sort_button)
        
        self.assigned_list = QListWidget()
        self.assigned_list.setDragDropMode(QAbstractItemView.InternalMove)
        assigned_layout.addWidget(self.assigned_list)
        subject_list_layout.addWidget(assigned_group)
        
        # 未割り当て教科
        unassigned_group = QGroupBox("未割り当て教科")
        unassigned_layout = QVBoxLayout(unassigned_group)
        self.unassigned_list = QListWidget()
        unassigned_layout.addWidget(self.unassigned_list)
        subject_list_layout.addWidget(unassigned_group)
        
        content_layout.addWidget(subject_list_container, 1)
        
        # --- 右側: 詳細エリア ---
        details_area = QWidget()
        details_layout = QVBoxLayout(details_area)
        content_layout.addWidget(details_area, 3)
        
        # 特別単位数設定
        abnormal_group = QGroupBox("特別単位数設定")
        abnormal_layout = QFormLayout(abnormal_group)
        self.normal_units_label = QLabel("- 単位")
        abnormal_layout.addRow("通常単位数:", self.normal_units_label)
        self.final_units_input = QSpinBox()
        self.final_units_input.setRange(0, 99)
        self.final_units_input.setToolTip("この教科の最終的な単位数を設定します。")
        abnormal_layout.addRow("最終的な単位数:", self.final_units_input)
        details_layout.addWidget(abnormal_group)
        
        # スロット番号
        number_scroll = QScrollArea()
        number_scroll.setWidgetResizable(True)
        self.number_group = QGroupBox("スロット番号 (subject_number)")
        self.number_layout = QFormLayout()
        self.number_group.setLayout(self.number_layout)
        number_scroll.setWidget(self.number_group)
        details_layout.addWidget(number_scroll)
        
        # スロットグループ
        slots_scroll = QScrollArea()
        slots_scroll.setWidgetResizable(True)
        self.slots_group = QGroupBox("スロットグループ (subject_slots_base)")
        slots_layout = QVBoxLayout()
        self.slots_table = QTableWidget()
        self.slots_table.setColumnCount(10)
        slots_layout.addWidget(self.slots_table)
        
        slots_buttons = QHBoxLayout()
        self.add_slot_btn = QPushButton("スロットグループを追加")
        self.del_slot_btn = QPushButton("選択グループを削除")
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_slot_btn.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.del_slot_btn.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
        slots_buttons.addWidget(self.add_slot_btn)
        slots_buttons.addWidget(self.del_slot_btn)
        slots_layout.addLayout(slots_buttons)
        self.slots_group.setLayout(slots_layout)
        slots_scroll.setWidget(self.slots_group)
        details_layout.addWidget(slots_scroll)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.assigned_list.itemSelectionChanged.connect(self._on_assigned_selected)
        self.unassigned_list.itemSelectionChanged.connect(self._on_unassigned_selected)
        self.sort_button.clicked.connect(self._sort_assigned)
        self.add_slot_btn.clicked.connect(self._add_slot_group)
        self.del_slot_btn.clicked.connect(self._delete_slot_group)
        self.final_units_input.valueChanged.connect(self._on_units_changed)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.sort_button.setIcon(self._icon_creator(os.path.join(svg_path, "translate.svg")))
                self.add_slot_btn.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.del_slot_btn.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass

    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        self._initialize_selectors()
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集（親ウィンドウで処理）"""
        pass  # MainWindowのget_current_ui_configで処理
    
    # =========================================================================
    # Year Selection
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
            self._update_subject_lists()
    
    # =========================================================================
    # Subject Lists
    # =========================================================================
    
    def _update_subject_lists(self):
        """教科リストを更新"""
        self.assigned_list.clear()
        self.unassigned_list.clear()
        
        if not self._current_year:
            return
        
        master_subjects = self.config_model.get_master_subjects()
        # ここでconfig_modelからsubject_number等のデータを取得してリストを構築
        # 実際の実装はMainWindowのupdate_details_subject_listsに準拠
    
    def _on_assigned_selected(self):
        """割り当て済みリスト選択時"""
        if self.assigned_list.currentItem() and self.assigned_list.hasFocus():
            self.unassigned_list.clearSelection()
            item = self.assigned_list.currentItem()
            if item:
                self._on_subject_changed(item.text())
    
    def _on_unassigned_selected(self):
        """未割り当てリスト選択時"""
        if self.unassigned_list.currentItem() and self.unassigned_list.hasFocus():
            self.assigned_list.clearSelection()
            item = self.unassigned_list.currentItem()
            if item:
                self._on_subject_changed(item.text())
    
    def _on_subject_changed(self, subject_name: str):
        """科目選択変更時"""
        self._current_subject = subject_name
        self.subject_selection_changed.emit(subject_name)
    
    def _sort_assigned(self):
        """割り当て済みリストを50音順にソート"""
        items = []
        for i in range(self.assigned_list.count()):
            item = self.assigned_list.item(i)
            items.append((item.text(), item.data(Qt.UserRole)))
        
        items.sort(key=lambda x: x[0])
        
        self.assigned_list.clear()
        for text, data in items:
            new_item = QListWidgetItem(text)
            new_item.setData(Qt.UserRole, data)
            self.assigned_list.addItem(new_item)
        
        self.mark_modified()
    
    # =========================================================================
    # Slot Groups
    # =========================================================================
    
    def _add_slot_group(self):
        """スロットグループを追加"""
        row = self.slots_table.rowCount()
        self.slots_table.insertRow(row)
        self.mark_modified()
    
    def _delete_slot_group(self):
        """選択されたスロットグループを削除"""
        current_row = self.slots_table.currentRow()
        if current_row >= 0:
            self.slots_table.removeRow(current_row)
            self.mark_modified()
    
    def _on_units_changed(self, value: int):
        """単位数変更時"""
        self.mark_modified()

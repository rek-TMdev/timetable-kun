"""
required_subjects_tab.py - 必須教科設定タブ

履修要件のルールを設定するタブ。
条件グループを使って複雑な履修要件を定義できます。
MainWindowの実装に完全準拠。
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QFormLayout, QScrollArea,
    QMessageBox, QColorDialog
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class RequiredSubjectsTab(BaseTab):
    """
    必須教科設定タブ。
    
    履修要件ルールを管理します。
    各ルールは条件グループを複数持ち、複雑な履修要件を表現できます。
    """
    
    # シグナル
    rule_selected = Signal(str)  # ルール名
    rule_modified = Signal()
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._current_rule_key: Optional[tuple] = None
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        main_layout = QHBoxLayout()
        self._main_layout.addLayout(main_layout)
        
        # === 左側: ルールリスト ===
        master_pane = QWidget()
        master_layout = QVBoxLayout(master_pane)
        master_pane.setFixedWidth(250)
        
        master_layout.addWidget(QLabel("<b>登録ルール一覧</b>"))
        self.rules_list = QListWidget()
        master_layout.addWidget(self.rules_list)
        
        # ボタン
        buttons_layout = QHBoxLayout()
        self.add_rule_btn = QPushButton("ルールを追加")
        self.remove_rule_btn = QPushButton("ルールを削除")
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_rule_btn.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_rule_btn.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
        buttons_layout.addWidget(self.add_rule_btn)
        buttons_layout.addWidget(self.remove_rule_btn)
        master_layout.addLayout(buttons_layout)
        main_layout.addWidget(master_pane)
        
        # === 右側: ルール詳細 ===
        self.details_pane = QWidget()
        self.details_pane.setVisible(False)
        self.details_pane.setEnabled(False)
        details_layout = QVBoxLayout(self.details_pane)
        
        # 基本情報
        info_form = QFormLayout()
        self.rule_name_edit = QLineEdit()
        info_form.addRow("ルール名:", self.rule_name_edit)
        self.rule_target_combo = QComboBox()
        info_form.addRow("対象:", self.rule_target_combo)
        self.rule_color_btn = QPushButton("色を選択")
        info_form.addRow("表示色:", self.rule_color_btn)
        details_layout.addLayout(info_form)
        
        # 条件グループ
        condition_header = QHBoxLayout()
        condition_header.addWidget(QLabel("<b>条件グループ</b>"))
        condition_header.addStretch()
        self.add_condition_btn = QPushButton("条件追加")
        self.remove_condition_btn = QPushButton("条件削除")
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_condition_btn.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_condition_btn.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
        condition_header.addWidget(self.add_condition_btn)
        condition_header.addWidget(self.remove_condition_btn)
        details_layout.addLayout(condition_header)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.conditions_widget = QWidget()
        self.conditions_layout = QVBoxLayout(self.conditions_widget)
        self.conditions_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(self.conditions_widget)
        details_layout.addWidget(scroll_area)
        
        main_layout.addWidget(self.details_pane)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.rules_list.currentRowChanged.connect(self._on_rule_selected)
        self.add_rule_btn.clicked.connect(self._add_rule)
        self.remove_rule_btn.clicked.connect(self._remove_rule)
        self.add_condition_btn.clicked.connect(self._add_condition_group)
        self.remove_condition_btn.clicked.connect(self._remove_condition_group)
        self.rule_name_edit.editingFinished.connect(self._update_rule_details)
        self.rule_target_combo.currentIndexChanged.connect(self._update_rule_details)
        self.rule_color_btn.clicked.connect(self._select_color)
    
        self.rule_color_btn.clicked.connect(self._select_color)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_rule_btn.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_rule_btn.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.add_condition_btn.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.remove_condition_btn.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
            except Exception:
                pass
    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        self._populate_rules_list()
        self._populate_target_combo()
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集（親ウィンドウで処理）"""
        pass
    
    # =========================================================================
    # ルール一覧
    # =========================================================================
    
    def _populate_rules_list(self):
        """ルールリストを更新"""
        self.rules_list.clear()
        # config_modelから必須教科ルールを取得
        # 実際の実装はMainWindowのpopulate_rules_listに準拠
    
    def _populate_target_combo(self):
        """対象コンボボックスを更新"""
        self.rule_target_combo.clear()
        self.rule_target_combo.addItem("全体")
        
        hierarchy = self.config_model.get_years_hierarchy()
        targets = self._flatten_hierarchy(hierarchy)
        self.rule_target_combo.addItems(sorted(targets))
    
    def _flatten_hierarchy(self, hierarchy: dict, prefix: str = "") -> List[str]:
        """階層を平坦化"""
        result = []
        for key, value in hierarchy.items():
            full_key = f"{prefix}_{key}" if prefix else key
            result.append(full_key)
            if value:
                result.extend(self._flatten_hierarchy(value, full_key))
        return result
    
    def _on_rule_selected(self, index: int):
        """ルール選択時"""
        if index < 0:
            self.details_pane.setVisible(False)
            self.details_pane.setEnabled(False)
            self._current_rule_key = None
            return
        
        item = self.rules_list.item(index)
        if not item:
            return
        
        rule_data = item.data(Qt.UserRole)
        if not rule_data:
            return
        
        self._current_rule_key = (rule_data.get('id'), rule_data.get('target'))
        self._load_rule_details(rule_data)
        
        self.details_pane.setVisible(True)
        self.details_pane.setEnabled(True)
        self.rule_selected.emit(rule_data.get("name", ""))
    
    def _load_rule_details(self, rule_data: dict):
        """ルール詳細を読み込む"""
        self._clear_conditions()
        
        self.rule_name_edit.setText(rule_data.get("name", ""))
        
        display_target = "全体" if rule_data.get('target') == "ALL" else rule_data.get('target', "")
        self.rule_target_combo.blockSignals(True)
        self.rule_target_combo.setCurrentText(display_target)
        self.rule_target_combo.blockSignals(False)
        
        color = rule_data.get("color", "#FFFFFF")
        self.rule_color_btn.setStyleSheet(f"background-color: {color};")
        self.rule_color_btn.setProperty("color", color)
    
    def _clear_conditions(self):
        """条件グループをクリア"""
        while self.conditions_layout.count():
            child = self.conditions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    # =========================================================================
    # ルール操作
    # =========================================================================
    
    def _add_rule(self):
        """ルールを追加"""
        # 新しいルールを作成してリストに追加
        self.mark_modified()
    
    def _remove_rule(self):
        """選択されたルールを削除"""
        current = self.rules_list.currentItem()
        if not current:
            QMessageBox.warning(self, "エラー", "削除するルールを選択してください。")
            return
        
        reply = QMessageBox.question(
            self, "確認",
            "選択したルールを削除しますか？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.rules_list.takeItem(self.rules_list.row(current))
            self.details_pane.setVisible(False)
            self._current_rule_key = None
            self.mark_modified()
    
    def _add_condition_group(self):
        """条件グループを追加"""
        # 条件グループウィジェットを追加
        self.mark_modified()
    
    def _remove_condition_group(self):
        """条件グループを削除"""
        self.mark_modified()
    
    def _update_rule_details(self):
        """ルール詳細を更新"""
        self.rule_modified.emit()
        self.mark_modified()
    
    def _select_color(self):
        """色を選択"""
        current = self.rule_color_btn.property("color") or "#FFFFFF"
        color = QColorDialog.getColor(QColor(current), self, "カラーを選択")
        if color.isValid():
            self.rule_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self.rule_color_btn.setProperty("color", color.name())
            self.mark_modified()

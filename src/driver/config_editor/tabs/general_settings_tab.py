"""
general_settings_tab.py - その他設定タブ

アプリケーション全般の設定を管理するタブ。
組み合わせ設定、テーマ色設定、学校名などを設定できます。
MainWindowの実装に完全準拠。
"""
from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QScrollArea,
    QPushButton, QLabel, QLineEdit, QSpinBox, QCheckBox, QColorDialog
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class GeneralSettingsTab(BaseTab):
    """
    その他設定タブ。
    
    アプリケーション全般の設定を管理します：
    - 組み合わせ設定（最大数、メモリ制限）
    - テーマ・配色設定
    - その他設定（学校名、チュートリアルなど）
    """
    
    # シグナル
    settings_changed = Signal()
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._settings_widgets: Dict[str, QWidget] = {}
        self._theme_widgets: Dict[str, QPushButton] = {}
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._main_layout.addWidget(scroll)
        
        container = QWidget()
        scroll.setWidget(container)
        self.settings_layout = QVBoxLayout(container)
        self.settings_layout.setAlignment(Qt.AlignTop)
        
        # === テーマ・配色設定 ===
        self._create_theme_group()
        
        # === 組み合わせ設定 ===
        self._create_combination_group()
        
        # === その他設定 ===
        self._create_other_settings_group()
    
    def _create_theme_group(self):
        """テーマ・配色設定グループ"""
        group = QGroupBox("テーマ・配色設定")
        layout = QFormLayout(group)
        
        color_definitions = {
            "duplicate_subject": "重複教科の背景色",
            "prerequisite_missing": "前提教科不足の背景色",
            "no_together_conflict": "同時選択不可の背景色",
            "user_locked_subject": "手動固定した教科の背景色",
            "user_locked_conflict": "手動固定により競合した教科の背景色"
        }
        
        for key, label in color_definitions.items():
            row_layout = QHBoxLayout()
            
            light_btn = QPushButton("Light 色を選択")
            light_btn.setFixedWidth(120)
            light_btn.clicked.connect(lambda _, b=light_btn, k=key: self._select_color(b, k, "light"))
            
            dark_btn = QPushButton("Dark 色を選択")
            dark_btn.setFixedWidth(120)
            dark_btn.clicked.connect(lambda _, b=dark_btn, k=key: self._select_color(b, k, "dark"))
            
            row_layout.addWidget(light_btn)
            row_layout.addWidget(dark_btn)
            
            self._theme_widgets[f"{key}_light"] = light_btn
            self._theme_widgets[f"{key}_dark"] = dark_btn
            
            layout.addRow(label, row_layout)
        
        self.settings_layout.addWidget(group)
    
    def _create_combination_group(self):
        """組み合わせ設定グループ"""
        group = QGroupBox("組み合わせ設定")
        layout = QFormLayout(group)
        
        # 最大時間割数
        self.max_count_spin = QSpinBox()
        self.max_count_spin.setRange(1, 10000)
        self.max_count_spin.valueChanged.connect(self._on_setting_changed)
        layout.addRow("1ページ当たりの時間割の最大数:", self.max_count_spin)
        self._settings_widgets["SUBJECT_COMBINATION_COUNT"] = self.max_count_spin
        
        # メモリ制限
        self.memory_spin = QSpinBox()
        self.memory_spin.setRange(100, 10000)
        self.memory_spin.valueChanged.connect(self._on_setting_changed)
        layout.addRow("最大メモリ使用量 (MB):", self.memory_spin)
        self._settings_widgets["MAX_MEMORY_LIMIT"] = self.memory_spin
        
        self.settings_layout.addWidget(group)
    
    def _create_other_settings_group(self):
        """その他設定グループ"""
        group = QGroupBox("その他設定")
        layout = QFormLayout(group)
        
        # 学校名
        self.school_name_edit = QLineEdit()
        self.school_name_edit.editingFinished.connect(self._on_setting_changed)
        layout.addRow("学校名:", self.school_name_edit)
        self._settings_widgets["SCHOOL_NAME"] = self.school_name_edit
        
        # 時間割順序
        self.order_check = QCheckBox()
        self.order_check.stateChanged.connect(self._on_setting_changed)
        layout.addRow("時間割を単位数が多い順に表示:", self.order_check)
        self._settings_widgets["TIMETABLE_ORDER"] = self.order_check
        
        # チュートリアル
        self.tutorial_check = QCheckBox()
        self.tutorial_check.stateChanged.connect(self._on_setting_changed)
        layout.addRow("チュートリアルを有効化する:", self.tutorial_check)
        self._settings_widgets["RUN_TUTORIAL_ON_STARTUP"] = self.tutorial_check
        
        # マスターconfigパス
        path_layout = QHBoxLayout()
        self.master_path_edit = QLineEdit()
        self.master_path_edit.setReadOnly(True)
        path_layout.addWidget(self.master_path_edit)
        self.master_path_btn = QPushButton("設定を開く")
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs", "edit.svg")
                self.master_path_btn.setIcon(self._icon_creator(svg_path))
            except Exception:
                pass
        path_layout.addWidget(self.master_path_btn)
        layout.addRow("マスターconfigの保存位置:", path_layout)
        self._settings_widgets["MASTER_CONFIG_PATH"] = self.master_path_edit
        
        self.settings_layout.addWidget(group)
    
    def _connect_signals(self):
        """シグナルとスロットを接続（_setup_uiで接続済み）"""
        pass
    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        self._populate_general_settings()
        self._populate_theme_settings()
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集"""
        self._collect_general_settings(config_dict)
        self._collect_theme_settings(config_dict)
    
    # =========================================================================
    # 設定値の反映
    # =========================================================================
    
    def _populate_general_settings(self):
        """一般設定を反映"""
        settings = self.config_model.get_setting("GENERAL_SETTINGS", {})
        
        for key, widget in self._settings_widgets.items():
            value = settings.get(key)
            if value is None:
                continue
            
            widget.blockSignals(True)
            try:
                if isinstance(widget, QSpinBox):
                    widget.setValue(int(value))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(value))
            except (ValueError, TypeError):
                pass
            finally:
                widget.blockSignals(False)
    
    def _populate_theme_settings(self):
        """テーマ設定を反映"""
        theme_data = self.config_model.get_setting("THEME_COLORS", {})
        
        defaults = {
            "duplicate_subject": "#FFD699",
            "prerequisite_missing": "#FF9999",
            "no_together_conflict": "#7CAAFA",
            "user_locked_subject": "#D8E6FF",
            "user_locked_conflict": "#E0E0E0"
        }
        
        for key, default in defaults.items():
            light_color = theme_data.get(f"{key}_light", default)
            dark_color = theme_data.get(f"{key}_dark", default)
            
            light_btn = self._theme_widgets.get(f"{key}_light")
            dark_btn = self._theme_widgets.get(f"{key}_dark")
            
            if light_btn:
                light_btn.setStyleSheet(f"background-color: {light_color}; color: #000000;")
                light_btn.setProperty("color_val", light_color)
            
            if dark_btn:
                dark_btn.setStyleSheet(f"background-color: {dark_color}; color: #ffffff;")
                dark_btn.setProperty("color_val", dark_color)
    
    # =========================================================================
    # 設定値の収集
    # =========================================================================
    
    def _collect_general_settings(self, config_dict: Dict[str, Any]):
        """一般設定を収集"""
        if "GENERAL_SETTINGS" not in config_dict:
            config_dict["GENERAL_SETTINGS"] = {}
        
        for key, widget in self._settings_widgets.items():
            if isinstance(widget, QSpinBox):
                config_dict["GENERAL_SETTINGS"][key] = widget.value()
            elif isinstance(widget, QCheckBox):
                config_dict["GENERAL_SETTINGS"][key] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                config_dict["GENERAL_SETTINGS"][key] = widget.text()
    
    def _collect_theme_settings(self, config_dict: Dict[str, Any]):
        """テーマ設定を収集"""
        if "THEME_COLORS" not in config_dict:
            config_dict["THEME_COLORS"] = {}
        
        for key, btn in self._theme_widgets.items():
            color = btn.property("color_val")
            if color:
                config_dict["THEME_COLORS"][key] = color
    
    # =========================================================================
    # イベントハンドラ
    # =========================================================================
    
    def _on_setting_changed(self):
        """設定変更時"""
        self.settings_changed.emit()
        self.mark_modified()
    
    def _select_color(self, button: QPushButton, key: str, mode: str):
        """色を選択"""
        current = button.property("color_val") or "#FFFFFF"
        color = QColorDialog.getColor(QColor(current), self, "カラーを選択")
        
        if color.isValid():
            text_color = "#000000" if mode == "light" else "#ffffff"
            button.setStyleSheet(f"background-color: {color.name()}; color: {text_color};")
            button.setProperty("color_val", color.name())
            self.mark_modified()

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs", "edit.svg")
                self.master_path_btn.setIcon(self._icon_creator(svg_path))
            except Exception:
                pass

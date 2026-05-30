"""
alias_tab.py - 科目エイリアス設定タブ

教科名のエイリアス（別名）を管理するタブウィジェットです。
エイリアスは、ユーザーが教科名を入力する際の名寄せに使用されます。
"""
from __future__ import annotations
import os
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel

# オプショナルなインポート（インストールされていない場合は機能制限）
try:
    import pykakasi
    HAS_PYKAKASI = True
except ImportError:
    HAS_PYKAKASI = False

try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False


class AliasTab(BaseTab):
    """
    科目エイリアス設定タブ。
    
    教科ごとにエイリアス（別名）を設定できます。
    自動生成機能では、ひらがな/カタカナ/ローマ字/英語訳を生成します。
    """
    
    # シグナル
    aliases_updated = Signal()
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = "",
        alias_generator_dialog_class=None
    ):
        """
        Args:
            config_model: 設定データを管理するConfigModelインスタンス
            parent: 親ウィジェット
            icon_creator: アイコン作成関数
            base_path: アプリのベースパス
            alias_generator_dialog_class: AliasGeneratorDialogクラス（外部から注入）
        """
        self._icon_creator = icon_creator
        self._base_path = base_path
        self._alias_generator_dialog_class = alias_generator_dialog_class
        self._current_selected_subject: Optional[str] = None
        
        # 翻訳オブジェクト（遅延初期化）
        self._translator = None
        self._kks = None
        
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        # メインは水平レイアウト（左：教科リスト、右：エイリアスリスト）
        h_layout = QHBoxLayout()
        self._main_layout.addLayout(h_layout)
        
        # === 左側: 教科リスト ===
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("設定対象の教科"))
        
        self.subject_list = QListWidget()
        left_layout.addWidget(self.subject_list)
        
        h_layout.addLayout(left_layout, 1)
        
        # === 右側: エイリアスリスト ===
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("エイリアス（別名）リスト"))
        
        self.alias_list = QListWidget()
        right_layout.addWidget(self.alias_list)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")
        self.generate_button = QPushButton("自動生成")
        
        # アイコンを設定
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.edit_button.setIcon(self._icon_creator(os.path.join(svg_path, "edit.svg")))
                self.delete_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.generate_button.setIcon(self._icon_creator(os.path.join(svg_path, "glyphs.svg")))
            except Exception:
                pass
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.generate_button)
        
        right_layout.addLayout(button_layout)
        h_layout.addLayout(right_layout, 2)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.subject_list.currentRowChanged.connect(self._on_subject_selected)
        self.add_button.clicked.connect(self.add_alias)
        self.edit_button.clicked.connect(self.edit_alias)
        self.delete_button.clicked.connect(self.delete_alias)
        self.generate_button.clicked.connect(self.open_alias_generator)
    
        self.generate_button.clicked.connect(self.open_alias_generator)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.edit_button.setIcon(self._icon_creator(os.path.join(svg_path, "edit.svg")))
                self.delete_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.generate_button.setIcon(self._icon_creator(os.path.join(svg_path, "glyphs.svg")))
            except Exception:
                pass
    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        # 現在の選択を保存
        current_subject = (
            self.subject_list.currentItem().text() 
            if self.subject_list.currentItem() else None
        )
        
        self.subject_list.blockSignals(True)
        self.subject_list.clear()
        
        master_subjects = self.config_model.get_master_subjects()
        all_aliases = self.config_model.get_all_aliases()
        
        for subject in master_subjects:
            item = QListWidgetItem(subject)
            # エイリアスをアイテムのUserRoleに保存
            aliases = all_aliases.get(subject, [])
            item.setData(Qt.UserRole, aliases)
            self.subject_list.addItem(item)
        
        # 選択を復元
        if current_subject:
            items = self.subject_list.findItems(current_subject, Qt.MatchExactly)
            if items:
                self.subject_list.setCurrentItem(items[0])
        
        self.subject_list.blockSignals(False)
        
        # 選択中のエイリアスを更新
        if self.subject_list.currentItem():
            self._on_subject_selected(self.subject_list.currentRow())
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集"""
        subject_aliases = {}
        
        for i in range(self.subject_list.count()):
            item = self.subject_list.item(i)
            subject_name = item.text()
            aliases = item.data(Qt.UserRole) or []
            if aliases:
                subject_aliases[subject_name] = sorted(aliases)
        
        if subject_aliases:
            config_dict["SUBJECT_ALIASES"] = subject_aliases
        elif "SUBJECT_ALIASES" in config_dict:
            del config_dict["SUBJECT_ALIASES"]
    
    # =========================================================================
    # イベントハンドラ
    # =========================================================================
    
    def _on_subject_selected(self, index: int):
        """教科選択時のハンドラ"""
        item = self.subject_list.item(index)
        if not item:
            self._current_selected_subject = None
            self.alias_list.clear()
            return
        
        self._current_selected_subject = item.text()
        aliases = item.data(Qt.UserRole) or []
        self._update_alias_display(aliases)
    
    # =========================================================================
    # 公開メソッド
    # =========================================================================
    
    def add_alias(self):
        """エイリアスを追加"""
        if not self._current_selected_subject:
            return
        
        text, ok = QInputDialog.getText(
            self, "エイリアスの追加", "新しいエイリアスを入力してください:"
        )
        if ok and text:
            text = text.strip()
            if text:
                self.alias_list.addItem(text)
                self._save_aliases_to_item()
                self.mark_modified()
    
    def edit_alias(self):
        """選択されたエイリアスを編集"""
        selected_item = self.alias_list.currentItem()
        if not selected_item:
            return
        
        old_text = selected_item.text()
        new_text, ok = QInputDialog.getText(
            self, "エイリアスの編集", "新しいエイリアスを入力してください:",
            text=old_text
        )
        
        if ok and new_text and new_text != old_text:
            selected_item.setText(new_text.strip())
            self._save_aliases_to_item()
            self.mark_modified()
    
    def delete_alias(self):
        """選択されたエイリアスを削除"""
        selected_item = self.alias_list.currentItem()
        if selected_item:
            self.alias_list.takeItem(self.alias_list.row(selected_item))
            self._save_aliases_to_item()
            self.mark_modified()
    
    def open_alias_generator(self):
        """エイリアス自動生成ダイアログを開く"""
        master_subjects = self.config_model.get_master_subjects()
        if not master_subjects:
            QMessageBox.warning(self, "エラー", "教科マスタが空です。")
            return
        
        if not self._alias_generator_dialog_class:
            QMessageBox.warning(self, "エラー", "エイリアス生成ダイアログが設定されていません。")
            return
        
        pre_selected = []
        if self._current_selected_subject:
            pre_selected.append(self._current_selected_subject)
        
        dialog = self._alias_generator_dialog_class(master_subjects, pre_selected, self)
        if dialog.exec():
            subjects_to_process = dialog.get_selected_subjects()
            if subjects_to_process:
                self.generate_aliases(subjects_to_process)
    
    def generate_aliases(self, subjects: List[str]):
        """エイリアスを自動生成"""
        if not HAS_PYKAKASI:
            QMessageBox.warning(
                self, "エラー", 
                "pykakasiがインストールされていないため、エイリアス生成ができません。"
            )
            return
        
        # 遅延初期化
        if self._kks is None:
            self._kks = pykakasi.kakasi()
        
        if self._translator is None and HAS_TRANSLATOR:
            try:
                self._translator = GoogleTranslator(source='ja', target='en')
            except Exception:
                pass
        
        processed_count = 0
        error_subjects = []
        
        for subject in subjects:
            try:
                # 現在のエイリアスを取得
                current_aliases = set(self.config_model.get_aliases(subject))
                
                # pykakasiによる変換
                converted = self._kks.convert(subject)
                hira_alias = "".join([item['hira'] for item in converted])
                kana_alias = "".join([item['kana'] for item in converted])
                hepburn_alias = "".join([item['hepburn'] for item in converted])
                
                new_aliases = {hira_alias, kana_alias, hepburn_alias}
                
                # 翻訳による変換（オプション）
                if self._translator:
                    try:
                        clean_subject = re.sub(r'[0-9０-９A-ZＡ-ＺⅠ-Ⅲ\s]', '', subject).strip()
                        if clean_subject:
                            translated = self._translator.translate(clean_subject)
                            if translated and translated.lower() != clean_subject.lower():
                                if translated.lower() != hepburn_alias.lower():
                                    new_aliases.add(translated)
                    except Exception as e:
                        print(f"Warning: Could not translate '{subject}': {e}")
                
                # 元の教科名自身はエイリアスに含めない
                new_aliases.discard(subject)
                
                # 新しいエイリアスを追加
                final_aliases = current_aliases | new_aliases
                self.config_model.update_aliases(subject, sorted(list(final_aliases)))
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing alias for '{subject}': {e}")
                error_subjects.append(subject)
        
        # UIを更新
        self.populate()
        self.mark_modified()
        
        # 結果を表示
        if not error_subjects:
            QMessageBox.information(
                self, "成功",
                f"{processed_count}件の教科について、読み方と英単語のエイリアス生成を試みました。"
            )
        else:
            QMessageBox.warning(
                self, "一部エラー",
                f"{processed_count}件の教科は処理しましたが、以下の教科でエラーが発生しました：\n"
                f"{', '.join(error_subjects)}"
            )
    
    # =========================================================================
    # 内部メソッド
    # =========================================================================
    
    def _update_alias_display(self, aliases: List[str]):
        """エイリアスリストの表示を更新"""
        self.alias_list.clear()
        self.alias_list.addItems(sorted(aliases))
    
    def _save_aliases_to_item(self):
        """現在のエイリアスリストをアイテムのUserRoleに保存"""
        current_item = self.subject_list.currentItem()
        if not current_item:
            return
        
        aliases = [
            self.alias_list.item(i).text()
            for i in range(self.alias_list.count())
        ]
        current_item.setData(Qt.UserRole, aliases)

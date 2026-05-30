"""
master_subject_tab.py - 教科マスタ設定タブ

教科マスタ（すべてのタブで使用される教科リスト）を管理するタブウィジェットです。
"""
from __future__ import annotations
import os
import unicodedata
from typing import TYPE_CHECKING, Any, Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, 
    QLabel, QInputDialog, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon

from .base_tab import BaseTab

if TYPE_CHECKING:
    from config_model import ConfigModel


class MasterSubjectTab(BaseTab):
    """
    教科マスタ設定タブ。
    
    教科の追加、編集、削除、ソート機能を提供します。
    ここで定義された教科が他のすべてのタブで選択肢として使用されます。
    """
    
    # シグナル
    subject_added = Signal(str)      # 教科追加時（チュートリアル用）
    subject_removed = Signal(str)    # 教科削除時
    subject_renamed = Signal(str, str)  # 教科名変更時（old, new）
    subjects_reloaded = Signal()     # リスト再読み込み時
    
    def __init__(
        self, 
        config_model: "ConfigModel", 
        parent: Optional[QWidget] = None,
        icon_creator=None,
        base_path: str = ""
    ):
        """
        Args:
            config_model: 設定データを管理するConfigModelインスタンス
            parent: 親ウィジェット
            icon_creator: アイコン作成関数（MainWindowから渡される）
            base_path: アプリのベースパス（SVGアイコン用）
        """
        self._icon_creator = icon_creator
        self._base_path = base_path
        super().__init__(config_model, parent)
    
    def _setup_ui(self):
        """UIコンポーネントを構築"""
        # 説明ラベル
        description = QLabel(
            "マスターとなる教科名（ここにある教科名が他のタブで選択肢になります）"
        )
        self._main_layout.addWidget(description)
        
        # 教科リスト（ドラッグ＆ドロップで並べ替え可能）
        self.subject_list = QListWidget()
        self.subject_list.setDragDropMode(QAbstractItemView.InternalMove)
        self._main_layout.addWidget(self.subject_list)
        
        # ボタンレイアウト
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("追加")
        self.edit_button = QPushButton("編集")
        self.delete_button = QPushButton("削除")
        self.sort_button = QPushButton("50音順ソート")
        
        # アイコンを設定（icon_creatorが提供されている場合）
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.edit_button.setIcon(self._icon_creator(os.path.join(svg_path, "edit.svg")))
                self.delete_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.sort_button.setIcon(self._icon_creator(os.path.join(svg_path, "translate.svg")))
            except Exception:
                pass  # アイコンが見つからない場合は無視
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.sort_button)
        
        self._main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """シグナルとスロットを接続"""
        self.add_button.clicked.connect(self.add_subject)
        self.edit_button.clicked.connect(self.edit_subject)
        self.delete_button.clicked.connect(self.delete_subject)
        self.sort_button.clicked.connect(self.sort_subjects)
    
        self.sort_button.clicked.connect(self.sort_subjects)

    def update_icons(self):
        """アイコンを更新"""
        if self._icon_creator and self._base_path:
            try:
                svg_path = os.path.join(self._base_path, "svgs")
                self.add_button.setIcon(self._icon_creator(os.path.join(svg_path, "plus.svg")))
                self.edit_button.setIcon(self._icon_creator(os.path.join(svg_path, "edit.svg")))
                self.delete_button.setIcon(self._icon_creator(os.path.join(svg_path, "eraser.svg")))
                self.sort_button.setIcon(self._icon_creator(os.path.join(svg_path, "translate.svg")))
            except Exception:
                pass
    
    def populate(self):
        """config_modelからデータを読み込んでUIを更新"""
        self.subject_list.clear()
        subjects = self.config_model.get_master_subjects()
        sorted_subjects = sorted(list(set(subjects)))
        self.subject_list.addItems(sorted_subjects)
    
    def collect_to_config(self, config_dict: Dict[str, Any]):
        """UIの状態をconfig_dictに収集"""
        subjects = [
            self.subject_list.item(i).text() 
            for i in range(self.subject_list.count())
        ]
        config_dict["MASTER_SUBJECTS"] = sorted(list(set(subjects)))
    
    # =========================================================================
    # 公開メソッド
    # =========================================================================
    
    def add_subject(self):
        """教科を追加"""
        text, ok = QInputDialog.getText(
            self, "教科の追加", "新しい教科名を入力してください:"
        )
        if ok and text:
            text = text.strip()
            if not text:
                return
            
            # 重複チェック
            if self.subject_list.findItems(text, Qt.MatchExactly):
                QMessageBox.warning(self, "重複", "その教科名はすでに存在します。")
                return
            
            # リストに追加
            self.subject_list.addItem(text)
            self.mark_modified()
            
            # シグナル発火
            self.subject_added.emit(text)
            self.subjects_reloaded.emit()
    
    def edit_subject(self):
        """選択された教科を編集"""
        selected_item = self.subject_list.currentItem()
        if not selected_item:
            return
        
        old_text = selected_item.text()
        new_text, ok = QInputDialog.getText(
            self, "教科の編集", "新しい教科名を入力してください:", 
            text=old_text
        )
        
        if not ok or not new_text or new_text == old_text:
            return
        
        new_text = new_text.strip()
        
        # 重複チェック
        if self.subject_list.findItems(new_text, Qt.MatchExactly):
            QMessageBox.warning(self, "重複", "その教科名はすでに存在します。")
            return
        
        # ConfigModelで名前変更（関連設定も更新）
        self.config_model.rename_master_subject(old_text, new_text)
        selected_item.setText(new_text)
        self.mark_modified()
        
        # シグナル発火
        self.subject_renamed.emit(old_text, new_text)
        self.subjects_reloaded.emit()
    
    def delete_subject(self):
        """選択された教科を削除"""
        selected_item = self.subject_list.currentItem()
        if not selected_item:
            return
        
        subject_name = selected_item.text()
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self, "削除の確認",
            f"「{subject_name}」をすべての設定から削除しますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # ConfigModelで削除（関連設定からも削除）
        self.config_model.remove_master_subject(subject_name)
        self.subject_list.takeItem(self.subject_list.row(selected_item))
        self.mark_modified()
        
        # シグナル発火
        self.subject_removed.emit(subject_name)
        self.subjects_reloaded.emit()
    
    def sort_subjects(self):
        """教科リストを50音順にソート"""
        reply = QMessageBox.question(
            self, "確認",
            "教科マスタリストを50音順に並び替えますか？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # アイテムを取得してソート
        items = [
            self.subject_list.item(i).text() 
            for i in range(self.subject_list.count())
        ]
        items.sort(key=self._japanese_sort_key)
        
        # リストを更新
        self.subject_list.clear()
        self.subject_list.addItems(items)
        self.mark_modified()
    
    def get_subjects(self) -> list:
        """現在のリストから教科一覧を取得"""
        return [
            self.subject_list.item(i).text() 
            for i in range(self.subject_list.count())
        ]
    
    # =========================================================================
    # 内部メソッド
    # =========================================================================
    
    def _japanese_sort_key(self, text: str) -> str:
        """日本語ソート用のキー（NFKC正規化）"""
        return unicodedata.normalize('NFKC', text)

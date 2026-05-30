"""
undo_manager.py - Undo/Redo機能を管理するマネージャクラス

QUndoStackを使用して、操作履歴を管理し、Undo/Redo機能を提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from PySide6.QtGui import QUndoStack, QKeySequence, QAction
from PySide6.QtWidgets import QMenu
from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow


class UndoManager(QObject):
    """
    Undo/Redo機能を管理するマネージャクラス。
    
    使用方法:
    1. MainWindowでUndoManagerを初期化
    2. undo_stack.push()でコマンドを追加
    3. Ctrl+Z / Ctrl+Yでundo/redo
    """
    
    # シグナル
    can_undo_changed = Signal(bool)
    can_redo_changed = Signal(bool)
    
    def __init__(self, parent: Optional["QMainWindow"] = None):
        super().__init__(parent)
        
        self._undo_stack = QUndoStack(self)
        
        # シグナル転送
        self._undo_stack.canUndoChanged.connect(self.can_undo_changed.emit)
        self._undo_stack.canRedoChanged.connect(self.can_redo_changed.emit)
    
    @property
    def undo_stack(self) -> QUndoStack:
        """QUndoStackインスタンスを取得"""
        return self._undo_stack
    
    def create_undo_action(self, parent: QObject, prefix: str = "元に戻す") -> QAction:
        """Undoアクションを作成"""
        action = self._undo_stack.createUndoAction(parent, prefix)
        action.setShortcut(QKeySequence.Undo)
        return action
    
    def create_redo_action(self, parent: QObject, prefix: str = "やり直す") -> QAction:
        """Redoアクションを作成"""
        action = self._undo_stack.createRedoAction(parent, prefix)
        action.setShortcut(QKeySequence.Redo)
        return action
    
    def setup_menu(self, menu: QMenu, parent: QObject) -> tuple:
        """
        メニューにUndo/Redoアクションを追加。
        
        Returns:
            (undo_action, redo_action) のタプル
        """
        undo_action = self.create_undo_action(parent)
        redo_action = self.create_redo_action(parent)
        
        menu.addAction(undo_action)
        menu.addAction(redo_action)
        
        return undo_action, redo_action
    
    def push(self, command):
        """コマンドをスタックにプッシュ"""
        self._undo_stack.push(command)
    
    def undo(self):
        """直前の操作を元に戻す"""
        if self._undo_stack.canUndo():
            self._undo_stack.undo()
    
    def redo(self):
        """操作をやり直す"""
        if self._undo_stack.canRedo():
            self._undo_stack.redo()
    
    def clear(self):
        """履歴をクリア"""
        self._undo_stack.clear()
    
    def set_clean(self):
        """現在の状態をクリーン状態としてマーク"""
        self._undo_stack.setClean()
    
    def is_clean(self) -> bool:
        """クリーン状態かどうか"""
        return self._undo_stack.isClean()
    
    def can_undo(self) -> bool:
        """Undoが可能か"""
        return self._undo_stack.canUndo()
    
    def can_redo(self) -> bool:
        """Redoが可能か"""
        return self._undo_stack.canRedo()
    
    def undo_text(self) -> str:
        """Undoテキストを取得"""
        return self._undo_stack.undoText()
    
    def redo_text(self) -> str:
        """Redoテキストを取得"""
        return self._undo_stack.redoText()

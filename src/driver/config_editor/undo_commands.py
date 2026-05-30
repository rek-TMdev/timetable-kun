"""
undo_commands.py - Undo/Redo機能のためのコマンドクラス

QUndoCommandを使用して、各操作の元に戻す/やり直し機能を提供します。
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from PySide6.QtGui import QUndoCommand

if TYPE_CHECKING:
    from config_model import ConfigModel


class AddSubjectCommand(QUndoCommand):
    """教科追加コマンド"""
    
    def __init__(self, model: "ConfigModel", subject: str):
        super().__init__(f"教科 '{subject}' を追加")
        self.model = model
        self.subject = subject
    
    def redo(self):
        self.model.add_master_subject(self.subject)
    
    def undo(self):
        self.model.remove_master_subject(self.subject)


class RemoveSubjectCommand(QUndoCommand):
    """教科削除コマンド"""
    
    def __init__(self, model: "ConfigModel", subject: str):
        super().__init__(f"教科 '{subject}' を削除")
        self.model = model
        self.subject = subject
        # 削除前の関連データを保存
        self.aliases = model.get_aliases(subject)
    
    def redo(self):
        self.model.remove_master_subject(self.subject)
    
    def undo(self):
        self.model.add_master_subject(self.subject)
        # エイリアスを復元
        if self.aliases:
            self.model.update_aliases(self.subject, self.aliases)


class RenameSubjectCommand(QUndoCommand):
    """教科名変更コマンド"""
    
    def __init__(self, model: "ConfigModel", old_name: str, new_name: str):
        super().__init__(f"教科 '{old_name}' → '{new_name}'")
        self.model = model
        self.old_name = old_name
        self.new_name = new_name
    
    def redo(self):
        self.model.rename_master_subject(self.old_name, self.new_name)
    
    def undo(self):
        self.model.rename_master_subject(self.new_name, self.old_name)


class UpdateAliasesCommand(QUndoCommand):
    """エイリアス更新コマンド"""
    
    def __init__(self, model: "ConfigModel", subject: str, old_aliases: List[str], new_aliases: List[str]):
        super().__init__(f"'{subject}' のエイリアスを更新")
        self.model = model
        self.subject = subject
        self.old_aliases = old_aliases
        self.new_aliases = new_aliases
    
    def redo(self):
        self.model.update_aliases(self.subject, self.new_aliases)
    
    def undo(self):
        self.model.update_aliases(self.subject, self.old_aliases)


class AddAliasCommand(QUndoCommand):
    """エイリアス追加コマンド"""
    
    def __init__(self, model: "ConfigModel", subject: str, alias: str):
        super().__init__(f"'{subject}' にエイリアス '{alias}' を追加")
        self.model = model
        self.subject = subject
        self.alias = alias
    
    def redo(self):
        self.model.add_alias(self.subject, self.alias)
    
    def undo(self):
        self.model.remove_alias(self.subject, self.alias)


class RemoveAliasCommand(QUndoCommand):
    """エイリアス削除コマンド"""
    
    def __init__(self, model: "ConfigModel", subject: str, alias: str):
        super().__init__(f"'{subject}' からエイリアス '{alias}' を削除")
        self.model = model
        self.subject = subject
        self.alias = alias
    
    def redo(self):
        self.model.remove_alias(self.subject, self.alias)
    
    def undo(self):
        self.model.add_alias(self.subject, self.alias)


class UpdateSettingCommand(QUndoCommand):
    """汎用設定更新コマンド"""
    
    def __init__(self, model: "ConfigModel", key: str, old_value: Any, new_value: Any):
        super().__init__(f"設定 '{key}' を更新")
        self.model = model
        self.key = key
        self.old_value = old_value
        self.new_value = new_value
    
    def redo(self):
        self.model.set_setting(self.key, self.new_value)
    
    def undo(self):
        self.model.set_setting(self.key, self.old_value)


class UpdatePrerequisiteCommand(QUndoCommand):
    """前提教科更新コマンド"""
    
    def __init__(self, model: "ConfigModel", subject: str, old_prereqs: List[str], new_prereqs: List[str]):
        super().__init__(f"'{subject}' の前提教科を更新")
        self.model = model
        self.subject = subject
        self.old_prereqs = old_prereqs
        self.new_prereqs = new_prereqs
    
    def redo(self):
        self.model.update_prerequisites(self.subject, self.new_prereqs)
    
    def undo(self):
        self.model.update_prerequisites(self.subject, self.old_prereqs)


class UpdateNoTogetherCommand(QUndoCommand):
    """同時選択不可グループ更新コマンド"""
    
    def __init__(self, model: "ConfigModel", old_groups: List[List[str]], new_groups: List[List[str]]):
        super().__init__("同時選択不可グループを更新")
        self.model = model
        self.old_groups = old_groups
        self.new_groups = new_groups
    
    def redo(self):
        self.model.update_no_together_groups(self.new_groups)
    
    def undo(self):
        self.model.update_no_together_groups(self.old_groups)


class UpdateYearsHierarchyCommand(QUndoCommand):
    """年次階層更新コマンド"""
    
    def __init__(self, model: "ConfigModel", old_hierarchy: Dict, new_hierarchy: Dict):
        super().__init__("年次階層を更新")
        self.model = model
        self.old_hierarchy = old_hierarchy
        self.new_hierarchy = new_hierarchy
    
    def redo(self):
        self.model.update_years_hierarchy(self.new_hierarchy)
    
    def undo(self):
        self.model.update_years_hierarchy(self.old_hierarchy)

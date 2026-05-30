"""
config_model.py - 設定データを管理するモデルクラス

MVC/MVVMパターンに基づき、UIとデータ操作を分離するためのモデル層を提供します。
このクラスはconfig_dataを内部で保持し、データへの安全なアクセスメソッドを提供します。
"""
from __future__ import annotations
import json
import copy
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import QObject, Signal


class ConfigModel(QObject):
    """
    設定データを管理するモデルクラス。
    
    UIクラスはこのモデルを通じてデータを操作し、データの整合性を保ちます。
    変更があった場合はシグナルを発火し、UIに通知します。
    """
    
    # データ変更シグナル
    data_changed = Signal()
    master_subjects_changed = Signal()
    aliases_changed = Signal()
    hierarchy_changed = Signal()
    
    # デフォルト設定値
    DEFAULT_CONFIG: Dict[str, Any] = {
        "SUBJECT_COMBINATION_COUNT": 20,
        "MORE_SUBJECT_COMBINATION": 10,
        "MIN_SUBJECT_COUNT": 2,
        "MAX_SUBJECT_COUNT": 10,
        "MIN_SUBJECT_COUNT_UNITS": 9,
        "MAX_SUBJECT_COUNT_UNITS": 30,
        "ACTIVE_MIN_SUBJECT": True,
        "ACTIVE_MAX_SUBJECT": False,
        "ACTIVE_FILTER_SUBJECT": True,
        "ACTIVE_FILTER_SUBJECT_AMOUNT": False,
        "ACTIVE_MIN_SUBJECT_UNITS": True,
        "ACTIVE_MAX_SUBJECT_UNITS": False,
        "ACTIVE_FILTER_SUBJECT_UNITS": False,
        "MAX_MEMORY_LIMIT": 1000,
        "INCLUDE_FIXED": False,
        "TIMETABLE_ORDER": True,
        "APP_FONT_SIZE": 11,
        "TUTORIAL": True,
        "RUN_TUTORIAL_ON_STARTUP": True,
        "ART_SUBJECT": 0,
        "EDITOR_FONT_SIZE": 10,
        "MASTER_SUBJECTS": [],
        "SUBJECT_ALIASES": {},
        "PREREQUISITE_SUBJECTS": {},
        "NO_TOGETHER_SUBJECTS": [],
        "YEARS_MESSAGE": [],
        "YEARS_HIERARCHY": {},
    }
    
    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._data: Dict[str, Any] = copy.deepcopy(self.DEFAULT_CONFIG)
        self._is_modified: bool = False
        self._file_path: Optional[Path] = None
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def is_modified(self) -> bool:
        """未保存の変更があるか"""
        return self._is_modified
    
    @property
    def file_path(self) -> Optional[Path]:
        """現在のファイルパス"""
        return self._file_path
    
    @file_path.setter
    def file_path(self, value: Optional[Path]):
        self._file_path = value
    
    @property
    def raw_data(self) -> Dict[str, Any]:
        """
        生のデータ辞書へのアクセス（読み取り専用のコピー）。
        直接編集が必要な場合のみ使用してください。
        """
        return copy.deepcopy(self._data)
    
    # =========================================================================
    # Data Persistence
    # =========================================================================
    
    def load_from_file(self, file_path: str | Path) -> bool:
        """
        ファイルから設定を読み込む。
        
        Args:
            file_path: 読み込むJSONファイルのパス
            
        Returns:
            成功した場合True
        """
        path = Path(file_path)
        if not path.exists():
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # デフォルト値をベースにマージ
            self._data = copy.deepcopy(self.DEFAULT_CONFIG)
            self._data.update(loaded_data)
            
            self._file_path = path
            self._is_modified = False
            self.data_changed.emit()
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config file: {e}")
            return False
    
    def load_from_dict(self, data: Dict[str, Any]):
        """
        辞書からデータを読み込む（チュートリアルモード等で使用）。
        
        Args:
            data: 設定データの辞書
        """
        self._data = copy.deepcopy(self.DEFAULT_CONFIG)
        self._data.update(copy.deepcopy(data))
        self._is_modified = False
        self.data_changed.emit()
    
    def save_to_file(self, file_path: Optional[str | Path] = None) -> bool:
        """
        ファイルに設定を保存する。
        
        Args:
            file_path: 保存先のパス（省略時は現在のfile_pathを使用）
            
        Returns:
            成功した場合True
        """
        path = Path(file_path) if file_path else self._file_path
        if path is None:
            return False
        
        try:
            # 更新日時を設定
            self._data["LAST_UPDATE_DAY"] = datetime.now().strftime("%Y/%m/%d/%H:%M")
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            
            self._file_path = path
            self._is_modified = False
            return True
            
        except IOError as e:
            print(f"Error saving config file: {e}")
            return False
    
    def mark_modified(self):
        """データが変更されたことを記録する"""
        self._is_modified = True
        self.data_changed.emit()
    
    def update_data(self, data: Dict[str, Any]):
        """
        既存データを新しいデータで更新する（MainWindowとの互換性のため）。
        
        Args:
            data: 更新するデータ辞書
        """
        self._data = copy.deepcopy(self.DEFAULT_CONFIG)
        self._data.update(copy.deepcopy(data))
        self._is_modified = False
        self.data_changed.emit()
    
    # =========================================================================
    # Master Subjects
    # =========================================================================
    
    def get_master_subjects(self) -> List[str]:
        """教科マスタリストを取得"""
        return list(self._data.get("MASTER_SUBJECTS", []))
    
    def add_master_subject(self, subject: str) -> bool:
        """
        教科を追加（重複チェック付き）。
        
        Args:
            subject: 追加する教科名
            
        Returns:
            追加成功した場合True、重複の場合False
        """
        subjects = self._data.setdefault("MASTER_SUBJECTS", [])
        if subject in subjects:
            return False
        
        subjects.append(subject)
        self._is_modified = True
        self.master_subjects_changed.emit()
        self.data_changed.emit()
        return True
    
    def remove_master_subject(self, subject: str) -> bool:
        """
        教科を削除（関連設定からも削除）。
        
        Args:
            subject: 削除する教科名
            
        Returns:
            削除成功した場合True
        """
        subjects = self._data.get("MASTER_SUBJECTS", [])
        if subject not in subjects:
            return False
        
        subjects.remove(subject)
        
        # 関連設定からも削除
        self._remove_subject_from_aliases(subject)
        self._remove_subject_from_prerequisites(subject)
        self._remove_subject_from_no_together(subject)
        self._remove_subject_from_required_subjects(subject)
        self._remove_subject_from_selected_art(subject)
        
        self._is_modified = True
        self.master_subjects_changed.emit()
        self.data_changed.emit()
        return True
    
    def rename_master_subject(self, old_name: str, new_name: str) -> bool:
        """
        教科名を変更（全ての参照を更新）。
        
        Args:
            old_name: 現在の教科名
            new_name: 新しい教科名
            
        Returns:
            変更成功した場合True
        """
        subjects = self._data.get("MASTER_SUBJECTS", [])
        if old_name not in subjects or new_name in subjects:
            return False
        
        # マスターリストを更新
        idx = subjects.index(old_name)
        subjects[idx] = new_name
        
        # 関連設定を更新
        self._rename_in_aliases(old_name, new_name)
        self._rename_in_prerequisites(old_name, new_name)
        self._rename_in_no_together(old_name, new_name)
        self._rename_in_required_subjects(old_name, new_name)
        self._rename_in_selected_art(old_name, new_name)
        self._rename_in_subject_details(old_name, new_name)
        
        self._is_modified = True
        self.master_subjects_changed.emit()
        self.data_changed.emit()
        return True
    
    # =========================================================================
    # Aliases
    # =========================================================================
    
    def get_aliases(self, subject: str) -> List[str]:
        """指定教科のエイリアスを取得"""
        aliases = self._data.get("SUBJECT_ALIASES", {})
        return list(aliases.get(subject, []))
    
    def get_all_aliases(self) -> Dict[str, List[str]]:
        """全てのエイリアスを取得"""
        return copy.deepcopy(self._data.get("SUBJECT_ALIASES", {}))
    
    def update_aliases(self, subject: str, aliases: List[str]):
        """
        エイリアスを更新。
        
        Args:
            subject: 教科名
            aliases: 新しいエイリアスリスト
        """
        aliases_dict = self._data.setdefault("SUBJECT_ALIASES", {})
        if aliases:
            aliases_dict[subject] = list(aliases)
        elif subject in aliases_dict:
            del aliases_dict[subject]
        
        self._is_modified = True
        self.aliases_changed.emit()
        self.data_changed.emit()
    
    def add_alias(self, subject: str, alias: str) -> bool:
        """エイリアスを追加"""
        aliases = self._data.setdefault("SUBJECT_ALIASES", {}).setdefault(subject, [])
        if alias in aliases:
            return False
        aliases.append(alias)
        self._is_modified = True
        self.aliases_changed.emit()
        self.data_changed.emit()
        return True
    
    def remove_alias(self, subject: str, alias: str) -> bool:
        """エイリアスを削除"""
        aliases_dict = self._data.get("SUBJECT_ALIASES", {})
        if subject not in aliases_dict or alias not in aliases_dict[subject]:
            return False
        aliases_dict[subject].remove(alias)
        if not aliases_dict[subject]:
            del aliases_dict[subject]
        self._is_modified = True
        self.aliases_changed.emit()
        self.data_changed.emit()
        return True
    
    # =========================================================================
    # Years Hierarchy
    # =========================================================================
    
    def get_years_hierarchy(self) -> Dict:
        """年次階層を取得"""
        return copy.deepcopy(self._data.get("YEARS_HIERARCHY", {}))
    
    def get_years_message(self) -> List[str]:
        """階層選択ダイアログのメッセージリストを取得"""
        return list(self._data.get("YEARS_MESSAGE", []))
    
    def get_all_leaf_years(self) -> List[str]:
        """
        全ての末端年次（leaf nodes）を取得。
        
        Returns:
            末端年次の名前リスト
        """
        hierarchy = self._data.get("YEARS_HIERARCHY", {})
        return self._collect_leaf_years(hierarchy)
    
    def _collect_leaf_years(self, node: Dict, path_prefix: str = "") -> List[str]:
        """再帰的にleaf年次を収集"""
        leaves = []
        for key, children in node.items():
            current_path = f"{path_prefix}/{key}" if path_prefix else key
            if not children:  # leaf node
                leaves.append(key)
            else:
                leaves.extend(self._collect_leaf_years(children, current_path))
        return leaves
    
    def update_years_hierarchy(self, hierarchy: Dict):
        """年次階層を更新"""
        self._data["YEARS_HIERARCHY"] = copy.deepcopy(hierarchy)
        self._is_modified = True
        self.hierarchy_changed.emit()
        self.data_changed.emit()
    
    def get_hierarchy_anchors(self) -> List[str]:
        """階層アンカーのリストを取得"""
        return list(self._data.get("HIERARCHY_ANCHORS", []))
    
    def update_hierarchy_anchors(self, anchors: List[str]):
        """階層アンカーのリストを更新"""
        self._data["HIERARCHY_ANCHORS"] = list(anchors)
        self._is_modified = True
        self.data_changed.emit()
    
    def update_years_message(self, messages: List[str]):
        """階層選択ダイアログのメッセージを更新"""
        self._data["YEARS_MESSAGE"] = list(messages)
        self._is_modified = True
        self.data_changed.emit()
    
    # =========================================================================
    # Prerequisites
    # =========================================================================
    
    def get_prerequisites(self) -> Dict[str, List[str]]:
        """前提教科設定を取得"""
        return copy.deepcopy(self._data.get("PREREQUISITE_SUBJECTS", {}))
    
    def update_prerequisites(self, subject: str, prerequisites: List[str]):
        """前提教科を更新"""
        prereq_dict = self._data.setdefault("PREREQUISITE_SUBJECTS", {})
        if prerequisites:
            prereq_dict[subject] = list(prerequisites)
        elif subject in prereq_dict:
            del prereq_dict[subject]
        self._is_modified = True
        self.data_changed.emit()
    
    # =========================================================================
    # No Together Subjects
    # =========================================================================
    
    def get_no_together_groups(self) -> List[List[str]]:
        """同時履修不可グループを取得"""
        return copy.deepcopy(self._data.get("NO_TOGETHER_SUBJECTS", []))
    
    def update_no_together_groups(self, groups: List[List[str]]):
        """同時履修不可グループを更新"""
        self._data["NO_TOGETHER_SUBJECTS"] = copy.deepcopy(groups)
        self._is_modified = True
        self.data_changed.emit()
    
    # =========================================================================
    # General Settings
    # =========================================================================
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """任意の設定値を取得"""
        return self._data.get(key, default)
    
    def set_setting(self, key: str, value: Any):
        """任意の設定値を設定"""
        self._data[key] = value
        self._is_modified = True
        self.data_changed.emit()
    
    def get_settings(self, keys: List[str]) -> Dict[str, Any]:
        """複数の設定値を一括取得"""
        return {key: self._data.get(key) for key in keys}
    
    def update_settings(self, settings: Dict[str, Any]):
        """複数の設定値を一括更新"""
        self._data.update(settings)
        self._is_modified = True
        self.data_changed.emit()
    
    # =========================================================================
    # Table Layout (year-specific)
    # =========================================================================
    
    def get_table_layout(self, year: str) -> List[List[str]]:
        """指定年次のテーブルレイアウトを取得"""
        key = f"table_layout{year}"
        return copy.deepcopy(self._data.get(key, []))
    
    def update_table_layout(self, year: str, layout: List[List[str]]):
        """テーブルレイアウトを更新"""
        key = f"table_layout{year}"
        self._data[key] = copy.deepcopy(layout)
        self._is_modified = True
        self.data_changed.emit()
    
    def get_fixed_slots(self, year: str) -> Dict[str, str]:
        """固定スロットを取得"""
        key = f"FIXED_SLOTS{year}"
        return copy.deepcopy(self._data.get(key, {}))
    
    def update_fixed_slots(self, year: str, slots: Dict[str, str]):
        """固定スロットを更新"""
        key = f"FIXED_SLOTS{year}"
        self._data[key] = copy.deepcopy(slots)
        self._is_modified = True
        self.data_changed.emit()
    
    # =========================================================================
    # Subject Details (year-specific)
    # =========================================================================
    
    def get_subject_details(self, year: str) -> Dict[str, Dict]:
        """指定年次の科目詳細を取得"""
        key = f"SUBJECT_DETAILS_{year}"
        return copy.deepcopy(self._data.get(key, {}))
    
    def update_subject_details(self, year: str, details: Dict[str, Dict]):
        """科目詳細を更新"""
        key = f"SUBJECT_DETAILS_{year}"
        self._data[key] = copy.deepcopy(details)
        self._is_modified = True
        self.data_changed.emit()
    
    # =========================================================================
    # Required Subjects
    # =========================================================================
    
    def get_required_subjects_rules(self) -> Dict[str, Dict]:
        """必修教科ルールを取得"""
        rules = {}
        for key in self._data:
            if key.startswith("REQUIRED_SUBJECTS_"):
                rules[key] = copy.deepcopy(self._data[key])
        return rules
    
    def update_required_subjects_rule(self, rule_key: str, rule_data: Dict):
        """必修教科ルールを更新"""
        self._data[rule_key] = copy.deepcopy(rule_data)
        self._is_modified = True
        self.data_changed.emit()
    
    def remove_required_subjects_rule(self, rule_key: str) -> bool:
        """必修教科ルールを削除"""
        if rule_key in self._data:
            del self._data[rule_key]
            self._is_modified = True
            self.data_changed.emit()
            return True
        return False
    
    # =========================================================================
    # Private Helper Methods - Remove subject from related settings
    # =========================================================================
    
    def _remove_subject_from_aliases(self, subject: str):
        """エイリアスから教科を削除"""
        aliases = self._data.get("SUBJECT_ALIASES", {})
        if subject in aliases:
            del aliases[subject]
    
    def _remove_subject_from_prerequisites(self, subject: str):
        """前提教科設定から教科を削除"""
        prereqs = self._data.get("PREREQUISITE_SUBJECTS", {})
        if subject in prereqs:
            del prereqs[subject]
        for key in list(prereqs.keys()):
            if subject in prereqs[key]:
                prereqs[key].remove(subject)
    
    def _remove_subject_from_no_together(self, subject: str):
        """同時履修不可グループから教科を削除"""
        groups = self._data.get("NO_TOGETHER_SUBJECTS", [])
        for group in groups:
            if subject in group:
                group.remove(subject)
        # 空のグループを削除
        self._data["NO_TOGETHER_SUBJECTS"] = [g for g in groups if len(g) >= 2]
    
    def _remove_subject_from_required_subjects(self, subject: str):
        """必修教科設定から教科を削除"""
        for key in list(self._data.keys()):
            if key.startswith("REQUIRED_SUBJECTS_"):
                rule = self._data[key]
                if "conditions" in rule:
                    for cond in rule["conditions"]:
                        if "subjects" in cond and subject in cond["subjects"]:
                            cond["subjects"].remove(subject)
    
    def _remove_subject_from_selected_art(self, subject: str):
        """特別選択教科から削除"""
        selected = self._data.get("SELECTED_ART_SUBJECT", [])
        if subject in selected:
            selected.remove(subject)
    
    # =========================================================================
    # Private Helper Methods - Rename subject in related settings
    # =========================================================================
    
    def _rename_in_aliases(self, old_name: str, new_name: str):
        """エイリアス設定で教科名を変更"""
        aliases = self._data.get("SUBJECT_ALIASES", {})
        if old_name in aliases:
            aliases[new_name] = aliases.pop(old_name)
    
    def _rename_in_prerequisites(self, old_name: str, new_name: str):
        """前提教科設定で教科名を変更"""
        prereqs = self._data.get("PREREQUISITE_SUBJECTS", {})
        if old_name in prereqs:
            prereqs[new_name] = prereqs.pop(old_name)
        for key in prereqs:
            if old_name in prereqs[key]:
                prereqs[key] = [new_name if x == old_name else x for x in prereqs[key]]
    
    def _rename_in_no_together(self, old_name: str, new_name: str):
        """同時履修不可グループで教科名を変更"""
        groups = self._data.get("NO_TOGETHER_SUBJECTS", [])
        for group in groups:
            for i, subj in enumerate(group):
                if subj == old_name:
                    group[i] = new_name
    
    def _rename_in_required_subjects(self, old_name: str, new_name: str):
        """必修教科設定で教科名を変更"""
        for key in self._data:
            if key.startswith("REQUIRED_SUBJECTS_"):
                rule = self._data[key]
                if "conditions" in rule:
                    for cond in rule["conditions"]:
                        if "subjects" in cond:
                            cond["subjects"] = [
                                new_name if x == old_name else x 
                                for x in cond["subjects"]
                            ]
    
    def _rename_in_selected_art(self, old_name: str, new_name: str):
        """特別選択教科で教科名を変更"""
        selected = self._data.get("SELECTED_ART_SUBJECT", [])
        for i, subj in enumerate(selected):
            if subj == old_name:
                selected[i] = new_name
    
    def _rename_in_subject_details(self, old_name: str, new_name: str):
        """科目詳細設定で教科名を変更"""
        for key in self._data:
            if key.startswith("SUBJECT_DETAILS_"):
                details = self._data[key]
                if old_name in details:
                    details[new_name] = details.pop(old_name)

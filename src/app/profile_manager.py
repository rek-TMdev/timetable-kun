"""
ProfileManager - プロファイルデータを管理するクラス

Application クラスからプロファイル管理の責務を分離するために作成。
プロファイルの作成、削除、複製、切り替え時のデータ操作を担当します。

Note:
    タブウィジェットやダイアログなどのUI操作はApplicationに残し、
    このクラスはプロファイルデータの管理ロジックのみを行います。
"""
import copy
from typing import Any, Optional


class ProfileManager:
    """
    プロファイルデータの管理を行うクラス。
    
    責務:
    - プロファイルの作成・削除・複製
    - プロファイル順序の管理
    - プロファイル間のデータコピー
    - アクティブプロファイルの追跡
    
    Note:
        このクラスはUIに依存しない純粋なデータ管理ロジックを提供します。
        タブの追加・削除などのUI操作はApplicationクラスが担当します。
    """
    
    DEFAULT_PROFILE_NAME = "Default"
    
    def __init__(self, year_data: dict, years: list):
        """
        ProfileManagerを初期化します。
        
        Args:
            year_data: 学年ごとのデータ辞書への参照
            years: 学年のリスト
        """
        self.year_data = year_data
        self.years = years
        self.art_subject_selections: dict = {}
        self.current_profile_name: str = self.DEFAULT_PROFILE_NAME
    
    def initialize_default_profile(self) -> None:
        """
        Defaultプロファイルが存在しない場合に初期化します。
        """
        if not self.year_data.get(self.years[0], {}).get("saved_profiles"):
            for year in self.years:
                if "saved_profiles" not in self.year_data[year]:
                    self.year_data[year]["saved_profiles"] = {}
                self.year_data[year]["saved_profiles"][self.DEFAULT_PROFILE_NAME] = {}
            self.art_subject_selections[self.DEFAULT_PROFILE_NAME] = []
    
    def get_all_profile_names(self) -> list[str]:
        """
        すべてのプロファイル名を取得します。
        
        Returns:
            プロファイル名のリスト
        """
        if self.years and self.years[0] in self.year_data:
            return list(self.year_data[self.years[0]].get("saved_profiles", {}).keys())
        return [self.DEFAULT_PROFILE_NAME]
    
    def get_ordered_profile_names(self, saved_order: list[str]) -> list[str]:
        """
        保存された順序に基づいたプロファイル名リストを取得します。
        
        存在しないプロファイルは除外し、新しいプロファイルは末尾に追加します。
        
        Args:
            saved_order: 保存されていた順序リスト
            
        Returns:
            整理された順序のプロファイル名リスト
        """
        all_profiles = self.get_all_profile_names()
        
        # 存在するプロファイルのみをフィルタリング
        ordered = [p for p in saved_order if p in all_profiles]
        
        # 新しいプロファイルを末尾に追加
        for name in all_profiles:
            if name not in ordered:
                ordered.append(name)
        
        return ordered
    
    def create_profile(self, name: str) -> bool:
        """
        新しいプロファイルを作成します。
        
        Args:
            name: プロファイル名
            
        Returns:
            作成に成功した場合はTrue、既に存在する場合はFalse
        """
        all_profiles = self.get_all_profile_names()
        if name in all_profiles:
            return False
        
        for year in self.years:
            self.year_data[year]["saved_profiles"][name] = {}
            self.year_data[year].setdefault("profile_lock_settings", {})[name] = {}
            self.year_data[year].setdefault("profile_all_slots", {})[name] = []
            self.year_data[year].setdefault("profile_ui_states", {})[name] = {
                "checked": [],
                "important": [],
                "prefixes": {}
            }
        
        self.art_subject_selections[name] = []
        return True
    
    def delete_profile(self, name: str) -> bool:
        """
        プロファイルを削除します。
        
        Args:
            name: 削除するプロファイル名
            
        Returns:
            削除に成功した場合はTrue、Defaultプロファイルは削除できないためFalse
        """
        if name == self.DEFAULT_PROFILE_NAME:
            return False
        
        for year in self.years:
            if name in self.year_data[year].get("saved_profiles", {}):
                del self.year_data[year]["saved_profiles"][name]
            if name in self.year_data[year].get("profile_lock_settings", {}):
                del self.year_data[year]["profile_lock_settings"][name]
            if name in self.year_data[year].get("profile_all_slots", {}):
                del self.year_data[year]["profile_all_slots"][name]
            if name in self.year_data[year].get("profile_ui_states", {}):
                del self.year_data[year]["profile_ui_states"][name]
        
        if name in self.art_subject_selections:
            del self.art_subject_selections[name]
        
        return True
    
    def duplicate_profile(self, original_name: str, new_name: str = None) -> str:
        """
        プロファイルを複製します。
        
        Args:
            original_name: 元のプロファイル名
            new_name: 新しいプロファイル名（省略時は自動生成）
            
        Returns:
            作成されたプロファイル名
        """
        if new_name is None:
            new_name = self._generate_copy_name(original_name)
        
        for year in self.years:
            # 時間割データをコピー
            original_timetable = self.year_data[year].get("saved_profiles", {}).get(original_name, {})
            self.year_data[year]["saved_profiles"][new_name] = copy.copy(original_timetable)
            
            # ロック設定をコピー
            original_locks = self.year_data[year].get("profile_lock_settings", {}).get(original_name, {})
            self.year_data[year].setdefault("profile_lock_settings", {})[new_name] = copy.copy(original_locks)
            
            # スロット一覧をコピー
            original_slots = self.year_data[year].get("profile_all_slots", {}).get(original_name, [])
            self.year_data[year].setdefault("profile_all_slots", {})[new_name] = original_slots[:]
            
            # UI状態をコピー
            original_ui = self.year_data[year].get("profile_ui_states", {}).get(
                original_name, {"checked": [], "important": [], "prefixes": {}}
            )
            self.year_data[year].setdefault("profile_ui_states", {})[new_name] = {
                "checked": list(original_ui.get("checked", [])),
                "important": list(original_ui.get("important", [])),
                "prefixes": copy.copy(original_ui.get("prefixes", {}))
            }
        
        # 芸術科目選択をコピー
        original_art = self.art_subject_selections.get(original_name, [])
        self.art_subject_selections[new_name] = original_art[:]
        
        return new_name
    
    def rename_profile(self, old_name: str, new_name: str) -> bool:
        """
        プロファイル名を変更します。
        
        Args:
            old_name: 変更前の名前
            new_name: 変更後の名前
            
        Returns:
            変更に成功した場合はTrue
        """
        if old_name == self.DEFAULT_PROFILE_NAME:
            return False
        
        if new_name in self.get_all_profile_names():
            return False
        
        # データを新しい名前でコピーして古い名前を削除
        self.duplicate_profile(old_name, new_name)
        self.delete_profile(old_name)
        
        return True
    
    def set_active_profile(self, name: str) -> None:
        """
        アクティブプロファイルを設定します。
        
        Args:
            name: アクティブにするプロファイル名
        """
        self.current_profile_name = name
        for year in self.years:
            self.year_data[year]["active_profile_name"] = name
    
    def get_profile_timetable(self, profile_name: str, year: str) -> dict:
        """
        指定されたプロファイルと学年の時間割を取得します。
        
        Args:
            profile_name: プロファイル名
            year: 学年
            
        Returns:
            時間割の辞書（スロット名: 教科名）
        """
        return self.year_data.get(year, {}).get("saved_profiles", {}).get(profile_name, {})
    
    def set_profile_timetable(self, profile_name: str, year: str, timetable: dict) -> None:
        """
        指定されたプロファイルと学年の時間割を設定します。
        
        Args:
            profile_name: プロファイル名
            year: 学年
            timetable: 時間割の辞書
        """
        if year in self.year_data:
            self.year_data[year].setdefault("saved_profiles", {})[profile_name] = timetable
    
    def _generate_copy_name(self, original_name: str) -> str:
        """
        コピー用の新しい名前を生成します。
        
        Args:
            original_name: 元の名前
            
        Returns:
            重複しない新しい名前
        """
        base_name = f"{original_name}のコピー"
        new_name = base_name
        i = 1
        all_profiles = self.get_all_profile_names()
        
        while new_name in all_profiles:
            i += 1
            new_name = f"{base_name} {i}"
        
        return new_name

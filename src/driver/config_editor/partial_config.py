"""
partial_config.py - 部分設定のインポート/エクスポート機能

設定の一部（教科マスタのみ、エイリアスのみなど）を
インポート/エクスポートする機能を提供します。
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class ConfigSection(Enum):
    """設定のセクションを表す列挙型"""
    MASTER_SUBJECTS = "MASTER_SUBJECTS"
    ALIASES = "SUBJECT_ALIASES"
    PREREQUISITES = "PREREQUISITE_SUBJECTS"
    NO_TOGETHER = "NO_TOGETHER_SUBJECTS"
    YEARS_HIERARCHY = "YEARS_HIERARCHY"
    YEARS_MESSAGE = "YEARS_MESSAGE"
    REQUIRED_SUBJECTS = "REQUIRED_SUBJECTS"  # プレフィックスで始まるキー
    TABLE_LAYOUTS = "TABLE_LAYOUTS"  # table_layoutで始まるキー
    SUBJECT_DETAILS = "SUBJECT_DETAILS"  # SUBJECT_DETAILS_で始まるキー
    GENERAL_SETTINGS = "GENERAL_SETTINGS"  # その他の設定


# セクションの表示名
SECTION_DISPLAY_NAMES = {
    ConfigSection.MASTER_SUBJECTS: "教科マスタ",
    ConfigSection.ALIASES: "エイリアス設定",
    ConfigSection.PREREQUISITES: "前提教科設定",
    ConfigSection.NO_TOGETHER: "同時選択不可設定",
    ConfigSection.YEARS_HIERARCHY: "年次階層",
    ConfigSection.YEARS_MESSAGE: "年次メッセージ",
    ConfigSection.REQUIRED_SUBJECTS: "必修教科設定",
    ConfigSection.TABLE_LAYOUTS: "テーブルレイアウト",
    ConfigSection.SUBJECT_DETAILS: "科目詳細",
    ConfigSection.GENERAL_SETTINGS: "一般設定",
}


@dataclass
class PartialConfig:
    """部分設定を表すデータクラス"""
    sections: Set[ConfigSection] = field(default_factory=set)
    data: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None
    exported_at: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "_meta": {
                "sections": [s.value for s in self.sections],
                "source_file": self.source_file,
                "exported_at": self.exported_at,
                "description": self.description,
            },
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PartialConfig":
        """辞書から作成"""
        meta = d.get("_meta", {})
        return cls(
            sections={ConfigSection(s) for s in meta.get("sections", [])},
            source_file=meta.get("source_file"),
            exported_at=meta.get("exported_at"),
            description=meta.get("description", ""),
            data=d.get("data", {})
        )


class PartialConfigExporter:
    """
    部分設定をエクスポートするクラス。
    """
    
    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
    
    def export_sections(self, sections: Set[ConfigSection]) -> PartialConfig:
        """
        指定されたセクションをエクスポート。
        
        Args:
            sections: エクスポートするセクション
            
        Returns:
            PartialConfig
        """
        from datetime import datetime
        
        data = {}
        
        for section in sections:
            section_data = self._extract_section(section)
            data.update(section_data)
        
        return PartialConfig(
            sections=sections,
            data=data,
            exported_at=datetime.now().isoformat(),
        )
    
    def _extract_section(self, section: ConfigSection) -> Dict[str, Any]:
        """セクションのデータを抽出"""
        result = {}
        
        if section == ConfigSection.MASTER_SUBJECTS:
            if "MASTER_SUBJECTS" in self.config_data:
                result["MASTER_SUBJECTS"] = self.config_data["MASTER_SUBJECTS"]
        
        elif section == ConfigSection.ALIASES:
            if "SUBJECT_ALIASES" in self.config_data:
                result["SUBJECT_ALIASES"] = self.config_data["SUBJECT_ALIASES"]
        
        elif section == ConfigSection.PREREQUISITES:
            if "PREREQUISITE_SUBJECTS" in self.config_data:
                result["PREREQUISITE_SUBJECTS"] = self.config_data["PREREQUISITE_SUBJECTS"]
        
        elif section == ConfigSection.NO_TOGETHER:
            if "NO_TOGETHER_SUBJECTS" in self.config_data:
                result["NO_TOGETHER_SUBJECTS"] = self.config_data["NO_TOGETHER_SUBJECTS"]
        
        elif section == ConfigSection.YEARS_HIERARCHY:
            if "YEARS_HIERARCHY" in self.config_data:
                result["YEARS_HIERARCHY"] = self.config_data["YEARS_HIERARCHY"]
        
        elif section == ConfigSection.YEARS_MESSAGE:
            if "YEARS_MESSAGE" in self.config_data:
                result["YEARS_MESSAGE"] = self.config_data["YEARS_MESSAGE"]
        
        elif section == ConfigSection.REQUIRED_SUBJECTS:
            for key in self.config_data:
                if key.startswith("REQUIRED_SUBJECTS_"):
                    result[key] = self.config_data[key]
        
        elif section == ConfigSection.TABLE_LAYOUTS:
            for key in self.config_data:
                if key.startswith("table_layout"):
                    result[key] = self.config_data[key]
        
        elif section == ConfigSection.SUBJECT_DETAILS:
            for key in self.config_data:
                if key.startswith("SUBJECT_DETAILS_"):
                    result[key] = self.config_data[key]
        
        elif section == ConfigSection.GENERAL_SETTINGS:
            general_keys = [
                "EDITOR_FONT_SIZE", "APP_FONT_SIZE",
                "SUBJECT_COMBINATION_COUNT", "MORE_SUBJECT_COMBINATION",
                "MIN_SUBJECT_COUNT", "MAX_SUBJECT_COUNT",
                "MIN_SUBJECT_COUNT_UNITS", "MAX_SUBJECT_COUNT_UNITS",
                "ACTIVE_MIN_SUBJECT", "ACTIVE_MAX_SUBJECT",
                "ACTIVE_FILTER_SUBJECT", "ACTIVE_FILTER_SUBJECT_AMOUNT",
                "ACTIVE_MIN_SUBJECT_UNITS", "ACTIVE_MAX_SUBJECT_UNITS",
                "ACTIVE_FILTER_SUBJECT_UNITS",
                "INCLUDE_FIXED", "TIMETABLE_ORDER",
                "TUTORIAL", "RUN_TUTORIAL_ON_STARTUP",
                "MAX_MEMORY_LIMIT", "ART_SUBJECT",
            ]
            for key in general_keys:
                if key in self.config_data:
                    result[key] = self.config_data[key]
        
        return result
    
    def save_to_file(self, partial: PartialConfig, file_path: str | Path) -> bool:
        """
        部分設定をファイルに保存。
        
        Args:
            partial: 保存するPartialConfig
            file_path: 保存先のパス
            
        Returns:
            成功時True
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(partial.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"部分設定の保存エラー: {e}")
            return False


class PartialConfigImporter:
    """
    部分設定をインポートするクラス。
    """
    
    def __init__(self, target_config: Dict[str, Any]):
        self.target_config = target_config
    
    def load_from_file(self, file_path: str | Path) -> Optional[PartialConfig]:
        """
        ファイルから部分設定を読み込み。
        
        Args:
            file_path: 読み込むファイルのパス
            
        Returns:
            PartialConfig、失敗時はNone
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return PartialConfig.from_dict(data)
        except Exception as e:
            print(f"部分設定の読み込みエラー: {e}")
            return None
    
    def merge(self, partial: PartialConfig, overwrite: bool = True) -> Dict[str, Any]:
        """
        部分設定を現在の設定にマージ。
        
        Args:
            partial: マージするPartialConfig
            overwrite: 既存の値を上書きするか
            
        Returns:
            マージ後の設定
        """
        import copy
        result = copy.deepcopy(self.target_config)
        
        for key, value in partial.data.items():
            if overwrite or key not in result:
                result[key] = copy.deepcopy(value)
        
        return result
    
    def get_conflicts(self, partial: PartialConfig) -> List[str]:
        """
        マージ時の競合をチェック。
        
        Args:
            partial: チェックするPartialConfig
            
        Returns:
            競合するキーのリスト
        """
        conflicts = []
        
        for key in partial.data:
            if key in self.target_config:
                if self.target_config[key] != partial.data[key]:
                    conflicts.append(key)
        
        return conflicts


def export_sections_to_file(
    config_data: Dict[str, Any],
    sections: Set[ConfigSection],
    file_path: str | Path,
    description: str = ""
) -> bool:
    """
    指定セクションをファイルにエクスポートする簡易関数。
    """
    exporter = PartialConfigExporter(config_data)
    partial = exporter.export_sections(sections)
    partial.description = description
    return exporter.save_to_file(partial, file_path)


def import_sections_from_file(
    target_config: Dict[str, Any],
    file_path: str | Path,
    overwrite: bool = True
) -> Optional[Dict[str, Any]]:
    """
    ファイルからセクションをインポートする簡易関数。
    """
    importer = PartialConfigImporter(target_config)
    partial = importer.load_from_file(file_path)
    if partial is None:
        return None
    return importer.merge(partial, overwrite)

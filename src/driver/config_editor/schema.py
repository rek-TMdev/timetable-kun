"""
schema.py - 設定ファイルのJSONスキーマ定義と検証

設定ファイルの構造を検証するためのスキーマ定義と検証関数を提供します。
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


# 設定ファイルのスキーマ定義
CONFIG_SCHEMA = {
    "type": "object",
    "required": ["MASTER_SUBJECTS"],
    "properties": {
        # 教科マスタ（必須）
        "MASTER_SUBJECTS": {
            "type": "array",
            "items": {"type": "string"},
            "description": "教科名のリスト"
        },
        
        # エイリアス設定
        "SUBJECT_ALIASES": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {"type": "string"}
            },
            "description": "教科名とそのエイリアスのマッピング"
        },
        
        # 前提教科設定
        "PREREQUISITE_SUBJECTS": {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {"type": "string"}
            },
            "description": "教科とその前提教科のマッピング"
        },
        
        # 同時選択不可グループ
        "NO_TOGETHER_SUBJECTS": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 2
            },
            "description": "同時に選択できない教科のグループ"
        },
        
        # 年次階層
        "YEARS_HIERARCHY": {
            "type": "object",
            "description": "学年・課程の階層構造"
        },
        
        # 年次選択メッセージ
        "YEARS_MESSAGE": {
            "type": "array",
            "items": {"type": "string"},
            "description": "階層選択時に表示するメッセージ"
        },
        
        # 一般設定
        "EDITOR_FONT_SIZE": {"type": "integer", "minimum": 8, "maximum": 24},
        "APP_FONT_SIZE": {"type": "integer", "minimum": 8, "maximum": 24},
        "SUBJECT_COMBINATION_COUNT": {"type": "integer", "minimum": 1},
        "MORE_SUBJECT_COMBINATION": {"type": "integer", "minimum": 0},
        "MIN_SUBJECT_COUNT": {"type": "integer", "minimum": 0},
        "MAX_SUBJECT_COUNT": {"type": "integer", "minimum": 0},
        "MIN_SUBJECT_COUNT_UNITS": {"type": "integer", "minimum": 0},
        "MAX_SUBJECT_COUNT_UNITS": {"type": "integer", "minimum": 0},
        
        # フラグ設定
        "ACTIVE_MIN_SUBJECT": {"type": "boolean"},
        "ACTIVE_MAX_SUBJECT": {"type": "boolean"},
        "ACTIVE_FILTER_SUBJECT": {"type": "boolean"},
        "ACTIVE_FILTER_SUBJECT_AMOUNT": {"type": "boolean"},
        "ACTIVE_MIN_SUBJECT_UNITS": {"type": "boolean"},
        "ACTIVE_MAX_SUBJECT_UNITS": {"type": "boolean"},
        "ACTIVE_FILTER_SUBJECT_UNITS": {"type": "boolean"},
        "INCLUDE_FIXED": {"type": "boolean"},
        "TIMETABLE_ORDER": {"type": "boolean"},
        "TUTORIAL": {"type": "boolean"},
        "RUN_TUTORIAL_ON_STARTUP": {"type": "boolean"},
        
        # メタデータ
        "LAST_UPDATE_DAY": {"type": "string"},
        "MAX_MEMORY_LIMIT": {"type": "integer", "minimum": 100},
        "ART_SUBJECT": {"type": "integer"},
    }
}


class ValidationError:
    """検証エラーを表すクラス"""
    
    def __init__(self, path: str, message: str, severity: str = "error"):
        """
        Args:
            path: エラーが発生したキーのパス（例: "MASTER_SUBJECTS[0]"）
            message: エラーメッセージ
            severity: 重要度（"error", "warning", "info"）
        """
        self.path = path
        self.message = message
        self.severity = severity
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.path}: {self.message}"
    
    def __repr__(self) -> str:
        return f"ValidationError({self.path!r}, {self.message!r}, {self.severity!r})"


class ConfigValidator:
    """
    設定データを検証するクラス。
    
    JSONスキーマに基づいた構造検証と、ビジネスルールに基づいた
    意味的検証の両方を行います。
    """
    
    def __init__(self, schema: Dict[str, Any] = None):
        self.schema = schema or CONFIG_SCHEMA
    
    def validate(self, config_data: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        設定データを検証する。
        
        Args:
            config_data: 検証する設定データ
            
        Returns:
            (成功/失敗, エラーリスト) のタプル
        """
        errors = []
        
        # 構造検証
        errors.extend(self._validate_structure(config_data))
        
        # 意味的検証
        errors.extend(self._validate_semantics(config_data))
        
        # エラーのみをフィルタリング
        critical_errors = [e for e in errors if e.severity == "error"]
        
        return len(critical_errors) == 0, errors
    
    def _validate_structure(self, config_data: Dict[str, Any]) -> List[ValidationError]:
        """構造検証（型チェック、必須フィールドチェック）"""
        errors = []
        
        # 必須キーのチェック
        required = self.schema.get("required", [])
        for key in required:
            if key not in config_data:
                errors.append(ValidationError(
                    key, 
                    f"必須キー '{key}' が見つかりません",
                    "error"
                ))
        
        # プロパティの型チェック
        properties = self.schema.get("properties", {})
        for key, value in config_data.items():
            if key in properties:
                prop_schema = properties[key]
                type_errors = self._check_type(key, value, prop_schema)
                errors.extend(type_errors)
        
        return errors
    
    def _check_type(self, path: str, value: Any, schema: Dict) -> List[ValidationError]:
        """値の型をスキーマに基づいてチェック"""
        errors = []
        expected_type = schema.get("type")
        
        if expected_type is None:
            return errors
        
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        
        python_type = type_map.get(expected_type)
        if python_type and not isinstance(value, python_type):
            errors.append(ValidationError(
                path,
                f"型が不正です: 期待={expected_type}, 実際={type(value).__name__}",
                "error"
            ))
            return errors
        
        # 配列の要素チェック
        if expected_type == "array" and "items" in schema:
            items_schema = schema["items"]
            for i, item in enumerate(value):
                item_path = f"{path}[{i}]"
                errors.extend(self._check_type(item_path, item, items_schema))
            
            # 最小要素数チェック
            if "minItems" in schema and len(value) < schema["minItems"]:
                errors.append(ValidationError(
                    path,
                    f"配列の要素数が不足: 最小={schema['minItems']}, 実際={len(value)}",
                    "error"
                ))
        
        # 数値の範囲チェック
        if expected_type in ("integer", "number"):
            if "minimum" in schema and value < schema["minimum"]:
                errors.append(ValidationError(
                    path,
                    f"値が小さすぎます: 最小={schema['minimum']}, 実際={value}",
                    "warning"
                ))
            if "maximum" in schema and value > schema["maximum"]:
                errors.append(ValidationError(
                    path,
                    f"値が大きすぎます: 最大={schema['maximum']}, 実際={value}",
                    "warning"
                ))
        
        return errors
    
    def _validate_semantics(self, config_data: Dict[str, Any]) -> List[ValidationError]:
        """意味的検証（ビジネスルールチェック）"""
        errors = []
        
        master_subjects = set(config_data.get("MASTER_SUBJECTS", []))
        
        # エイリアス設定の検証
        aliases = config_data.get("SUBJECT_ALIASES", {})
        for subject, alias_list in aliases.items():
            if subject not in master_subjects:
                errors.append(ValidationError(
                    f"SUBJECT_ALIASES.{subject}",
                    f"マスタに存在しない教科 '{subject}' のエイリアスが定義されています",
                    "warning"
                ))
        
        # 前提教科設定の検証
        prereqs = config_data.get("PREREQUISITE_SUBJECTS", {})
        for subject, prereq_list in prereqs.items():
            if subject not in master_subjects:
                errors.append(ValidationError(
                    f"PREREQUISITE_SUBJECTS.{subject}",
                    f"マスタに存在しない教科 '{subject}' の前提教科が定義されています",
                    "warning"
                ))
            for prereq in prereq_list:
                if prereq not in master_subjects:
                    errors.append(ValidationError(
                        f"PREREQUISITE_SUBJECTS.{subject}",
                        f"前提教科 '{prereq}' がマスタに存在しません",
                        "warning"
                    ))
        
        # 同時選択不可グループの検証
        no_together = config_data.get("NO_TOGETHER_SUBJECTS", [])
        for i, group in enumerate(no_together):
            for subject in group:
                if subject not in master_subjects:
                    errors.append(ValidationError(
                        f"NO_TOGETHER_SUBJECTS[{i}]",
                        f"同時選択不可グループの教科 '{subject}' がマスタに存在しません",
                        "warning"
                    ))
        
        # 重複チェック
        if len(master_subjects) != len(config_data.get("MASTER_SUBJECTS", [])):
            errors.append(ValidationError(
                "MASTER_SUBJECTS",
                "教科マスタに重複があります",
                "warning"
            ))
        
        return errors


def validate_config(config_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    設定データを検証する簡易関数。
    
    Args:
        config_data: 検証する設定データ
        
    Returns:
        (成功/失敗, エラーメッセージリスト) のタプル
    """
    validator = ConfigValidator()
    is_valid, errors = validator.validate(config_data)
    return is_valid, [str(e) for e in errors]


def validate_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    ファイルを読み込んで検証する。
    
    Args:
        file_path: 検証するJSONファイルのパス
        
    Returns:
        (成功/失敗, エラーメッセージリスト) のタプル
    """
    import json
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"JSONパースエラー: {e}"]
    except FileNotFoundError:
        return False, [f"ファイルが見つかりません: {file_path}"]
    except Exception as e:
        return False, [f"ファイル読み込みエラー: {e}"]
    
    return validate_config(config_data)

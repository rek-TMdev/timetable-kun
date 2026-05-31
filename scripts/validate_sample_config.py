from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "examples" / "sample_config.json"


def collect_leaf_parts(node: Any, parts: list[str] | None = None) -> list[list[str]]:
    parts = parts or []
    if not isinstance(node, dict):
        raise TypeError(f"YEARS_HIERARCHY の葉は list ではなく dict にしてください: {'_'.join(parts)}")
    if not node:
        return [parts] if parts else []

    paths: list[list[str]] = []
    for key, child in node.items():
        if not isinstance(key, str) or not key:
            raise ValueError("YEARS_HIERARCHY のキーは空でない文字列にしてください")
        paths.extend(collect_leaf_parts(child, parts + [key]))
    return paths


def flatten_table_layout(table_key: str, table_layout: Any) -> set[str]:
    if not isinstance(table_layout, list):
        raise TypeError("table_layout* は二次元配列にしてください")
    if len(table_layout) != 6:
        raise ValueError(f"{table_key} は6行にしてください")
    slots: set[str] = set()
    for row_index, row in enumerate(table_layout, start=1):
        if not isinstance(row, list):
            raise TypeError("table_layout* の各行は配列にしてください")
        if len(row) != 5:
            raise ValueError(f"{table_key} の{row_index}行目は5列にしてください")
        for slot in row:
            if slot:
                if not isinstance(slot, str):
                    raise TypeError("table_layout* のスロット名は文字列にしてください")
                slots.add(slot)
    return slots


def require_list_of_subject_maps(config: dict[str, Any], key: str) -> None:
    value = config.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} は空でない配列にしてください")
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise TypeError(f"{key}[{index}] はオブジェクトにしてください")
        if not isinstance(item.get("name"), str) or not item["name"]:
            raise ValueError(f"{key}[{index}].name は空でない文字列にしてください")
        if not isinstance(item.get("data"), (dict, list)):
            raise TypeError(f"{key}[{index}].data はオブジェクトまたは配列にしてください")


def require_art_subjects(config: dict[str, Any]) -> None:
    master_subjects = config.get("MASTER_SUBJECTS")
    if not isinstance(master_subjects, list) or not master_subjects:
        raise ValueError("MASTER_SUBJECTS は空でない配列にしてください")

    art_count = config.get("ART_SUBJECT")
    if isinstance(art_count, bool) or not isinstance(art_count, int) or art_count < 1:
        raise ValueError("ART_SUBJECT は1以上の整数にしてください")

    selectable = config.get("SELECTED_ART_SUBJECT")
    if not isinstance(selectable, list) or len(selectable) < art_count:
        raise ValueError("SELECTED_ART_SUBJECT は ART_SUBJECT 数以上の候補配列にしてください")
    if not all(isinstance(subject, str) and subject for subject in selectable):
        raise ValueError("SELECTED_ART_SUBJECT の各候補は空でない文字列にしてください")
    expected_selectable = ["書道Ⅰ", "美術Ⅰ", "音楽Ⅰ"]
    if selectable != expected_selectable:
        raise ValueError(f"SELECTED_ART_SUBJECT は元データと同じ候補順にしてください: {expected_selectable}")

    missing_from_master = sorted(set(selectable) - set(master_subjects))
    if missing_from_master:
        raise ValueError(f"芸術科目候補が MASTER_SUBJECTS にありません: {missing_from_master}")

    if "PROFILE_ART_SELECTIONS" in config:
        raise ValueError("PROFILE_ART_SELECTIONS は元データの基本形にないためサンプルへ入れないでください")


def main() -> int:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    hierarchy = config.get("YEARS_HIERARCHY")
    if not isinstance(hierarchy, dict) or not hierarchy:
        raise ValueError("YEARS_HIERARCHY は空でないオブジェクトにしてください")

    year_messages = config.get("YEARS_MESSAGE")
    if year_messages != ["課程"]:
        raise ValueError('公開サンプルの YEARS_MESSAGE は元データと同じ ["課程"] にしてください')

    expected_hierarchy = {"全日制": {"2年": {}, "3年": {}}}
    if hierarchy != expected_hierarchy:
        raise ValueError(f"公開サンプルの YEARS_HIERARCHY は元データと同じ構造にしてください: {expected_hierarchy}")
    if config.get("HIERARCHY_ANCHORS") != ["全日制"]:
        raise ValueError('HIERARCHY_ANCHORS は ["全日制"] にしてください')

    leaf_parts = collect_leaf_parts(hierarchy)
    if not leaf_parts:
        raise ValueError("YEARS_HIERARCHY に葉がありません")

    require_art_subjects(config)
    if "REQUIRED_SUBJECTS_ALL" in config:
        raise ValueError("REQUIRED_SUBJECTS_ALL は元データの現行サンプル形に合わせて含めないでください")
    unit_keys = [key for key in config if key.startswith("YEARS_SUBJECTS_UNITS_")]
    if unit_keys != ["YEARS_SUBJECTS_UNITS_全日制"]:
        raise ValueError("YEARS_SUBJECTS_UNITS_* は元データと同じく YEARS_SUBJECTS_UNITS_全日制 のみにしてください")
    if not isinstance(config.get("SAVE_POSITION全日制"), dict):
        raise TypeError("SAVE_POSITION全日制 はオブジェクトにしてください")

    leaf_paths: list[str] = []
    for parts in leaf_parts:
        path = "_".join(parts)
        leaf_paths.append(path)
        top_level = parts[0]
        table_key = f"table_layout{path}"
        number_key = f"subject_number{path}"
        slots_key = f"subject_slots_base{path}"
        save_key = f"SAVE_POSITION{path}"
        top_units_key = f"YEARS_SUBJECTS_UNITS_{top_level}"
        all_slots_key = f"ALL_SLOTS{path}"
        abnormal_key = f"ABNORMAL_SUBJECTS_UNITS{path}"
        required_top_key = f"REQUIRED_SUBJECTS_{top_level}"
        leaf_units_key = f"YEARS_SUBJECTS_UNITS_{path}"

        missing = [
            key
            for key in [
                table_key,
                number_key,
                slots_key,
                save_key,
                top_units_key,
                all_slots_key,
                abnormal_key,
                required_top_key,
            ]
            if key not in config
        ]
        if missing:
            raise KeyError(f"{path} に対応する設定キーが不足しています: {', '.join(missing)}")
        if leaf_units_key in config:
            raise ValueError(f"{leaf_units_key} は元データと違うため入れないでください")

        slots = flatten_table_layout(table_key, config[table_key])
        if not slots:
            raise ValueError(f"{table_key} に有効なスロットがありません")
        if not all(slot[:1].isalpha() and slot[1:].isdigit() for slot in slots):
            raise ValueError(f"{table_key} のスロット名は A1 形式にしてください")

        require_list_of_subject_maps(config, number_key)
        require_list_of_subject_maps(config, slots_key)

        save_position = config[save_key]
        if not isinstance(save_position, dict):
            raise TypeError(f"{save_key} はオブジェクトにしてください")
        unknown_save_slots = set(save_position) - slots
        if unknown_save_slots:
            raise ValueError(f"{save_key} に table_layout 未定義のスロットがあります: {sorted(unknown_save_slots)}")

        if not isinstance(config[top_units_key], int | float):
            raise TypeError(f"{top_units_key} は数値にしてください")
        if not isinstance(config[all_slots_key], list):
            raise TypeError(f"{all_slots_key} は配列にしてください")
        missing_all_slots = slots - set(config[all_slots_key])
        if missing_all_slots:
            raise ValueError(f"{all_slots_key} に table_layout のスロットが不足しています: {sorted(missing_all_slots)}")
        if not isinstance(config[abnormal_key], dict):
            raise TypeError(f"{abnormal_key} はオブジェクトにしてください")
        if not isinstance(config[required_top_key], dict):
            raise TypeError(f"{required_top_key} はオブジェクトにしてください")

    if not isinstance(config.get("REQUIRED_SUBJECTS_全日制_3年"), dict):
        raise TypeError("REQUIRED_SUBJECTS_全日制_3年 はオブジェクトにしてください")

    print(f"sample_config OK: {', '.join(leaf_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

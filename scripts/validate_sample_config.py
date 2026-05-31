from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "examples" / "sample_config.json"


def collect_leaf_paths(node: Any, parts: list[str] | None = None) -> list[str]:
    parts = parts or []
    if not isinstance(node, dict):
        raise TypeError(f"YEARS_HIERARCHY の葉は list ではなく dict にしてください: {'_'.join(parts)}")
    if not node:
        return ["_".join(parts)] if parts else []

    paths: list[str] = []
    for key, child in node.items():
        if not isinstance(key, str) or not key:
            raise ValueError("YEARS_HIERARCHY のキーは空でない文字列にしてください")
        paths.extend(collect_leaf_paths(child, parts + [key]))
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


def main() -> int:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = json.load(f)

    hierarchy = config.get("YEARS_HIERARCHY")
    if not isinstance(hierarchy, dict) or not hierarchy:
        raise ValueError("YEARS_HIERARCHY は空でないオブジェクトにしてください")

    leaf_paths = collect_leaf_paths(hierarchy)
    if not leaf_paths:
        raise ValueError("YEARS_HIERARCHY に葉がありません")

    for path in leaf_paths:
        table_key = f"table_layout{path}"
        number_key = f"subject_number{path}"
        slots_key = f"subject_slots_base{path}"
        save_key = f"SAVE_POSITION{path}"
        units_key = f"YEARS_SUBJECTS_UNITS_{path}"

        missing = [key for key in [table_key, number_key, slots_key, save_key, units_key] if key not in config]
        if missing:
            raise KeyError(f"{path} に対応する設定キーが不足しています: {', '.join(missing)}")

        slots = flatten_table_layout(table_key, config[table_key])
        if not slots:
            raise ValueError(f"{table_key} に有効なスロットがありません")

        require_list_of_subject_maps(config, number_key)
        require_list_of_subject_maps(config, slots_key)

        save_position = config[save_key]
        if not isinstance(save_position, dict):
            raise TypeError(f"{save_key} はオブジェクトにしてください")
        unknown_save_slots = set(save_position) - slots
        if unknown_save_slots:
            raise ValueError(f"{save_key} に table_layout 未定義のスロットがあります: {sorted(unknown_save_slots)}")

        if not isinstance(config[units_key], int | float):
            raise TypeError(f"{units_key} は数値にしてください")

    print(f"sample_config OK: {', '.join(leaf_paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

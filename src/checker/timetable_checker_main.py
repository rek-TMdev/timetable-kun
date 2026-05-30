import os
import sys
import json
import shutil
import csv
import darkdetect
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QTabWidget, QSpinBox, QFileDialog, QMessageBox, QProgressBar,
    QDialog, QGroupBox, QRadioButton, QButtonGroup, QListWidget, QCheckBox, QFrame
)
from PySide6.QtGui import (
    QFont, QFontDatabase, QDragEnterEvent, QDropEvent, 
    QColor, QPalette, QIcon
)
from PySide6.QtCore import Qt, QEvent
import concurrent.futures
import openpyxl
from pathlib import Path

# ログ基盤
try:
    from logging_utils import setup_logger, log_exception
    logger = setup_logger("timetable_checker")
except ImportError:
    import logging
    logger = logging.getLogger("timetable_checker")
    logger.addHandler(logging.NullHandler())

def set_button_styles(app, is_dark=None):
    """テーマに応じたQPushButton/QComboBox用スタイルを適用する。"""
    if is_dark is None:
        is_dark = darkdetect.theme() == "Dark"

    light_style = """
        QPushButton, QComboBox {
            background-color: #3478f6FF;
            color: black;
            border: 1px solid #3478f6;
            padding: 4px;
            border-radius: 4px;
        }
        QPushButton:hover, QComboBox:hover {
            background-color: #5F92F1;
            border-color: #285ec6;
        }
        QPushButton:pressed {
            background-color: #1a479b;
            border-color: #1a479b;
        }
        QPushButton:disabled, QComboBox:disabled {
            background-color: #E4E4E4FF;
            color: #999999;
            border-color: #999999;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            color: black;
            border: 1px solid #3478f6;
            selection-background-color: #285ec6;
            selection-color: white;
        }
    """

    dark_style = """
        QPushButton, QComboBox {
            background-color: #0A5AAAFF;
            color: white;
            border: 1px solid #0A84FF;
            padding: 4px;
            border-radius: 4px;
        }
        QPushButton:hover, QComboBox:hover {
            background-color: #0166C5;
            border-color: #0077E8;
        }
        QPushButton:pressed {
            background-color: #0062C2;
            border-color: #0062C2;
        }
        QPushButton:disabled, QComboBox:disabled {
            background-color: #1e1e1e;
            color: #999999;
            border-color: #999999;
        }
        QComboBox QAbstractItemView {
            background-color: #2D2D2D;
            color: white;
            border: 1px solid #0A84FF;
            selection-background-color: #0077E8;
            selection-color: white;
        }
    """

    app.setStyleSheet(dark_style if is_dark else light_style)


class ConfigSelectionDialog(QDialog):
    """設定ファイルを選択するための汎用ダイアログ"""
    def __init__(self, parent, title, message, items):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint) # 最前面
        self.setModal(True)
        self.selected_item = None

        icon_base_name = "時間割くんチェッカーアイコン.ico"
        icon_path_obj = parent.base_path / icon_base_name
        icon_path = str(icon_path_obj) # QIcon用に文字列へ変換

        if icon_path_obj.exists(): # pathlibのexists()で存在確認
            icon = QIcon(icon_path) # QIconには文字列パスを渡す
            if not icon.isNull():
                self.setWindowIcon(icon)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(message))

        self.list_widget = QListWidget()
        self.list_widget.addItems(items)
        if items:
            self.list_widget.setCurrentRow(0)
        layout.addWidget(self.list_widget)

        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

    def accept(self):
        if self.list_widget.currentItem():
            self.selected_item = self.list_widget.currentItem().text()
        super().accept()
    def get_selected_item(self): return self.selected_item

class DepartmentSelectionDialog(QDialog):
    def __init__(self, parent=None, hierarchy_keys=None, message="学科を選択してください"):
        super().__init__(parent)
        self.setWindowTitle(message)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint) # 最前面
        self.setModal(True)
        self.selected_department = None

        self.selected_department = None

        main_layout = QVBoxLayout(self)

        label = QLabel("選択してください:")
        main_layout.addWidget(label)

        # ラジオボタンをグループ化する
        self.radio_group_box = QGroupBox()
        radio_layout = QVBoxLayout()
        self.radio_button_group = QButtonGroup(self)

        if hierarchy_keys:
            sorted_keys = sorted(hierarchy_keys)
            for i, key in enumerate(sorted_keys):
                radio_button = QRadioButton(key)
                radio_layout.addWidget(radio_button)
                self.radio_button_group.addButton(radio_button, i)
            
            if self.radio_button_group.buttons():
                self.radio_button_group.buttons()[0].setChecked(True)

        self.radio_group_box.setLayout(radio_layout)
        main_layout.addWidget(self.radio_group_box)

        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("キャンセル")
        cancel_button.clicked.connect(self.reject)

        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        main_layout.addLayout(button_box)

    def accept(self):
        checked_button = self.radio_button_group.checkedButton()
        if checked_button:
            self.selected_department = checked_button.text()
        super().accept()

    def get_selected_department(self):
        return self.selected_department

class DepartmentSelector:
    """学科の階層選択に関するUIロジックを管理するクラス"""
    def __init__(self, window):
        self.window = window
        self.config = window.config
        
        self.selected_path = ""
        self.selected_hierarchy = {}
        self.selected_display = "全て"

    def initialize(self):
        """保存された設定に基づいて初期選択を決定し、UIを更新する"""
        last_path = self.config.get("LAST_SELECTED_PATH")
        if last_path is not None:
            self.selected_path = last_path
            self.selected_hierarchy = self._get_hierarchy_from_path(last_path)
        else:
            # 保存されたパスがない場合、デフォルト（全体）のまま
            self.selected_path = ""
            self.selected_hierarchy = self.config.get("YEARS_HIERARCHY", {})
        
        self.selected_display = self.selected_path.replace('_', ' ') if self.selected_path else "全て"
        self._update_window_state()

    def change_department(self):
        """学科選択ダイアログを表示し、選択結果を適用する"""
        path_key, hierarchy = self._perform_hierarchical_selection()

        if path_key != "SUB_CANCEL":
            self.selected_path = path_key
            self.selected_hierarchy = hierarchy
            self.selected_display = path_key.replace('_', ' ') if path_key else "全て"
            
            self._update_window_state()
            
            self.config["LAST_SELECTED_PATH"] = path_key
            self.window.config_manager.save_config()

    def _update_window_state(self):
        """選択結果をメインウィンドウのUIとプロパティに反映する"""
        self.window.dept_label.setText(f"現在選択中の学科: {self.selected_display}")
        self.window.selected_department_path = self.selected_path
        self.window.selected_hierarchy = self.selected_hierarchy

    def _perform_hierarchical_selection(self):
        """ダイアログを順に表示して学科を選択させる"""
        full_hierarchy = self.config.get("YEARS_HIERARCHY", {})
        messages = self.config.get("YEARS_MESSAGE", [])

        if not messages or not isinstance(messages, list) or not full_hierarchy:
            return "SUB_CANCEL", full_hierarchy

        current_hierarchy = full_hierarchy
        selected_path_parts = []

        for message_base in messages:
            keys = list(current_hierarchy.keys())
            if not keys or not isinstance(current_hierarchy, dict): break

            dialog = DepartmentSelectionDialog(self.window, keys, f"{message_base}を選択してください")
            if dialog.exec() == QDialog.Accepted:
                choice = dialog.get_selected_department()
                if choice and choice in current_hierarchy:
                    selected_path_parts.append(choice)
                    current_hierarchy = current_hierarchy[choice]
                else:
                    return "SUB_CANCEL", full_hierarchy
            else:
                return "SUB_CANCEL", full_hierarchy

        return "_".join(selected_path_parts), current_hierarchy

    def _get_hierarchy_from_path(self, path):
        """パス文字列から対応する階層のサブセットを返す"""
        if not path:
            return self.config.get("YEARS_HIERARCHY", {})
        
        parts = path.split('_')
        current_node = self.config.get("YEARS_HIERARCHY", {})
        
        try:
            for part in parts:
                current_node = current_node[part]
            return current_node
        except (KeyError, TypeError):
            return self.config.get("YEARS_HIERARCHY", {})

class TimetableValidator:
    """時間割ファイルの検証ロジックをカプセル化するクラス"""
    def __init__(self, config):
        self.config = config

    def validate(self, file_path, hierarchy_to_check, department_path, min_units):
        """単一のファイルを検証し、エラーのリストを返す"""
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True, keep_links=False)
            ws = wb.active
        except Exception as e:
            return [{'type': 'file_read_error', 'details': str(e)}]
        
        errors = []
        years = self._get_all_leaf_years(hierarchy_to_check)
        
        all_subjects_for_prereq_check = set()
        subjects_by_year_for_unit_check = {year: [] for year in years}
        subjects_by_year_for_required_check = {}

        for year in years:
            save_pos = self.config.get(f"SAVE_POSITION{year}", {})
            year_subjects_from_excel = set()
            if save_pos:
                for slot_name, pos_list in save_pos.items():
                    for pos_info in pos_list:
                        try:
                            coords = self._a1_to_coords(pos_info[0])
                            if coords:
                                cell_value = ws.cell(row=coords[0], column=coords[1]).value
                                if cell_value is not None:
                                    subject = self.find_subject_for_slot_and_number(year, slot_name, str(cell_value).strip())
                                    if subject:
                                        year_subjects_from_excel.add(subject)
                                        subjects_by_year_for_unit_check[year].append(subject)
                        except Exception as e:
                            errors.append({'type': 'cell_read_error', 'details': f"{year} {slot_name}: {e}"})
            
            fixed_slots = self.config.get(f"FIXED_SLOTS{year}", {})
            subjects_by_year_for_unit_check[year].extend(fixed_slots.values())
            
            fixed_subjects_this_year = set(fixed_slots.values())
            total_year_subjects = year_subjects_from_excel.union(fixed_subjects_this_year)
            subjects_by_year_for_required_check[year] = total_year_subjects
            all_subjects_for_prereq_check.update(total_year_subjects)

        # 単位数チェック
        config_key = f"YEARS_SUBJECTS_UNITS_{department_path}"
        total_units = float(self.config.get(config_key, 30))
        for year in years:
            subjects_this_year = subjects_by_year_for_unit_check[year]
            if subjects_this_year:
                total_units += self._calculate_units_for_year(subjects_this_year, year)
        
        if total_units < min_units:
            errors.append({'type': 'units_insufficient', 'details': {'current': total_units, 'required': min_units}})

        # 必須科目チェック
        for year, year_subjects_set in subjects_by_year_for_required_check.items():
            missing_required = self.check_required_subjects(year_subjects_set, year)
            if missing_required:
                errors.append({'type': 'required_missing', 'details': {'year': year, 'missing': missing_required}})

        # 前提科目チェック
        missing_prerequisites = self.check_prerequisites(all_subjects_for_prereq_check)
        if missing_prerequisites:
            errors.append({'type': 'prereq_missing', 'details': missing_prerequisites})

        wb.close()
        return errors

    def find_subject_for_slot_and_number(self, year: str, slot_name: str, num_str: str) -> str | None:
        if not all([year, slot_name, num_str]): return None
        subject_number_list = self.config.get(f"subject_number{year}", [])
        for subject_info in subject_number_list:
            if "data" in subject_info and isinstance(subject_info["data"], dict):
                number_in_config = subject_info["data"].get(slot_name)
                if number_in_config is not None and str(number_in_config).strip() == num_str:
                    return subject_info.get("name")
        return None

    def _a1_to_coords(self, a1_string: str) -> list | None:
        if not isinstance(a1_string, str): return None
        col_str, row_str = "", ""
        for char in a1_string:
            if char.isalpha(): col_str += char
            elif char.isdigit(): row_str += char
        if not col_str or not row_str: return None
        col_idx = 0
        for char in col_str.upper(): col_idx = col_idx * 26 + (ord(char) - ord('A') + 1)
        try:
            return [int(row_str), col_idx]
        except ValueError:
            return None

    def _normalize_subject_name(self, name: str) -> str | None:
        if not isinstance(name, str): return None
        return name

    def _calculate_units_for_year(self, subjects_list_raw: list, year: str) -> float:
        year_total_units = float(len(subjects_list_raw))
        abnormal_units_general = {self._normalize_subject_name(k): v for k, v in self.config.get("ABNORMAL_SUBJECTS_UNITS", {}).items()}
        year_abnormal_key = f"ABNORMAL_SUBJECTS_UNITS{year}"
        abnormal_units_year = {self._normalize_subject_name(k): v for k, v in self.config.get(year_abnormal_key, {}).items()}
        
        normalized_subjects_raw = [self._normalize_subject_name(s) for s in subjects_list_raw if self._normalize_subject_name(s)]
        special_subjects_in_year = [s for s in normalized_subjects_raw if s in abnormal_units_year or s in abnormal_units_general]
        
        for subject in set(special_subjects_in_year):
            delta = abnormal_units_year.get(subject) or abnormal_units_general.get(subject)
            if delta is not None:
                try: year_total_units += float(delta)
                except (ValueError, TypeError): pass
        return year_total_units

    def check_prerequisites(self, all_subjects: set) -> list:
        missing = []
        prerequisites = self.config.get("PREREQUISITE_SUBJECTS", {})
        for subject in all_subjects:
            if subject in prerequisites:
                missing_reqs = [p for p in prerequisites[subject] if p not in all_subjects]
                if missing_reqs:
                    missing.append({'subject': subject, 'requires': missing_reqs})
        return missing

    def check_required_subjects(self, all_subjects: set, year_label: str) -> list:
        missing_info = []
        # 学年固有 -> 階層 -> 全学年の順で要件をチェック
        keys_to_check = [f"REQUIRED_SUBJECTS_{year_label}"]
        parts = year_label.split('_')
        if len(parts) > 1:
            for i in range(len(parts) - 1):
                keys_to_check.append(f"REQUIRED_SUBJECTS_{'_'.join(parts[:i+1])}")
        keys_to_check.append("REQUIRED_SUBJECTS_ALL")
        
        source_labels = [year_label] + ['_'.join(parts[:i+1]) for i in range(len(parts) - 1)] + ["全学年"]
        
        for req_key, source_type in zip(keys_to_check, source_labels):
            requirements = self.config.get(req_key, {})
            if requirements:
                missing = self._check_requirements(all_subjects, requirements)
                for info in missing: info["source_type"] = source_type
                missing_info.extend(missing)
        return missing_info

    def _check_requirements(self, subjects: set, requirements: dict) -> list:
        missing = []
        for req_key, req_details in requirements.items():
            color = req_details.get("color", "#FF0000")
            if "conditions" in req_details and isinstance(req_details["conditions"], list):
                is_or_met = any(
                    sum(1 for s in cond.get("subjects", []) if s in subjects) >= int(cond.get("required", 1))
                    for cond in req_details["conditions"]
                )
                if not is_or_met:
                    all_or_conds = [{
                        'condition_num': req_key, 'required': int(c.get("required", 1)), 'matched': sum(1 for s in c.get("subjects", []) if s in subjects),
                        'subjects': c.get("subjects", []), 'color': color, 'is_or_group': True
                    } for c in req_details["conditions"]]
                    missing.extend(all_or_conds)
            else:
                req_count = int(req_details.get("required", 1))
                req_subjects = req_details.get("subjects", [])
                found_count = sum(1 for s in req_subjects if s in subjects)
                if found_count < req_count:
                    missing.append({'condition_num': req_key, 'required': req_count, 'matched': found_count, 'subjects': req_subjects, 'color': color, 'is_or_group': False})
        return missing

    def _get_all_leaf_years(self, hierarchy):
        collected_paths = []
        if not hierarchy: return []
        def find_nodes(node, current_path_parts):
            if not node or not isinstance(node, dict):
                if current_path_parts: collected_paths.append("_".join(current_path_parts))
                return
            for key, value in node.items(): find_nodes(value, current_path_parts + [key])
        find_nodes(hierarchy, [])
        return sorted(list(set(collected_paths)))

class ConfigManager:
    """設定ファイルの検索、選択、読み込み、保存を管理するクラス"""
    def __init__(self, parent):
        self.parent = parent
        self.user_settings = {}
        self.config_path = None
        self.config = {}

    def load_and_get_config(self):
        """設定の読み込み処理を統括し、最終的な設定オブジェクトを返す"""
        self.user_settings = self._load_user_settings()
        
        chosen_path = self._select_config_file()
        if not chosen_path:
            # ユーザーが選択をキャンセルした場合などは、Noneを返して終了
            return None
            
        self.config_path = Path(chosen_path)
        self._save_user_settings()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                local_config = json.load(f)
        except Exception as e:
            QMessageBox.critical(self.parent, "設定エラー", f"設定ファイルの読み込みに失敗しました:\n{self.config_path}\n\nエラー: {e}")
            return None

        master_config = None
        master_config_path_str = local_config.get("MASTER_CONFIG_PATH")
        if master_config_path_str:
            try:
                if Path(master_config_path_str).is_file():
                    with open(master_config_path_str, 'r', encoding='utf-8') as f:
                        master_config = json.load(f)
            except Exception as e:
                print(f"マスター設定の読み込みに失敗: {e}")

        if master_config:
            local_date = self._parse_update_day(local_config.get("LAST_UPDATE_DAY"))
            master_date = self._parse_update_day(master_config.get("LAST_UPDATE_DAY"))

            if master_date and (not local_date or master_date > local_date):
                self.config = master_config
                try:
                    with open(self.config_path, 'w', encoding='utf-8') as f:
                        json.dump(master_config, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    QMessageBox.warning(self.parent, "設定更新エラー", f"ローカル設定ファイルの更新に失敗しました:\n{e}")
            else:
                self.config = local_config
        else:
            self.config = local_config
            
        return self.config

    def save_config(self):
        """現在の設定をファイルに保存する"""
        if not self.config_path or not self.config:
            print("設定ファイルのパスまたはデータが見つからないため、保存できません。")
            return
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self.parent, "設定保存エラー", f"設定の保存に失敗しました:\n{e}")

    def _parse_update_day(self, date_str):
        if not date_str: return None
        try:
            return datetime.strptime(date_str, "%Y/%m/%d/%H:%M")
        except ValueError:
            try:
                date_part, time_part_str = date_str.rsplit('/', 1)
                year, month, day = map(int, date_part.split('/'))
                hour, minute = map(int, time_part_str.split(':'))
                return datetime(year, month, day, hour, minute)
            except Exception:
                return None

    def _get_user_settings_path(self):
        if getattr(sys, 'frozen', False):
            appdata = os.getenv('APPDATA') or str(Path.home())
            config_dir = Path(appdata) / "時間割くんチェッカー"
            try:
                config_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            return config_dir / "user_settings.json"
        return self.parent.base_path / "user_settings.json"

    def _load_user_settings(self):
        path = self._get_user_settings_path()
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_user_settings(self):
        settings = {"last_opened_config": str(self.config_path) if self.config_path else None}
        path = self._get_user_settings_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"ユーザー設定の保存に失敗しました: {e}")

    def _select_config_file(self, prefer_last_opened=True):
        if prefer_last_opened and self.user_settings and "last_opened_config" in self.user_settings:
            last_config_path_str = self.user_settings.get("last_opened_config")
            if last_config_path_str:
                last_config_path = Path(last_config_path_str)
                if last_config_path.is_file():
                    try:
                        with open(last_config_path, 'r', encoding='utf-8') as f:
                            json.load(f)
                        return str(last_config_path)
                    except (json.JSONDecodeError, IOError):
                        pass

        base_path = self.parent.base_path
        search_dirs = {str(base_path.resolve()), str(Path(os.getcwd()).resolve())}
        
        possible_paths = set()
        for directory in search_dirs:
            try:
                for filename in os.listdir(directory):
                    if filename.endswith('.json') and not filename.endswith('user_settings.json'):
                        possible_paths.add(os.path.join(directory, filename))
            except OSError:
                continue
        
        valid_configs = []
        seen_paths = set()
        for path_str in possible_paths:
            path = Path(path_str).resolve()
            if path in seen_paths or not path.is_file(): continue
            
            seen_paths.add(path)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    valid_configs.append({
                        "path": str(path),
                        "school": data.get("SCHOOL_NAME", "（学校名未設定）"),
                        "date": data.get("LAST_UPDATE_DAY", "（更新日時なし）")
                    })
            except (json.JSONDecodeError, IOError):
                continue

        if not valid_configs:
            if self.parent.splash: self.parent.splash.hide()
            file_dialog = QFileDialog(self.parent, "設定ファイルを開く", "", "JSON Files (*.json)")
            file_dialog.setWindowFlags(file_dialog.windowFlags() | Qt.WindowStaysOnTopHint)
            icon_path = base_path / "時間割くんチェッカーアイコン.ico"
            if icon_path.exists(): file_dialog.setWindowIcon(QIcon(str(icon_path)))
            
            result = None
            if file_dialog.exec():
                result = file_dialog.selectedFiles()[0] if file_dialog.selectedFiles() else None
            if self.parent.splash: self.parent.splash.show()
            return result

        if len(valid_configs) == 1:
            return valid_configs[0]["path"]

        schools = {c["school"]: [] for c in valid_configs}
        for config in valid_configs: schools[config["school"]].append(config)

        school_names = sorted(schools.keys())
        school_dialog = ConfigSelectionDialog(self.parent, "学校の選択", "複数の設定ファイルが見つかりました。\n使用する学校を選択してください:", school_names)
        if not school_dialog.exec(): return None
        
        selected_school = school_dialog.get_selected_item()
        if not selected_school: return None

        configs_for_school = schools[selected_school]
        if len(configs_for_school) == 1:
            return configs_for_school[0]["path"]
        else:
            configs_for_school.sort(key=lambda x: x['date'], reverse=True)
            date_items = [f"{c['date']} ({os.path.basename(c['path'])})" for c in configs_for_school]
            date_dialog = ConfigSelectionDialog(self.parent, "バージョンの選択", f"「{selected_school}」の複数のバージョンが見つかりました。\n使用する更新日時を選択してください:", date_items)
            if not date_dialog.exec(): return None
            
            selected_date_item = date_dialog.get_selected_item()
            if not selected_date_item: return None

            for config in configs_for_school:
                if f"{config['date']} ({os.path.basename(config['path'])})" == selected_date_item:
                    return config['path']
        return None

class ThemeColors:
    """テーマカラーの定義"""
    def __init__(self, is_dark: bool):
        if is_dark:
            # ダークモードのカラー
            self.error = QColor(255, 80, 80)  # 明るい赤
            self.warning = QColor(255, 160, 60)  # 明るいオレンジ
            self.success = QColor(100, 255, 100)  # 明るい緑
            self.info = QColor(220, 220, 220)  # 明るい灰色
            self.background = QColor(45, 45, 45)  # 暗い背景
            self.text = QColor(220, 220, 220)  # 明るいテキスト
        else:
            # ライトモードのカラー
            self.error = QColor(200, 0, 0)  # 暗い赤
            self.warning = QColor(200, 100, 0)  # 暗いオレンジ
            self.success = QColor(0, 140, 0)  # 暗い緑
            self.info = QColor(60, 60, 60)  # 暗い灰色
            self.background = QColor(255, 255, 255)  # 白背景
            self.text = QColor(0, 0, 0)  # 黒テキスト


class ThemeManager:
    """UIのテーマとスタイルを管理するクラス"""
    def __init__(self, window):
        self.window = window
        self.is_dark_mode = darkdetect.theme() == "Dark"
        self.theme_colors = ThemeColors(self.is_dark_mode)

    def toggle_theme(self):
        """テーマを切り替える"""
        self.is_dark_mode = not self.is_dark_mode
        self.theme_colors = ThemeColors(self.is_dark_mode)
        self.apply_theme()

    def apply_theme(self):
        """現在のテーマを適用する"""
        try:
            if hasattr(self.window, 'theme_button'):
                self.window.theme_button.setText("ダークモード" if not self.is_dark_mode else "ライトモード")
        except Exception:
            pass

        # OSのウィンドウスタイルを尊重するため、全体パレットの上書きは行わない。
        # 色指定は下記の個別ウィジェット（例: QTextEdit）に限定する。

        # テキスト表示用の基本色を定義
        base_color = "#3C3C3C" if self.is_dark_mode else "#FFFFFF"
        text_color = self.theme_colors.text.name()
        mid_color = "#808080" # フォールバック用の中間色
        
        text_style = f"""
            QTextEdit {{
                background-color: {base_color};
                color: {text_color};
                border: 1px solid {mid_color};
            }}
        """
        try:
            self.window.details_text.setStyleSheet(text_style)
            self.window.move_text.setStyleSheet(text_style)
        except Exception:
            pass

        try:
            if hasattr(self.window, "details_text") and self.window.details_text.toPlainText():
                current_text = self.window.details_text.toHtml()
                self.window.details_text.setHtml(self._update_text_colors(current_text))
            if hasattr(self.window, "move_text") and self.window.move_text.toPlainText():
                current_text = self.window.move_text.toHtml()
                self.window.move_text.setHtml(self._update_text_colors(current_text))
        except Exception:
            pass

    def _update_text_colors(self, html_text: str) -> str:
        """HTMLテキストの色を現在のテーマに合わせて更新"""
        colors = {
            "red": self.theme_colors.error.name(),
            "darkred": self.theme_colors.error.name(),
            "orange": self.theme_colors.warning.name(),
            "green": self.theme_colors.success.name(),
            "black": self.theme_colors.text.name(),
        }

        for old_color, new_color in colors.items():
            html_text = html_text.replace(f'color: {old_color}', f'color: {new_color}')
        return html_text

    def format_error_text(self, text: str, color_name: str) -> str:
        """エラーメッセージに色を付ける"""
        color = None
        if color_name == "red" or color_name == "darkred":
            color = self.theme_colors.error
        elif color_name == "orange":
            color = self.theme_colors.warning
        elif color_name == "green":
            color = self.theme_colors.success
        else:
            color = self.theme_colors.text
        return f'<span style="color: {color.name()};">{text}</span>'


class TimetableChecker(QMainWindow):
    def __init__(self, splash=None):
        super().__init__()
        self.splash = splash
        self._exit_requested = False

        # 1. パスの確定
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.base_path = Path(sys._MEIPASS)
        else:
            self.base_path = Path(__file__).resolve().parent

        # 2. ConfigManagerを通じて設定を読み込む
        self.config_manager = ConfigManager(self)
        self.config = self.config_manager.load_and_get_config()
        
        # 3. 設定読み込みの成否をチェック
        if self.config is None:
            self._exit_requested = True
            return
            
        self.config_path = self.config_manager.config_path
        self.user_settings = self.config_manager.user_settings

        # 4. UI構築
        self._init_ui()

    def is_exit_requested(self):
        return self._exit_requested

    def changeEvent(self, event):
        """テーマ変更を動的に反映する。"""
        if event.type() == QEvent.ThemeChange:
            # テーマ状態を更新
            if hasattr(self, 'theme_manager'):
                self.theme_manager.is_dark_mode = darkdetect.theme() == "Dark"
                self.theme_manager.theme_colors = ThemeColors(self.theme_manager.is_dark_mode)
                self.theme_manager.apply_theme()
            
            # ボタンスタイルを更新
            set_button_styles(QApplication.instance())
            
        super().changeEvent(event)

    def _init_ui(self):
        self.setWindowTitle("時間割チェッカー")
        self.resize(600, 400)
        self.setAcceptDrops(True)  # ドラッグ＆ドロップを有効化

        # ウィンドウアイコンを設定
        icon_path = self.base_path / "時間割くんチェッカーアイコン.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # 初期設定
        self._cancel_requested = False
        self.theme_manager = ThemeManager(self)
        self.department_selector = DepartmentSelector(self)

        # メインウィジェットとレイアウトの設定
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 学科選択ボタン
        dept_layout = QHBoxLayout()
        self.dept_select_button = QPushButton("学科を選択")
        self.dept_label = QLabel() # ラベルを先に作成
        dept_layout.addWidget(self.dept_select_button)
        dept_layout.addWidget(self.dept_label)
        dept_layout.addStretch()
        self.main_layout.addLayout(dept_layout)

        # ファイル選択ボタン
        select_button = QPushButton("時間割ファイルを選択")
        select_button.clicked.connect(self.select_files)
        self.main_layout.addWidget(select_button)

        # プログレスバー＆キャンセルボタンのレイアウト
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.main_layout.addLayout(progress_layout)

        horizontal_layout = QHBoxLayout()

        # フォント設定コントロール（サイズ・等幅）
        font_ctrl_layout = QHBoxLayout()
        font_ctrl_layout.addWidget(QLabel("フォントサイズ:"))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 40)
        self.font_size_spin.setValue(10)
        font_ctrl_layout.addWidget(self.font_size_spin)
        font_ctrl_layout.addStretch()

        # 単位数下限設定
        units_ctrl_layout = QHBoxLayout()
        units_ctrl_layout.addWidget(QLabel("最小単位数:"))
        self.min_units_spinbox = QSpinBox()
        self.min_units_spinbox.setRange(0, 100)
        self.min_units_spinbox.setValue(80)
        units_ctrl_layout.addWidget(self.min_units_spinbox)
        units_ctrl_layout.addStretch()

        horizontal_layout.addLayout(font_ctrl_layout)
        horizontal_layout.addLayout(units_ctrl_layout)
        horizontal_layout.addStretch()

        self.main_layout.addLayout(horizontal_layout)

        # --- Dry-Run モード & CSVエクスポート ---
        options_layout = QHBoxLayout()
        self.dry_run_checkbox = QCheckBox("ファイルを移動せずにレポートのみ作成 (Dry Run)")
        self.dry_run_checkbox.setChecked(True)  # デフォルトでDry-Run有効
        self.dry_run_checkbox.stateChanged.connect(self._update_move_tab_title)
        options_layout.addWidget(self.dry_run_checkbox)
        
        self.export_csv_button = QPushButton("CSVレポート出力")
        self.export_csv_button.clicked.connect(self._export_csv_report)
        self.export_csv_button.setEnabled(False)  # 結果が出るまで無効
        options_layout.addWidget(self.export_csv_button)
        options_layout.addStretch()
        self.main_layout.addLayout(options_layout)

        # --- サマリーダッシュボード ---
        self.summary_group = QGroupBox("検証結果サマリー")
        summary_layout = QHBoxLayout(self.summary_group)
        self.total_label = QLabel("処理件数: -")
        self.passed_label = QLabel("合格: -")
        self.passed_label.setStyleSheet("color: green; font-weight: bold;")
        self.failed_label = QLabel("不合格: -")
        self.failed_label.setStyleSheet("color: red; font-weight: bold;")
        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(self.passed_label)
        summary_layout.addWidget(self.failed_label)
        summary_layout.addStretch()
        self.main_layout.addWidget(self.summary_group)
        
        # 最後の検証結果を保持（CSVエクスポート用）
        self._last_results = {}
        self._last_files = []

        # 結果表示用タブ
        self.tab_widget = QTabWidget()

        # 移動結果タブのウィジェットとレイアウト
        move_widget = QWidget()
        move_layout = QVBoxLayout(move_widget)
        self.move_text = QTextEdit()
        self.move_text.setReadOnly(True)
        move_layout.addWidget(self.move_text)
        # コピーボタン（移動結果）
        copy_move_button = QPushButton("移動結果をコピー")
        copy_move_button.clicked.connect(lambda: self._copy_text_to_clipboard(self.move_text))
        move_layout.addWidget(copy_move_button)

        # 詳細タブのウィジェットとレイアウト
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        # コピーボタン（詳細）
        copy_details_button = QPushButton("詳細をコピー")
        copy_details_button.clicked.connect(lambda: self._copy_text_to_clipboard(self.details_text))
        details_layout.addWidget(copy_details_button)

        # 行折り返しをウィジェット幅に設定
        try:
            self.details_text.setLineWrapMode(QTextEdit.WidgetWidth)
            self.move_text.setLineWrapMode(QTextEdit.WidgetWidth)
        except Exception:
            pass

        # タブの追加（初期状態は"移動予定"）
        self._move_tab_title_base = "移動予定" if self.dry_run_checkbox.isChecked() else "移動結果"
        self.tab_widget.addTab(move_widget, self._move_tab_title_base)
        self.tab_widget.addTab(details_widget, "詳細")
        self.main_layout.addWidget(self.tab_widget)

        # フォント適用初期化
        self._monospace = False
        self.font_size_spin.valueChanged.connect(self._update_font_size)
        self._apply_font(self._monospace, self.font_size_spin.value())
        
        # --- 処理の最後にUIの初期化と接続を行う ---
        self.department_selector.initialize()
        self.dept_select_button.clicked.connect(self.department_selector.change_department)
        
        # 初期テーマを適用
        self.theme_manager.apply_theme()

    def select_files(self):
        """時間割ファイルを選択して検証を実行"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "時間割ファイルを選択",
            "",
            "Excel Files (*.xlsx *.xlsm)"
        )
        
        if not files:
            return
        
        # すべてのファイルが存在し、アクセス可能か確認
        inaccessible_files = []
        for file_path in files:
            if not os.path.exists(file_path):
                self.details_text.setHtml(
                    self.theme_manager.format_error_text(f"ファイルが見つかりません: {file_path}", "red")
                )
                return
            try:
                with open(file_path, 'rb'):
                    pass
            except IOError:
                inaccessible_files.append(file_path)
        
        if inaccessible_files:
            error_msg = "以下のファイルにアクセスできません（他のプロセスで使用中の可能性があります）:<br>" + \
                       "<br>".join(self.theme_manager.format_error_text(f, "red") for f in inaccessible_files)
            self.details_text.setHtml(error_msg)
            return
            
        # ファイル処理を実行
        self.process_files(files)
        return

    def _apply_font(self, monospace: bool, size: int):
        """結果表示用テキストとアプリにフォントを適用する"""
        font = QApplication.font()
        font.setPointSize(size)
        QApplication.setFont(font)
        try:
            if monospace:
                fm = QFontDatabase.systemFont(QFontDatabase.FixedFont)
                font = QFont(fm.family(), size)
            else:
                font = QFont()
                font.setPointSize(size)

            self.details_text.setFont(font)
            self.move_text.setFont(font)
        except Exception:
            # フォントAPIが使えない環境では無視
            pass

    def _update_font_size(self, val: int):
        self._apply_font(self._monospace, val)

    def _toggle_monospace(self, checked: bool):
        self._monospace = checked
        self._apply_font(self._monospace, self.font_size_spin.value())

    def _copy_text_to_clipboard(self, text_edit: QTextEdit):
        """指定されたQTextEditの内容をクリップボードにコピーする"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text_edit.toPlainText())


    def dragEnterEvent(self, event: QDragEnterEvent):
        """ドラッグされたファイルを受け入れるかどうかを判断"""
        if event.mimeData().hasUrls():
            # Excelファイルのみを受け入れる
            urls = event.mimeData().urls()
            if all(url.toLocalFile().lower().endswith(('.xlsx', '.xlsm')) for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """ドロップされたファイルを処理"""
        urls = event.mimeData().urls()
        files = [url.toLocalFile() for url in urls]
        self.process_files(files)

    def process_files(self, files: list):
        """ファイルをバックグラウンドで処理し、結果をUIに表示する"""
        self._cancel_requested = False
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(files))
        self.progress_bar.setValue(0)

        validator = TimetableValidator(self.config)
        
        def validate_file_job(file_path):
            if self._cancel_requested:
                return file_path, None
            
            hierarchy_to_check = self.selected_hierarchy if self.selected_hierarchy is not None else self.config.get("YEARS_HIERARCHY", {})
            min_units = self.min_units_spinbox.value()
            
            errors = validator.validate(file_path, hierarchy_to_check, self.selected_department_path, min_units)
            return file_path, errors

        all_results = {}
        max_workers = min(os.cpu_count() or 1, len(files))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(validate_file_job, fp): fp for fp in files}
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_file), 1):
                if self._cancel_requested:
                    executor.shutdown(wait=False, cancel_futures=True)
                    self.details_text.setHtml("処理がキャンセルされました。")
                    self.progress_bar.setVisible(False)
                    return
                
                file_path, errors = future.result()
                if errors is not None:
                    all_results[file_path] = errors
                self.progress_bar.setValue(i)

        self._format_and_display_results(all_results, files)
        self.progress_bar.setVisible(False)

    def _format_and_display_results(self, all_results: dict, original_files: list):
        """検証結果をフォーマットし、UIに表示およびファイル移動を行う"""
        invalid_files_with_errors = {fp: errs for fp, errs in all_results.items() if errs}
        
        # 結果を保持（CSVエクスポート用）
        self._last_results = all_results
        self._last_files = original_files
        
        # サマリーダッシュボード更新
        total_count = len(original_files)
        failed_count = len(invalid_files_with_errors)
        passed_count = total_count - failed_count
        self.total_label.setText(f"処理件数: {total_count}")
        self.passed_label.setText(f"合格: {passed_count}")
        self.failed_label.setText(f"不合格: {failed_count}")
        
        # CSVエクスポートボタンを有効化
        self.export_csv_button.setEnabled(True)
        
        # ログ出力
        logger.info(f"検証完了: 合計 {total_count} 件, 合格 {passed_count} 件, 不合格 {failed_count} 件")
        
        if not invalid_files_with_errors:
            self.details_text.setHtml(self.theme_manager.format_error_text("すべてのファイルが正常でした。", "green"))
            self.move_text.setHtml("")
            return

        # --- 詳細タブのメッセージ作成 ---
        details_lines = ["<html>", self.theme_manager.format_error_text("以下のファイルに問題が見つかりました:", "black"), "<br>不正なファイルの詳細:"]
        for file_path, errors in invalid_files_with_errors.items():
            file_name = os.path.basename(file_path)
            details_lines.append(f"<br><br><b>{file_name}:</b>")
            for error in errors:
                if error['type'] == 'file_read_error':
                    err_detail = error['details']
                    details_lines.append(f"<br>{self.theme_manager.format_error_text(f'ファイル読み込みエラー: {err_detail}', 'darkred')}")
                elif error['type'] == 'cell_read_error':
                    err_detail = error['details']
                    details_lines.append(f"<br>{self.theme_manager.format_error_text(f'セル読み取りエラー: {err_detail}', 'red')}")
                elif error['type'] == 'units_insufficient':
                    d = error['details']
                    current_units = d['current']
                    required_units = d['required']
                    details_lines.append(f"<br>{self.theme_manager.format_error_text(f'総単位数不足: {current_units} / {required_units} 単位', 'red')}")
                elif error['type'] == 'required_missing':
                    year_info = error['details']['year']
                    details_lines.append(f"<br>{self.theme_manager.format_error_text(f'必須科目不足 ({year_info}):', 'orange')}")
                    details_lines.append(self._format_missing_subjects_message(error['details']['missing']))
                elif error['type'] == 'prereq_missing':
                    prereq_msg = [f"{m['subject']} には {', '.join(m['requires'])} が必要です" for m in error['details']]
                    details_lines.append(f"<br>{self.theme_manager.format_error_text('前提科目不足:', 'red')}<br>" + "<br>".join(prereq_msg))
        details_lines.append("</html>")
        self.details_text.setHtml("\n".join(details_lines))

        # --- 移動タブのメッセージ作成（Dry-Runモード対応） ---
        is_dry_run = self.dry_run_checkbox.isChecked()
        invalid_folder = os.path.join(os.path.dirname(original_files[0]), "不正な時間割")
        
        if is_dry_run:
            # Dry-Runモード：移動予定のみ表示（移動先は表示しない）
            move_lines = ["<html>", "<br><b>Dry-Run モード: ファイルは移動されません</b>"]
            move_lines.append(f"<br><br>以下の {len(invalid_files_with_errors)} 個のファイルに問題があります:")
            for file_path in invalid_files_with_errors.keys():
                file_name = os.path.basename(file_path)
                move_lines.append(f"<br>• {file_name}")
            move_lines.append("</html>")
            logger.info(f"Dry-Run: {len(invalid_files_with_errors)} 個のファイルに問題あり")
        else:
            # 実際にファイルを移動
            os.makedirs(invalid_folder, exist_ok=True)
            move_lines = ["<html>", "<br>移動結果:"]
            move_success, move_failed = [], []
            
            for file_path in invalid_files_with_errors.keys():
                file_name = os.path.basename(file_path)
                try:
                    new_path = os.path.join(invalid_folder, file_name)
                    if os.path.exists(new_path):
                        base, ext = os.path.splitext(file_name)
                        counter = 1
                        new_path = os.path.join(invalid_folder, f"{base}_{counter}{ext}")
                        while os.path.exists(new_path):
                            counter += 1
                            new_path = os.path.join(invalid_folder, f"{base}_{counter}{ext}")
                    shutil.move(file_path, new_path)
                    move_success.append(file_name)
                    logger.info(f"ファイル移動: {file_name} -> {new_path}")
                except Exception as e:
                    move_failed.append((file_name, str(e)))
                    logger.error(f"ファイル移動失敗: {file_name}: {e}")

            if move_success:
                move_lines.append(self.theme_manager.format_error_text(f"<br>{len(move_success)}個のファイルが {invalid_folder} に移動されました。", "green"))
            if move_failed:
                move_lines.append(self.theme_manager.format_error_text("<br>以下のファイルは移動できませんでした:", "red"))
                for fname, reason in move_failed:
                    move_lines.append(f"<br>{fname}: {reason}")
            move_lines.append("</html>")
        
        self.move_text.setHtml("\n".join(move_lines))

    def _format_missing_subjects_message(self, missing_info):
        """必須科目の不足情報をフォーマットする"""
        if not missing_info: return ""
        grouped = {}
        for item in missing_info:
            source = item.get('source_type', '不明')
            grouped.setdefault(source, {}).setdefault(str(item['condition_num']), []).append(item)

        messages = []
        for source in sorted(grouped.keys()):
            try: sorted_groups = sorted(grouped[source].items(), key=lambda x: int(x[0]))
            except (ValueError, TypeError): sorted_groups = sorted(grouped[source].items())
            
            cond_counter = 1
            for _, items in sorted_groups:
                if not items: continue
                is_or = items[0].get('is_or_group', False)
                
                messages.append(f"--- {source} 条件 {cond_counter} ---")
                if is_or:
                    sorted_items = sorted(items, key=lambda x: x['subjects'][0] if x.get('subjects') else "")
                    for item in sorted_items:
                        subjects_str = ", ".join(item.get('subjects', []))
                        messages.append(f"  - {subjects_str} (現在: {item.get('matched', 0)} / 必要: {item.get('required', 1)})")
                else:
                    for item in items:
                        subjects_str = ", ".join(item.get('subjects', []))
                        messages.append(f"- 教科: {subjects_str} (現在: {item.get('matched', 0)} / 必要: {item.get('required', 1)})")
                cond_counter += 1
        return "<br>" + "<br>".join(messages).replace("\n", "<br>")

    def _update_move_tab_title(self):
        """Dry-Runチェックボックスの状態に応じてタブタイトルを更新"""
        if self.dry_run_checkbox.isChecked():
            self.tab_widget.setTabText(0, "移動予定")
        else:
            self.tab_widget.setTabText(0, "移動結果")
    
    def _export_csv_report(self):
        """検証結果をCSVファイルにエクスポート"""
        if not self._last_results:
            QMessageBox.information(self, "情報", "エクスポートするデータがありません。先に検証を実行してください。")
            return
        
        # ファイル保存ダイアログ
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "CSVレポートを保存",
            f"検証レポート_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                # ヘッダー行
                writer.writerow(["ファイル名", "ステータス", "エラー種別", "エラー詳細", "学科パス"])
                
                # データ行
                for file_path_key in self._last_files:
                    file_name = os.path.basename(file_path_key)
                    errors = self._last_results.get(file_path_key, [])
                    
                    if not errors:
                        writer.writerow([file_name, "合格", "", "", self.selected_department_path])
                    else:
                        for error in errors:
                            error_type = error.get('type', '不明')
                            error_details = self._format_error_for_csv(error)
                            writer.writerow([file_name, "不合格", error_type, error_details, self.selected_department_path])
            
            logger.info(f"CSVレポート出力: {file_path}")
            QMessageBox.information(self, "完了", f"CSVレポートを保存しました:\n{file_path}")
        except Exception as e:
            logger.error(f"CSVエクスポート失敗: {e}")
            QMessageBox.critical(self, "エラー", f"CSV保存に失敗しました:\n{e}")
    
    def _format_error_for_csv(self, error: dict) -> str:
        """エラー情報をCSV用のプレーンテキストに変換"""
        error_type = error.get('type', '')
        details = error.get('details', '')
        
        if error_type == 'file_read_error':
            return f"ファイル読み込みエラー: {details}"
        elif error_type == 'cell_read_error':
            return f"セル読み取りエラー: {details}"
        elif error_type == 'units_insufficient':
            if isinstance(details, dict):
                return f"総単位数不足: {details.get('current', '?')} / {details.get('required', '?')} 単位"
            return str(details)
        elif error_type == 'required_missing':
            if isinstance(details, dict):
                year = details.get('year', '?')
                missing = details.get('missing', [])
                return f"必須科目不足 ({year}): {len(missing)} 条件未達成"
            return str(details)
        elif error_type == 'prereq_missing':
            if isinstance(details, list):
                msgs = [f"{m.get('subject', '?')}には{', '.join(m.get('requires', []))}が必要" for m in details]
                return "; ".join(msgs)
            return str(details)
        return str(details)
        

def start_main_app():
    """時間割チェッカー本体のエントリーポイント。"""
    import tempfile
    
    app = QApplication(sys.argv)
    set_button_styles(app)

    # スプラッシュ画面は外部ランチャーが扱うためTimetableCheckerにはNoneを渡す。
    window = TimetableChecker(splash=None)

    if hasattr(window, 'is_exit_requested') and window.is_exit_requested():
        sys.exit(0)
    
    window.show()
    
    # IPC: メインウィンドウの準備完了をランチャーへ通知
    ipc_ready_file = Path(tempfile.gettempdir()) / "timetablechecker_ready.tmp"
    try:
        ipc_ready_file.touch()
        print(f"IPC: Created ready signal file at {ipc_ready_file}")
    except Exception as e:
        print(f"IPC: Failed to create ready signal file: {e}")
    
    sys.exit(app.exec())
    
if __name__ == '__main__':
    start_main_app()

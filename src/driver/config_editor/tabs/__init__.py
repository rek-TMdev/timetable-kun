# config_editor.tabs package
"""
タブウィジェットパッケージ

config_editor_main.pyのMainWindowから分離された各設定タブを提供します。
各タブはBaseTabを継承し、統一されたインターフェースを持ちます。
"""

from .base_tab import BaseTab
from .master_subject_tab import MasterSubjectTab
from .alias_tab import AliasTab
from .prerequisite_tab import PrerequisiteTab
from .no_together_tab import NoTogetherTab
from .general_settings_tab import GeneralSettingsTab
from .save_position_tab import SavePositionTab
from .year_settings_tab import YearSettingsTab
from .required_subjects_tab import RequiredSubjectsTab
from .subject_details_tab import SubjectDetailsTab
from .layout_tab import LayoutTab

__all__ = [
    'BaseTab',
    'MasterSubjectTab',
    'AliasTab',
    'PrerequisiteTab',
    'NoTogetherTab',
    'GeneralSettingsTab',
    'SavePositionTab',
    'YearSettingsTab',
    'RequiredSubjectsTab',
    'SubjectDetailsTab',
    'LayoutTab',
]

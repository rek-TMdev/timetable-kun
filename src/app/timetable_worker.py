"""
TimetableWorker - 時間割生成をバックグラウンドで実行するワーカークラス

UIフリーズを防ぐため、時間割の組み合わせ生成をQThreadで実行します。
進捗状況の通知とキャンセル機能をサポートします。

Note:
    このワーカーはTimetableLogic.generate_timetablesを使用して時間割を生成します。
    スレッド管理の責務とアルゴリズムの責務が分離されています。
"""
from PySide6.QtCore import QThread, Signal
from timetable_logic import TimetableLogic


class TimetableWorker(QThread):
    """
    時間割生成をバックグラウンドで実行するワーカー。
    
    責務:
    - QThreadによるバックグラウンド実行
    - 進捗状況の通知（Signalを使用）
    - キャンセル機能
    
    Note:
        実際の時間割生成アルゴリズムはTimetableLogicに委譲します。
    
    Signals:
        progress: 進捗状況 (見つかった組み合わせ数)
        finished_with_results: 生成完了 (結果リスト, 学年ラベル, 必含選択科目リスト)
        error: エラー発生 (エラーメッセージ)
    """
    # シグナル定義
    progress = Signal(int)  # 見つかった組み合わせ数
    finished_with_results = Signal(list, str, list)  # (結果, year_label, important_subjects)
    error = Signal(str)  # エラーメッセージ
    
    def __init__(
        self,
        selected_subjects: dict,
        fixed_slots: dict,
        all_slots: list,
        year_label: str,
        important_subjects: list,
        norm_to_raw_map: dict,
        max_limit: int,
        filter_settings: dict,
        unit_data: dict,
        parent=None
    ):
        """
        TimetableWorkerを初期化します。
        
        Args:
            selected_subjects: 選択された教科 {正規化名: [スロットリスト]}
            fixed_slots: 固定スロット {スロット名: 教科名}
            all_slots: 使用可能な全スロットのリスト
            year_label: 学年ラベル
            important_subjects: 必須で含める教科リスト
            norm_to_raw_map: 正規化名から元の名前へのマップ
            max_limit: 最大生成数
            filter_settings: フィルタリング設定
            unit_data: 単位計算用データ
            parent: 親オブジェクト
        """
        super().__init__(parent)
        self.selected_subjects = selected_subjects
        self.fixed_slots = fixed_slots
        self.all_slots = all_slots
        self.year_label = year_label
        self.important_subjects = important_subjects
        self.norm_to_raw_map = norm_to_raw_map
        self.max_limit = max_limit
        self.filter_settings = filter_settings
        self.unit_data = unit_data
        
        self._is_cancelled = False
    
    def cancel(self):
        """生成をキャンセルする"""
        self._is_cancelled = True
    
    def run(self):
        """バックグラウンドで時間割生成を実行"""
        try:
            results = []
            count = 0
            
            # フィルタ設定を変換
            filters = {
                'ACTIVE_FILTER_SUBJECT': self.filter_settings.get('active_filter_subject', False),
                'ACTIVE_FILTER_SUBJECT_AMOUNT': self.filter_settings.get('active_filter_subject_amount', False),
                'ACTIVE_MIN_SUBJECT': self.filter_settings.get('active_min_subject', False),
                'ACTIVE_MAX_SUBJECT': self.filter_settings.get('active_max_subject', False),
                'ACTIVE_FILTER_SUBJECT_UNITS': self.filter_settings.get('active_filter_subject_units', False),
                'ACTIVE_MIN_SUBJECT_UNITS': self.filter_settings.get('active_min_subject_units', False),
                'ACTIVE_MAX_SUBJECT_UNITS': self.filter_settings.get('active_max_subject_units', False),
                'MIN_SUBJECT_COUNT': self.filter_settings.get('min_subject_count', 0),
                'MAX_SUBJECT_COUNT': self.filter_settings.get('max_subject_count', 100),
                'MIN_UNITS': self.filter_settings.get('min_subject_units', 0),
                'MAX_UNITS': self.filter_settings.get('max_subject_units', 1000),
            }
            
            # TimetableLogic.generate_timetablesのパラメータを作成
            params = {
                'selected_subjects': self.selected_subjects,
                'fixed_slots': self.fixed_slots,
                'all_slots': self.all_slots,
                'important_subjects': self.important_subjects,
                'norm_to_raw_map': self.norm_to_raw_map,
                'filters': filters,
                'unit_data': self.unit_data,
            }
            
            # TimetableLogicのジェネレータを使用して時間割を生成
            for timetable in TimetableLogic.generate_timetables(params):
                if self._is_cancelled:
                    break
                
                results.append(timetable)
                count += 1
                
                # 100件ごとに進捗を通知
                if count % 100 == 0:
                    self.progress.emit(count)
                
                if count >= self.max_limit:
                    break
            
            if not self._is_cancelled:
                self.finished_with_results.emit(results, self.year_label, self.important_subjects)
        except Exception as e:
            self.error.emit(str(e))

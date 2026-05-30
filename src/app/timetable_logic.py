import unicodedata
from collections import Counter

class TimetableLogic:
    """
    時間割の生成、検証、計算に関するビジネスロジックをカプセル化するクラス。
    このクラスは状態を持たず、すべてのメソッドは静的メソッドとして実装され、
    必要なデータはすべて引数として受け取ります。
    """

    @staticmethod
    def normalize_subject_name(name: str | None) -> str | None:
        """
        教科名を正規化する。半角カナ、全角英数を半角に統一し、小文字に変換する。
        """
        if not isinstance(name, str):
            return None
        # 全角英数を半角に、半角カタカナを全角カタカナに変換後、再度カタカナを半角に変換
        # NFKC正規化で、一般的な文字種を統一
        normalized = unicodedata.normalize('NFKC', name)
        return normalized.strip().lower()

    @staticmethod
    def _calculate_units_for_list(subjects_list, abnormal_units_general, all_year_abnormal_units):
        """
        与えられた教科リストの単位数を計算する (コマ数基準 + 特別単位)
        - subjects_list: 単位計算対象の正規化済み教科名リスト
        - abnormal_units_general: 全学年共通の特別単位数データ
        - all_year_abnormal_units: 全学年の特別単位数データのリスト
        """
        subject_counts = Counter(subjects_list)
        total_units = 0
        
        for subject, count in subject_counts.items():
            total_units += count
            
            if subject in abnormal_units_general:
                total_units += abnormal_units_general[subject]
            else:
                for year_abnormal_units in all_year_abnormal_units:
                    if subject in year_abnormal_units:
                        total_units += year_abnormal_units[subject]
        return total_units

    @staticmethod
    def calculate_timetable_units(timetable, year_fixed_slots, include_fixed_subjects, abnormal_units_general, all_year_abnormal_units):
        """
        時間割の単位数を計算し、オプションで固定単位数を加算する
        """
        subjects_in_timetable = [
            TimetableLogic.normalize_subject_name(s) for s in timetable.values() 
            if s and s.strip() not in ["－", "-", ""]
        ]
        
        fixed_subjects_list = [TimetableLogic.normalize_subject_name(s) for s in year_fixed_slots.values() if s and s.strip() not in ["－", "-", ""]]
        fixed_subjects_set = set(fixed_subjects_list)
        
        subjects_to_calculate = [s for s in subjects_in_timetable if s not in fixed_subjects_set]
        
        units = TimetableLogic._calculate_units_for_list(subjects_to_calculate, abnormal_units_general, all_year_abnormal_units)
        
        if include_fixed_subjects:
            fixed_units = TimetableLogic._calculate_units_for_list(fixed_subjects_list, abnormal_units_general, all_year_abnormal_units)
            units += fixed_units
            
        return units

    @staticmethod
    def calculate_total_units(
        base_units: int,
        years: list,
        year_data: dict,
        active_profile: str,
        art_selections: dict,
        abnormal_units_general: dict
    ) -> int:
        """
        全学年の総単位数を計算する。
        
        Args:
            base_units: 基礎単位数
            years: 学年リスト
            year_data: 学年ごとのデータ
            active_profile: アクティブなプロファイル名
            art_selections: 芸術科目選択データ {profile_name: [subjects]}
            abnormal_units_general: 全学年共通の特別単位数データ
            
        Returns:
            総単位数
        """
        all_saved_subjects = []
        all_fixed_subjects = []
        all_year_abnormal_units = []
        
        for year in years:
            # ユーザーが選択した教科
            timetable = year_data[year].get("saved_profiles", {}).get(active_profile, {})
            all_saved_subjects.extend([
                s for s in timetable.values() 
                if s and s.strip() not in ["－", "-", ""]
            ])
            # 固定教科
            fixed_slots = year_data[year].get("fixed_slots", {})
            all_fixed_subjects.extend([
                s for s in fixed_slots.values() 
                if s and s.strip() not in ["－", "-", ""]
            ])
            # 学年ごとの特別単位数
            year_abnormal = year_data[year].get("abnormal_units", {})
            all_year_abnormal_units.append(year_abnormal)
        
        # 芸術科目を追加
        art_for_profile = art_selections.get(active_profile, [])
        all_saved_subjects.extend([s for s in art_for_profile if s])
        
        # 正規化
        norm_saved = [TimetableLogic.normalize_subject_name(s) for s in all_saved_subjects]
        norm_fixed = [TimetableLogic.normalize_subject_name(s) for s in all_fixed_subjects]
        
        # 二重カウント防止
        unique_saved = [s for s in norm_saved if s not in norm_fixed]
        
        # 単位計算
        fixed_units = TimetableLogic._calculate_units_for_list(
            norm_fixed, abnormal_units_general, all_year_abnormal_units
        )
        saved_units = TimetableLogic._calculate_units_for_list(
            unique_saved, abnormal_units_general, all_year_abnormal_units
        )
        
        return base_units + fixed_units + saved_units

    @staticmethod
    def check_prerequisites(timetable, art_subjects, prerequisite_config):
        """
        前提科目の不足をチェックする
        - timetable: 時間割データ {slot: raw_subject_name}
        - art_subjects: 選択された芸術科目のraw_subject_nameのセット
        - prerequisite_config: 前提科目の設定データ {raw_subject_name: [raw_prereq_name, ...]}
        """
        missing = {}
        
        # Create a set of all selected subjects, normalized for lookup.
        all_subjects_raw = set(timetable.values()).union(art_subjects)
        all_subjects_norm = {TimetableLogic.normalize_subject_name(s) for s in all_subjects_raw if s}

        # Iterate through the raw subject names to check their prereqs
        for subject_raw in all_subjects_raw:
            if not subject_raw: continue
            
            # Config keys are raw names
            if subject_raw in prerequisite_config:
                prereqs_raw = prerequisite_config[subject_raw]
                missing_reqs = []
                for prereq_raw in prereqs_raw:
                    if TimetableLogic.normalize_subject_name(prereq_raw) not in all_subjects_norm:
                        missing_reqs.append(prereq_raw) # append raw name for display
                
                if missing_reqs:
                    missing[subject_raw] = missing_reqs
        return missing

    @staticmethod
    def get_no_together_conflicts(all_subjects_norm, no_together_config):
        """
        同時履修不可の組み合わせをチェックし、競合している教科のセットを返す
        - all_subjects_norm: 選択されているすべての正規化済み教科名のセット
        - no_together_config: 同時履修不可設定データ
        """
        conflicting_subjects = set()
        for subject_group_raw in no_together_config:
            group_norm = {TimetableLogic.normalize_subject_name(s) for s in subject_group_raw}
            
            selected_in_group = all_subjects_norm.intersection(group_norm)
            
            if len(selected_in_group) > 1:
                conflicting_subjects.update(selected_in_group)
        return conflicting_subjects

    @staticmethod
    def get_prerequisite_highlight_targets(all_subjects_norm, prerequisite_config):
        """
        不足している前提科目を特定し、ハイライト対象となる教科のセットを返す
        - all_subjects_norm: 選択されているすべての正規化済み教科名のセット
        - prerequisite_config: 前提科目の設定データ {raw_subject_name: [raw_prereq_name, ...]}
        """
        prerequisite_targets = set()
        
        # 設定ファイルの前提科目もすべて正規化して、正規化済みセットと比較する
        # {norm_main_subj: [norm_prereq1, ...]} の辞書を作成
        norm_prereq_config = {
            TimetableLogic.normalize_subject_name(main_subj): [TimetableLogic.normalize_subject_name(p) for p in prereqs]
            for main_subj, prereqs in prerequisite_config.items()
        }

        for main_subject_norm, prereqs_norm in norm_prereq_config.items():
            if main_subject_norm in all_subjects_norm:
                for prereq_norm in prereqs_norm:
                    if prereq_norm not in all_subjects_norm:
                        prerequisite_targets.add(prereq_norm)
        return prerequisite_targets

    @staticmethod
    def generate_timetables(params):
        """
        時間割の組み合わせを生成するジェネレータ。
        params: 必要なすべてのデータを含む辞書
        """
        # Unpack parameters
        selected_subjects = params['selected_subjects']
        fixed_slots = params['fixed_slots']
        all_slots = params['all_slots']
        important_subjects = params['important_subjects']
        norm_to_raw_map = params['norm_to_raw_map']
        filters = params['filters']
        unit_data = params['unit_data']

        class ScheduleState:
            __slots__ = ['timetable', 'used_slots', 'remaining_subjects']

            def __init__(self, fixed_slots):
                self.timetable = {slot: subj for slot, subj in fixed_slots.items() if subj and subj.strip() not in ["－", "-", ""]}
                self.used_slots = set(slot for slot, subj in fixed_slots.items() if subj and subj.strip() not in ["－", "-", ""])
                self.remaining_subjects = []

            def clone(self):
                new_state = ScheduleState({})
                new_state.timetable = self.timetable.copy()
                new_state.used_slots = set(self.used_slots)
                new_state.remaining_subjects = list(self.remaining_subjects)
                return new_state

        def can_assign(slots, used_slots):
            return all(slot in all_slots and slot not in used_slots for slot in slots)

        def backtrack_generator(state):
            if not state.remaining_subjects:
                current_subjects_raw = [norm_to_raw_map.get(s) for s in state.timetable.values() if s]
                
                units = TimetableLogic._calculate_units_for_list(
                    list(state.timetable.values()), # Pass normalized names
                    unit_data['abnormal_units_general'],
                    unit_data['all_year_abnormal_units']
                )

                unique_subjects_in_combination = set(state.timetable.values())
                subject_count = len(unique_subjects_in_combination)
                all_important_included = all(subj in unique_subjects_in_combination for subj in important_subjects)

                if all_important_included or not important_subjects:
                    count_ok = (
                        not filters['ACTIVE_FILTER_SUBJECT_AMOUNT'] or
                        (not filters['ACTIVE_MIN_SUBJECT'] or subject_count >= filters['MIN_SUBJECT_COUNT']) and
                        (not filters['ACTIVE_MAX_SUBJECT'] or subject_count <= filters['MAX_SUBJECT_COUNT'])
                    )
                    units_ok = (
                        not filters['ACTIVE_FILTER_SUBJECT_UNITS'] or
                        (not filters['ACTIVE_MIN_SUBJECT_UNITS'] or units >= filters['MIN_UNITS']) and
                        (not filters['ACTIVE_MAX_SUBJECT_UNITS'] or units <= filters['MAX_UNITS'])
                    )
                    if not filters['ACTIVE_FILTER_SUBJECT'] or (count_ok and units_ok):
                        yield {slot: norm_to_raw_map.get(norm_name, norm_name) for slot, norm_name in state.timetable.items()}
                return

            current_subject = state.remaining_subjects[0]
            if not current_subject:
                state.remaining_subjects.pop(0)
                yield from backtrack_generator(state)
                return

            next_subjects = state.remaining_subjects[1:]

            if current_subject in important_subjects:
                assigned = False
                for slots in selected_subjects.get(current_subject, []):
                    if can_assign(slots, state.used_slots):
                        new_state = state.clone()
                        for slot in slots:
                            new_state.timetable[slot] = current_subject
                            new_state.used_slots.add(slot)
                        new_state.remaining_subjects = next_subjects
                        yield from backtrack_generator(new_state)
                        assigned = True
                if not assigned:
                    return
            else:
                for slots in selected_subjects.get(current_subject, []):
                    if can_assign(slots, state.used_slots):
                        new_state = state.clone()
                        for slot in slots:
                            new_state.timetable[slot] = current_subject
                            new_state.used_slots.add(slot)
                        new_state.remaining_subjects = next_subjects
                        yield from backtrack_generator(new_state)
                
                new_state_not_included = state.clone()
                new_state_not_included.remaining_subjects = next_subjects
                yield from backtrack_generator(new_state_not_included)

        initial_state = ScheduleState(fixed_slots)
        sorted_subjects = sorted(
            [s for s in selected_subjects.keys() if s],
            key=lambda s: s in important_subjects,
            reverse=True
        )
        initial_state.remaining_subjects = sorted_subjects
        
        yield from backtrack_generator(initial_state)

    @staticmethod
    def get_prefix(slots):
        """スロットのリストからプレフィックスを生成"""
        return "".join(sorted(set(slot[0] for slot in slots)))

    @staticmethod
    def _process_requirement_set(req_data, subjects_to_check, source_type):
        """指定された要件セットを処理し、不足情報を返す内部ヘルパー"""
        missing_for_set = []
        normalized_subjects = {s for s in (TimetableLogic.normalize_subject_name(subj) for subj in subjects_to_check) if s}

        for req_key, req_details in req_data.items():
            color = req_details.get("color", "#FF0000")

            if "conditions" in req_details and isinstance(req_details["conditions"], list):
                is_or_condition_met = False
                
                for sub_condition in req_details["conditions"]:
                    try:
                        req_count = int(sub_condition.get("required", 1))
                        required_subjects = [TimetableLogic.normalize_subject_name(s) for s in sub_condition.get("subjects", [])]
                        found_count = sum(1 for subj in required_subjects if subj in normalized_subjects)
                        if found_count >= req_count:
                            is_or_condition_met = True
                            break
                    except (ValueError, TypeError):
                        continue
                
                if not is_or_condition_met:
                    for sub_condition in req_details["conditions"]:
                        try:
                            req_count = int(sub_condition.get("required", 1))
                            required_subjects = [TimetableLogic.normalize_subject_name(s) for s in sub_condition.get("subjects", [])]
                            found_count = sum(1 for subj in required_subjects if subj in normalized_subjects)
                            
                            missing_for_set.append({
                                'condition_num': req_key,
                                'required': req_count,
                                'matched': found_count,
                                'subjects': sub_condition.get("subjects", []),
                                'color': color,
                                'is_or_group': True,
                                'source_type': source_type
                            })
                        except (ValueError, TypeError):
                            continue
            
            else:
                try:
                    req_count = int(req_details.get("required", 1))
                    required_subjects = [TimetableLogic.normalize_subject_name(s) for s in req_details.get("subjects", [])]
                    found_count = sum(1 for subj in required_subjects if subj in normalized_subjects)

                    if found_count < req_count:
                        missing_for_set.append({
                            'condition_num': req_key,
                            'required': req_count,
                            'matched': found_count,
                            'subjects': req_details.get("subjects", []),
                            'color': color,
                            'is_or_group': False,
                            'source_type': source_type
                        })
                except (ValueError, TypeError):
                    continue
                    
        return missing_for_set

    @staticmethod
    def check_required_subjects(subjects_to_check, requirement_sources):
        """必須科目チェック（動的階層対応）"""
        missing_info = []
        for source in requirement_sources:
            missing_info.extend(
                TimetableLogic._process_requirement_set(
                    req_data=source["requirements"],
                    subjects_to_check=source["subjects_to_check"],
                    source_type=source["source_label"]
                )
            )
        return missing_info

    @staticmethod
    def format_missing_subjects_message(missing_info):
        """不足科目情報のリストをユーザーフレンドリーな文字列にフォーマットする"""
        if not missing_info:
            return ""

        grouped = {}
        for item in missing_info:
            source = item.get('source_type', '不明')
            if isinstance(source, list):
                source = '_'.join(source)

            if source not in grouped:
                grouped[source] = {}
            
            group_key = str(item['condition_num'])
            
            if group_key not in grouped[source]:
                grouped[source][group_key] = []
            
            grouped[source][group_key].append(item)

        group_messages = []
        for source in sorted(grouped.keys()):
            groups = grouped[source]
            
            try:
                sorted_groups = sorted(groups.items(), key=lambda x: int(x[0]))
            except (ValueError, TypeError):
                sorted_groups = sorted(groups.items())
            
            output_condition_counter = 1
            for group_key, items in sorted_groups:
                message_parts_for_group = []
                is_or = items[0].get('is_or_group', False)

                if is_or:
                    message_parts_for_group.append(f"--- {source} 条件 {output_condition_counter} ---")
                    sorted_items = sorted(items, key=lambda x: x['subjects'][0] if x.get('subjects') else "")
                    for item in sorted_items:
                        subjects_str = ", ".join(item.get('subjects', []))
                        message_parts_for_group.append(
                            f"  - {subjects_str} (現在: {item.get('matched', 0)} / 必要: {item.get('required', 1)})"
                        )
                else:
                    for item in items:
                        message_parts_for_group.append(f"--- {source} 条件 {output_condition_counter} ---")
                        subjects_str = ", ".join(item.get('subjects', []))
                        message_parts_for_group.append(
                            f"- 教科: {subjects_str} (現在: {item.get('matched', 0)} / 必要: {item.get('required', 1)})"
                        )
                        output_condition_counter += 1
                
                group_messages.append("\n".join(message_parts_for_group))
                if is_or:
                    output_condition_counter += 1

        return "\n\n".join(group_messages)



    @staticmethod
    def get_prerequisite_highlight_targets(all_subjects_norm, prerequisite_config):
        """
        不足している前提科目を特定し、ハイライト対象となる教科のセットを返す
        - all_subjects_norm: 選択されているすべての正規化済み教科名のセット
        - prerequisite_config: 前提科目の設定データ {raw_subject_name: [raw_prereq_name, ...]}
        """
        prerequisite_targets = set()
        
        # 設定ファイルの前提科目もすべて正規化して、正規化済みセットと比較する
        # {norm_main_subj: [norm_prereq1, ...]} の辞書を作成
        norm_prereq_config = {
            TimetableLogic.normalize_subject_name(main_subj): [TimetableLogic.normalize_subject_name(p) for p in prereqs]
            for main_subj, prereqs in prerequisite_config.items()
        }

        for main_subject_norm, prereqs_norm in norm_prereq_config.items():
            if main_subject_norm in all_subjects_norm:
                for prereq_norm in prereqs_norm:
                    if prereq_norm not in all_subjects_norm:
                        prerequisite_targets.add(prereq_norm)
        return prerequisite_targets

    @staticmethod
    def find_subject_for_slot_and_number(subject_number_list, slot_name, num_str):
        """
        指定されたスロットと番号に一致する教科名を検索して返す。
        - subject_number_list: 教科番号リスト [{name: str, data: {slot: number}}]
        - slot_name: スロット名
        - num_str: 検索する番号（文字列）
        """
        if not all([slot_name, num_str]):
            return None
        
        for subject_info in subject_number_list:
            if "data" in subject_info and isinstance(subject_info["data"], dict):
                number_in_config = subject_info["data"].get(slot_name)
                if number_in_config is not None:
                    if str(number_in_config).strip() == num_str:
                        return subject_info.get("name")
        return None

# サンプルデータ

このフォルダには、公開用に作成した架空データのみを置きます。実在校の設定、履修登録用紙、Excel 出力、個人名を含むデータは Git 管理しません。

- `sample_config.json`: 本体・チェッカーで読み込める公開確認用サンプル

`YEARS_HIERARCHY` の葉は空のオブジェクトにし、科目や単位数は
`table_layout*`、`subject_number*`、`subject_slots_base*`、
`SAVE_POSITION*`、`YEARS_SUBJECTS_UNITS_*` に分けて定義します。

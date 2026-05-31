# サンプルデータ

このフォルダには、架空データのみで構成したサンプル設定を収録しています。
実在校の設定、履修登録用紙、Excel 出力、個人名を含むデータは含まれていません。

- `sample_config.json`: 本体・チェッカーで読み込めるサンプル設定

サンプルの時間割枠は、日本の高校で一般的な平日5日・1日6限を想定し、
`月〜金` の5列、`1〜6限` の6行で定義しています。
JSON 内の枠名は元データと同じく `A1`、`A2`、`X1` などのスロット ID です。
`YEARS_MESSAGE` は `課程`、`YEARS_HIERARCHY` は `全日制` の配下に
`2年`、`3年` の葉を持つ形です。葉キーは `全日制_2年` と
`全日制_3年` の2種類で、各葉に時間割枠、科目数、保存位置を用意しています。
単位設定は元データと同じく `YEARS_SUBJECTS_UNITS_全日制` に置いています。
`HIERARCHY_ANCHORS` は `全日制` に設定しています。
芸術科目セレクト用の候補として `書道Ⅰ`、`美術Ⅰ`、`音楽Ⅰ` も収録しています。

`YEARS_HIERARCHY` の葉は空のオブジェクトにし、科目や単位数は
`table_layout*`、`subject_number*`、`subject_slots_base*`、`SAVE_POSITION*`、
`ALL_SLOTS*`、`ABNORMAL_SUBJECTS_UNITS*`、`YEARS_SUBJECTS_UNITS_*` に分けて定義します。

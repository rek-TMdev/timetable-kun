# 時間割くん

時間割くんは、高校向けの履修選択と時間割候補の確認を支援する
Windows デスクトップアプリ群です。Python / PySide6 で実装しており、
本体アプリ、設定編集用ドライバ、Excel 時間割チェッカーで構成しています。

このリポジトリには、ソースコード、架空データのサンプル設定、ビルド定義、
HTML マニュアルを収録しています。実在校名、実生徒データ、実際の運用設定、
個人連絡先、生成済み実行ファイルは含まれていません。

## アプリ構成

| アプリ | 役割 |
| --- | --- |
| 本体 | 設定 JSON を読み込み、学科やコースごとの科目選択から時間割候補を生成・確認します。 |
| ドライバ | 科目マスタ、履修条件、枠レイアウト、Excel 保存位置などを編集します。 |
| チェッカー | 保存済み Excel 時間割を読み込み、単位数、必須科目、前提科目などを検証します。 |

## 主な機能

- 履修条件に基づく時間割候補の生成
- 前提科目、同時選択不可、必須科目、科目数、単位数のチェック
- 固定科目や手動追加科目との競合表示
- 複数プロファイルによる候補管理
- JSON 設定ファイルの画面編集
- 設定ファイルの統合と競合解決
- Excel 入出力と専用形式ファイル `.tm.json` の保存・読込
- Excel 時間割の一括検証と CSV レポート出力
- 本体、ドライバ、チェッカーをまとめた HTML マニュアル

## ディレクトリ構成

```text
timetable-kun/
  src/
    app/       # 本体アプリ
    driver/    # 設定編集用ドライバ
    checker/   # Excel 時間割チェッカー
  docs/
    html-manual/  # HTML マニュアル
  examples/    # 架空データのサンプル設定
  installer/   # PyInstaller / Inno Setup 定義
  assets/      # アプリ用アイコン
  scripts/     # サンプル設定の検証スクリプト
```

## 技術構成

- Python
- PySide6 / Qt
- openpyxl
- JSON
- PyInstaller
- Inno Setup
- HTML / CSS

## セットアップ

Windows / PowerShell / Python 3.12 系を想定しています。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

起動例:

```powershell
python src\app\time_manager_main.py
python src\driver\config_editor_main.py
python src\checker\timetable_checker_main.py
```

## サンプル設定

`examples/sample_config.json` は架空データのみで構成したサンプル設定です。
時間割枠は平日5日、1日6限の `6行 x 5列` です。区分サンプルは学年ではなく
学科を表しており、`普通科` と `情報科` を収録しています。

サンプル設定の構造は次のコマンドで検証できます。

```powershell
python scripts\validate_sample_config.py
```

## マニュアル

本体、ドライバ、チェッカーの基本操作は
`docs/html-manual/index.html` にまとめています。画像や外部スクリプトに依存しない
単一 HTML です。

## ビルド定義

PyInstaller:

```powershell
pyinstaller installer\時間割くん.spec
pyinstaller installer\時間割くんツール.spec
```

Inno Setup:

- `installer/時間割くん.iss`
- `installer/時間割くんツール.iss`

生成済み `exe`、`dist`、`build`、`_internal`、仮想環境はこのリポジトリに
含まれていません。

## ダウンロード

GitHub Releases には、架空データのサンプル設定を同梱した Windows 向け
ZIP を配置しています。

- https://github.com/rek-TMdev/timetable-kun/releases/tag/preview-2026-05-31

## 収録していないデータ

- 実在校名、個人名、連絡先などの識別情報
- 実際の履修登録用紙、Excel データ、運用設定 JSON
- 生成済み実行ファイル、ビルドフォルダ、仮想環境
- 配布先固有の自動更新先やローカル絶対パス

## ライセンス

本ソフトウェアの利用条件は `LICENSE` に記載しています。第三者ライブラリと
アイコン素材の扱いは `THIRD_PARTY_NOTICES.md` に記載しています。

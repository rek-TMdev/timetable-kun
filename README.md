# 時間割くん

時間割くんは、高校の履修選択と時間割候補の確認を支援する Python/PySide6 製のデスクトップシステムです。このリポジトリには実在校名、実生徒データ、実運用設定ファイル、生成済み配布物は含めていません。

教育現場での利用実績があります。この公開用リポジトリは、ポートフォリオとして構成と実装内容が分かるように、最新版ソースを中心に匿名化して整理したものです。

## 構成

```text
timetable-kun/
  src/
    app/       # 本体アプリ
    driver/    # 管理者向けドライバ/設定編集ツール
    checker/   # 設定・時間割チェック補助ツール
  installer/   # PyInstaller / Inno Setup 用の公開用定義
  docs/
    html-manual/  # HTMLマニュアルの公開用ダイジェスト
  examples/    # 架空データのみのサンプル
  assets/      # アプリ用アイコン等
```

## 主な機能

- 履修ルールに基づく時間割候補の生成・確認
- 前提科目、同時履修不可、単位数、教科数などの条件チェック
- 手動固定科目との競合検知と視覚的なハイライト
- JSON 設定ファイルを編集する管理者向けドライバ
- 3-way マージを含む設定競合対策
- Excel 入出力によるデータ整理
- PyInstaller と Inno Setup による Windows 配布
- HTML マニュアルによる運用説明

## 技術構成

- Python
- PySide6 / Qt
- openpyxl
- JSON
- PyInstaller
- Inno Setup
- HTML / CSS / JavaScript

## セットアップ

Windows / PowerShell を想定しています。

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

実運用設定は含めていないため、初回起動時は `examples/sample_config.json` を参考に、架空または許可済みの設定ファイルを用意してください。

## ビルド

PyInstaller:

```powershell
pyinstaller installer\時間割くん.spec
pyinstaller installer\時間割くんツール.spec
```

Inno Setup:

- `installer/時間割くん.iss`
- `installer/時間割くんツール.iss`

上記は公開用にパスを相対化した定義です。実際に配布する場合は、バージョン番号、発行者名、出力先、署名、更新手順を運用環境に合わせて調整します。

## 実行ファイルの配布

クライアントに動作確認してもらう目的であれば、実行ファイルを用意すること自体は有効です。ただし、このリポジトリには生成済み `exe` を直接コミットせず、必要に応じてサンプル設定のみで作成した確認用ビルドを GitHub Releases 等で配布する方針です。

確認用ビルドには、実在校名、実生徒データ、実運用設定、ローカルパス、個人連絡先、自動更新先などの運用先固有情報を含めません。

## 公開範囲

含めているもの:

- 本体、ドライバ、チェッカーの Python ソース
- アプリ用アイコンと SVG
- 公開用のサンプル設定
- ビルド・インストーラー定義
- HTML マニュアルの概要版

含めていないもの:

- 学校名、個人名、連絡先などの識別情報
- 実際の履修登録用紙、Excel データ、運用設定 JSON
- 生成済み `exe`、`dist`、`build`、`_internal`、仮想環境
- 生成済みの大型 HTML マニュアル一式

## ライセンス

このリポジトリはポートフォリオおよびソース参照用です。個人の私的用途または単独での業務効率化には無償で利用できますが、商用利用、組織的利用、再配布、改変には事前の許可が必要です。詳細は `LICENSE` を参照してください。

第三者ライブラリおよびアイコン素材の扱いは `THIRD_PARTY_NOTICES.md` を参照してください。Windows 配布物を作成する場合は、同梱ライブラリのライセンス条件を確認してください。

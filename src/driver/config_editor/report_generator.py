"""
report_generator.py - レポート出力機能

Timetable Checkerの検証結果をHTML/PDFレポートとして出力する機能を提供します。
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import html


@dataclass
class CheckResult:
    """検証結果を表すデータクラス"""
    file_path: str
    file_name: str
    status: str  # "OK", "WARNING", "ERROR"
    issues: List[Dict[str, Any]] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def issue_count(self) -> int:
        return len(self.issues)
    
    @property
    def has_errors(self) -> bool:
        return any(i.get("severity") == "error" for i in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        return any(i.get("severity") == "warning" for i in self.issues)


@dataclass
class ReportData:
    """レポートデータを表すデータクラス"""
    title: str
    generated_at: datetime
    results: List[CheckResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    config_path: Optional[str] = None
    
    @property
    def total_files(self) -> int:
        return len(self.results)
    
    @property
    def ok_count(self) -> int:
        return sum(1 for r in self.results if r.status == "OK")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == "WARNING")
    
    @property
    def error_count(self) -> int:
        return sum(1 for r in self.results if r.status == "ERROR")


class HTMLReportGenerator:
    """
    HTML形式のレポートを生成するクラス。
    """
    
    # HTMLテンプレート
    HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', 'Meiryo', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px 40px;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .meta {{
            opacity: 0.8;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card .number {{
            font-size: 36px;
            font-weight: bold;
        }}
        .summary-card .label {{
            color: #666;
            margin-top: 5px;
        }}
        .summary-card.ok .number {{ color: #28a745; }}
        .summary-card.warning .number {{ color: #ffc107; }}
        .summary-card.error .number {{ color: #dc3545; }}
        .results {{
            padding: 30px 40px;
        }}
        .results h2 {{
            margin-bottom: 20px;
            color: #333;
        }}
        .result-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }}
        .result-header {{
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }}
        .result-header.ok {{ background: #d4edda; }}
        .result-header.warning {{ background: #fff3cd; }}
        .result-header.error {{ background: #f8d7da; }}
        .result-header .file-name {{
            font-weight: bold;
        }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-badge.ok {{ background: #28a745; color: white; }}
        .status-badge.warning {{ background: #ffc107; color: black; }}
        .status-badge.error {{ background: #dc3545; color: white; }}
        .result-details {{
            padding: 15px 20px;
            background: #f8f9fa;
            border-top: 1px solid #e0e0e0;
        }}
        .issue {{
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .issue.error {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .issue.warning {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
        .issue.info {{ background: #d1ecf1; border-left: 4px solid #17a2b8; }}
        .footer {{
            padding: 20px 40px;
            background: #f8f9fa;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                生成日時: {generated_at}<br>
                設定ファイル: {config_path}
            </div>
        </div>
        <div class="summary">
            <div class="summary-card">
                <div class="number">{total_files}</div>
                <div class="label">検証ファイル数</div>
            </div>
            <div class="summary-card ok">
                <div class="number">{ok_count}</div>
                <div class="label">正常</div>
            </div>
            <div class="summary-card warning">
                <div class="number">{warning_count}</div>
                <div class="label">警告</div>
            </div>
            <div class="summary-card error">
                <div class="number">{error_count}</div>
                <div class="label">エラー</div>
            </div>
        </div>
        <div class="results">
            <h2>検証結果詳細</h2>
            {results_html}
        </div>
        <div class="footer">
            時間割くん Timetable Checker - Generated by Report Generator
        </div>
    </div>
</body>
</html>'''
    
    def generate(self, report_data: ReportData) -> str:
        """
        HTMLレポートを生成する。
        
        Args:
            report_data: レポートデータ
            
        Returns:
            HTML文字列
        """
        results_html = self._generate_results_html(report_data.results)
        
        return self.HTML_TEMPLATE.format(
            title=html.escape(report_data.title),
            generated_at=report_data.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            config_path=html.escape(report_data.config_path or "N/A"),
            total_files=report_data.total_files,
            ok_count=report_data.ok_count,
            warning_count=report_data.warning_count,
            error_count=report_data.error_count,
            results_html=results_html
        )
    
    def _generate_results_html(self, results: List[CheckResult]) -> str:
        """検証結果のHTML部分を生成"""
        html_parts = []
        
        for result in results:
            status_class = result.status.lower()
            
            issues_html = ""
            if result.issues:
                issues_html = '<div class="result-details">'
                for issue in result.issues:
                    severity = issue.get("severity", "info")
                    message = html.escape(issue.get("message", ""))
                    issues_html += f'<div class="issue {severity}">{message}</div>'
                issues_html += '</div>'
            
            html_parts.append(f'''
            <div class="result-item">
                <div class="result-header {status_class}">
                    <span class="file-name">{html.escape(result.file_name)}</span>
                    <span class="status-badge {status_class}">{result.status}</span>
                </div>
                {issues_html}
            </div>
            ''')
        
        return "".join(html_parts)
    
    def save_to_file(self, report_data: ReportData, file_path: str | Path) -> bool:
        """
        HTMLレポートをファイルに保存する。
        
        Args:
            report_data: レポートデータ
            file_path: 保存先のパス
            
        Returns:
            成功時True
        """
        try:
            html_content = self.generate(report_data)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return True
        except Exception as e:
            print(f"HTMLレポート保存エラー: {e}")
            return False


class TextReportGenerator:
    """
    テキスト形式のレポートを生成するクラス。
    """
    
    def generate(self, report_data: ReportData) -> str:
        """テキストレポートを生成"""
        lines = [
            "=" * 60,
            f"  {report_data.title}",
            "=" * 60,
            f"生成日時: {report_data.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"設定ファイル: {report_data.config_path or 'N/A'}",
            "",
            "【サマリー】",
            f"  検証ファイル数: {report_data.total_files}",
            f"  正常: {report_data.ok_count}",
            f"  警告: {report_data.warning_count}",
            f"  エラー: {report_data.error_count}",
            "",
            "-" * 60,
            "【検証結果詳細】",
            "-" * 60,
        ]
        
        for result in report_data.results:
            lines.append(f"\n[{result.status}] {result.file_name}")
            if result.issues:
                for issue in result.issues:
                    severity = issue.get("severity", "info").upper()
                    message = issue.get("message", "")
                    lines.append(f"  [{severity}] {message}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def save_to_file(self, report_data: ReportData, file_path: str | Path) -> bool:
        """テキストレポートをファイルに保存"""
        try:
            text_content = self.generate(report_data)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            return True
        except Exception as e:
            print(f"テキストレポート保存エラー: {e}")
            return False


def generate_report(
    results: List[CheckResult],
    title: str = "Timetable Checker 検証レポート",
    config_path: Optional[str] = None,
    output_path: Optional[str | Path] = None,
    format: str = "html"
) -> Optional[str]:
    """
    レポートを生成する簡易関数。
    
    Args:
        results: 検証結果のリスト
        title: レポートタイトル
        config_path: 設定ファイルのパス
        output_path: 出力先パス（Noneの場合は文字列を返す）
        format: "html" または "text"
        
    Returns:
        output_pathがNoneの場合はレポート文字列、それ以外はNone
    """
    report_data = ReportData(
        title=title,
        generated_at=datetime.now(),
        results=results,
        config_path=config_path
    )
    
    if format == "html":
        generator = HTMLReportGenerator()
    else:
        generator = TextReportGenerator()
    
    if output_path:
        generator.save_to_file(report_data, output_path)
        return None
    else:
        return generator.generate(report_data)

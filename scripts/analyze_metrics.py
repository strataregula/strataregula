#!/usr/bin/env python3
"""
プロジェクトメトリクス分析スクリプト
コードベースの統計とメトリクスを分析
"""

import os
import json
from pathlib import Path
from datetime import datetime
import subprocess
import sys

def count_lines_of_code():
    """コード行数を計算"""
    print("Counting lines of code...")
    
    extensions = {'.py': 'Python', '.yaml': 'YAML', '.yml': 'YAML', '.md': 'Markdown', '.json': 'JSON'}
    stats = {}
    total_files = 0
    total_lines = 0
    
    for ext, lang in extensions.items():
        files = list(Path('.').rglob(f'*{ext}'))
        if lang not in stats:
            stats[lang] = {'files': 0, 'lines': 0}
        
        for file_path in files:
            # Skip certain directories
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'node_modules', '.egg-info']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                    stats[lang]['files'] += 1
                    stats[lang]['lines'] += lines
                    total_files += 1
                    total_lines += lines
            except:
                pass
    
    return stats, total_files, total_lines

def analyze_test_coverage():
    """テストカバレッジを分析"""
    print("Analyzing test coverage...")
    
    try:
        # pytest-covを使ってカバレッジ測定を試行
        cmd = [sys.executable, "-m", "pytest", "--cov=strataregula", "--cov-report=json", "--quiet"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and Path('coverage.json').exists():
            with open('coverage.json', 'r') as f:
                coverage_data = json.load(f)
            
            coverage_percent = coverage_data.get('totals', {}).get('percent_covered', 0)
            return {
                'available': True,
                'coverage_percent': round(coverage_percent, 2),
                'files_tested': len(coverage_data.get('files', {}))
            }
    except:
        pass
    
    # フォールバック: テストファイル数をカウント
    test_files = list(Path('tests').rglob('test_*.py')) if Path('tests').exists() else []
    source_files = list(Path('strataregula').rglob('*.py')) if Path('strataregula').exists() else []
    
    return {
        'available': False,
        'test_files': len(test_files),
        'source_files': len(source_files),
        'test_ratio': round(len(test_files) / max(len(source_files), 1), 2)
    }

def check_code_quality():
    """コード品質メトリクス"""
    print("Checking code quality...")
    
    quality_metrics = {
        'ruff_issues': 0,
        'complexity_warnings': 0,
        'style_issues': 0
    }
    
    try:
        # Ruffでの検査
        cmd = [sys.executable, "-m", "ruff", "check", "strataregula/", "--output-format=json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            try:
                ruff_data = json.loads(result.stdout)
                quality_metrics['ruff_issues'] = len(ruff_data)
            except:
                pass
    except:
        pass
    
    return quality_metrics

def analyze_dependency_health():
    """依存関係の健全性チェック"""
    print("Analyzing dependency health...")
    
    dependencies = {}
    
    # requirements.txtを読み取り
    if Path('requirements.txt').exists():
        with open('requirements.txt', 'r') as f:
            deps = f.readlines()
            dependencies['requirements'] = len([d for d in deps if d.strip() and not d.startswith('#')])
    
    # pyproject.tomlを読み取り
    if Path('pyproject.toml').exists():
        with open('pyproject.toml', 'r') as f:
            content = f.read()
            dependencies['pyproject_available'] = True
    
    return dependencies

def generate_metrics_report():
    """メトリクスレポートを生成"""
    print("Generating comprehensive metrics report...")
    print("=" * 50)
    
    # メトリクス収集
    loc_stats, total_files, total_lines = count_lines_of_code()
    coverage_data = analyze_test_coverage()
    quality_data = check_code_quality()
    dependency_data = analyze_dependency_health()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'code_statistics': {
            'total_files': total_files,
            'total_lines': total_lines,
            'by_language': loc_stats
        },
        'test_coverage': coverage_data,
        'code_quality': quality_data,
        'dependencies': dependency_data
    }
    
    # レポートを表示
    print("Code Statistics:")
    print(f"   Total files: {total_files}")
    print(f"   Total lines: {total_lines:,}")
    
    for lang, stats in loc_stats.items():
        if stats['lines'] > 0:
            print(f"   {lang}: {stats['files']} files, {stats['lines']:,} lines")
    
    print("\nTest Coverage:")
    if coverage_data.get('available'):
        print(f"   Coverage: {coverage_data['coverage_percent']}%")
        print(f"   Files tested: {coverage_data['files_tested']}")
    else:
        print(f"   Test files: {coverage_data.get('test_files', 0)}")
        print(f"   Source files: {coverage_data.get('source_files', 0)}")
        print(f"   Test ratio: {coverage_data.get('test_ratio', 0):.2f}")
    
    print("\nCode Quality:")
    print(f"   Ruff issues: {quality_data['ruff_issues']}")
    
    print("\nDependencies:")
    if 'requirements' in dependency_data:
        print(f"   Requirements.txt deps: {dependency_data['requirements']}")
    if dependency_data.get('pyproject_available'):
        print(f"   pyproject.toml: Available")
    
    # JSONレポートを保存
    report_file = Path('metrics_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nMetrics report saved to {report_file}")
    
    # 健全性スコアを計算
    health_score = calculate_health_score(report)
    print(f"\nProject Health Score: {health_score:.1f}/100")
    
    return report

def calculate_health_score(report):
    """プロジェクト健全性スコアを計算"""
    score = 0
    
    # コード行数（基本点）
    if report['code_statistics']['total_lines'] > 1000:
        score += 20
    elif report['code_statistics']['total_lines'] > 500:
        score += 15
    
    # テストカバレッジ
    coverage = report['test_coverage']
    if coverage.get('available') and coverage.get('coverage_percent', 0) > 80:
        score += 30
    elif coverage.get('test_ratio', 0) > 0.5:
        score += 20
    elif coverage.get('test_files', 0) > 0:
        score += 10
    
    # コード品質
    if report['code_quality']['ruff_issues'] == 0:
        score += 25
    elif report['code_quality']['ruff_issues'] < 10:
        score += 15
    
    # ドキュメント
    if report['code_statistics']['by_language'].get('Markdown', {}).get('files', 0) > 5:
        score += 15
    elif report['code_statistics']['by_language'].get('Markdown', {}).get('files', 0) > 0:
        score += 10
    
    # 設定ファイル
    if report['dependencies'].get('pyproject_available'):
        score += 10
    
    return min(score, 100)

def main():
    """メイン関数"""
    print("Strataregula Project Metrics Analysis")
    print("========================================")
    
    try:
        report = generate_metrics_report()
        
        print("\nMetrics analysis completed successfully!")
        print("Run this script regularly to monitor project health")
        print("Use 'make benchmark-notebook' for performance visualization")
        
        return 0
    except Exception as e:
        print(f"Error during metrics analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
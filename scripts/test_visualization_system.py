#!/usr/bin/env python3
"""
ベンチマーク可視化システムのテストスクリプト
全てのコンポーネントが正常に動作することを確認
"""

import sys
import subprocess
from pathlib import Path
import json
import time

def test_component(name, test_func):
    """コンポーネントのテストを実行"""
    print(f"Testing {name}...", end=" ")
    start_time = time.time()
    
    try:
        success = test_func()
        duration = time.time() - start_time
        
        if success:
            print(f"PASS ({duration:.3f}s)")
            return True
        else:
            print(f"FAIL ({duration:.3f}s)")
            return False
    except Exception as e:
        duration = time.time() - start_time
        print(f"ERROR ({duration:.3f}s): {e}")
        return False

def test_benchmark_execution():
    """ベンチマーク実行をテスト"""
    try:
        result = subprocess.run([
            sys.executable, "scripts/run_benchmarks.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # benchmark_results.json が生成されているかチェック
            return Path('benchmark_results.json').exists()
        return False
    except subprocess.TimeoutExpired:
        return False

def test_image_generation():
    """画像生成をテスト"""
    try:
        result = subprocess.run([
            sys.executable, "scripts/generate_benchmark_images.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # 画像ファイルが生成されているかチェック
            images_dir = Path('docs/images')
            expected_files = [
                'benchmark_performance.png',
                'benchmark_scalability.png', 
                'benchmark_compilation.png',
                'benchmark_memory.png',
                'benchmark_dashboard.png'
            ]
            
            return all((images_dir / img).exists() for img in expected_files)
        return False
    except subprocess.TimeoutExpired:
        return False

def test_notebook_conversion():
    """Notebook変換をテスト"""
    try:
        result = subprocess.run([
            sys.executable, "scripts/convert_notebook.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            # HTMLファイルが生成されているかチェック
            return Path('docs/benchmark.html').exists()
        return False
    except subprocess.TimeoutExpired:
        return False

def test_benchmark_data_quality():
    """ベンチマークデータの品質をテスト"""
    benchmark_file = Path('benchmark_results.json')
    
    if not benchmark_file.exists():
        return False
    
    try:
        with open(benchmark_file, 'r') as f:
            data = json.load(f)
        
        # 必要なフィールドの存在確認
        required_fields = ['timestamp', 'version', 'benchmarks']
        if not all(field in data for field in required_fields):
            return False
        
        # ベンチマーク結果の確認
        benchmarks = data['benchmarks']
        expected_benchmarks = [
            'pattern_expansion',
            'compilation_speed', 
            'service_lookup',
            'doe_scalability',
            'memory_usage'
        ]
        
        if not all(bench in benchmarks for bench in expected_benchmarks):
            return False
        
        # パフォーマンス目標の確認
        pe = benchmarks.get('pattern_expansion', {})
        if pe.get('patterns_per_sec', 0) < 10000:
            return False
        
        sl = benchmarks.get('service_lookup', {})
        if not sl.get('lookup_methods', {}).get('direct_map', 0) >= 100000:
            return False
        
        return True
    except (json.JSONDecodeError, KeyError):
        return False

def test_makefile_commands():
    """Makefileコマンドの存在をテスト"""
    makefile_path = Path('Makefile')
    if not makefile_path.exists():
        return False
    
    with open(makefile_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 必要なコマンドの確認
    required_commands = [
        'benchmark',
        'benchmark-images',
        'benchmark-view',
        'security-check',
        'personas',
        'status'
    ]
    
    return all(f"{cmd}:" in content for cmd in required_commands)

def test_readme_integration():
    """README.mdにベンチマーク情報が統合されているかテスト"""
    readme_path = Path('README.md')
    if not readme_path.exists():
        return False
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 必要なセクションの確認
    required_sections = [
        '## 📊 Performance Benchmarks',
        'benchmark_performance.png',
        'benchmark_scalability.png',
        'All performance targets achieved'
    ]
    
    return all(section in content for section in required_sections)

def test_github_actions_workflow():
    """GitHub Actionsワークフローの存在をテスト"""
    workflow_path = Path('.github/workflows/benchmark.yml')
    if not workflow_path.exists():
        return False
    
    with open(workflow_path, 'r') as f:
        content = f.read()
    
    # 必要なステップの確認
    required_steps = [
        'Run benchmarks',
        'Generate visualizations',
        'Convert notebook to HTML',
        'Commit updated visualizations'
    ]
    
    return all(step in content for step in required_steps)

def run_comprehensive_test():
    """包括的なテストを実行"""
    print("Strataregula Benchmark Visualization System Test")
    print("=" * 55)
    
    test_cases = [
        ("Benchmark Execution", test_benchmark_execution),
        ("Image Generation", test_image_generation), 
        ("Notebook Conversion", test_notebook_conversion),
        ("Benchmark Data Quality", test_benchmark_data_quality),
        ("Makefile Commands", test_makefile_commands),
        ("README Integration", test_readme_integration),
        ("GitHub Actions Workflow", test_github_actions_workflow)
    ]
    
    results = []
    total_start_time = time.time()
    
    for name, test_func in test_cases:
        success = test_component(name, test_func)
        results.append((name, success))
    
    total_duration = time.time() - total_start_time
    
    # 結果サマリー
    print("\n" + "=" * 55)
    print("Test Results Summary:")
    print("-" * 30)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {name:<25} {status}")
    
    print("-" * 30)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"Duration: {total_duration:.3f}s")
    
    if passed == total:
        print("\nAll systems operational!")
        print("Benchmark visualization system ready for production")
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Complete benchmark visualization system'")  
        print("3. git push")
        print("4. Enable GitHub Pages for automatic publishing")
        return 0
    else:
        print(f"\n!! {total - passed} test(s) failed!")
        print("Please check the failing components before deployment")
        return 1

def main():
    """メイン関数"""
    try:
        return run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
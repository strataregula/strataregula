#!/usr/bin/env python3
"""
Jupyter NotebookをHTMLに変換してGitHub Pagesで表示可能にする
"""

import subprocess
import sys
from pathlib import Path

def convert_notebook_to_html():
    """NotebookをHTMLに変換"""
    print("Converting Jupyter notebook to HTML...")
    
    notebook_path = Path('notebooks/benchmark_results.ipynb')
    if not notebook_path.exists():
        print(f"Notebook not found: {notebook_path}")
        return False
    
    try:
        # nbconvertを使ってHTMLに変換
        cmd = [
            sys.executable, "-m", "nbconvert",
            "--execute",
            "--to", "html", 
            str(notebook_path),
            "--output", "benchmark_results.html"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            html_path = notebook_path.parent / "benchmark_results.html"
            print(f"Successfully converted to: {html_path}")
            
            # GitHub Pages用のindex.htmlも作成
            create_github_pages_index(html_path)
            
            return True
        else:
            print(f"Conversion failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def create_github_pages_index(html_path):
    """GitHub Pages用のindex.htmlを作成"""
    
    # HTML内容を読み取り
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # GitHub Pages用に調整
    enhanced_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Strataregula Benchmark Analysis</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background-color: #f8f9fa;
        }}
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            margin: -20px -20px 30px -20px;
            border-radius: 0 0 20px 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.2em;
        }}
        .content {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .nav {{
            background: #343a40;
            padding: 15px 30px;
            color: white;
        }}
        .nav a {{
            color: #17a2b8;
            text-decoration: none;
            margin-right: 20px;
            font-weight: 500;
        }}
        .nav a:hover {{
            color: #20c997;
        }}
        .notebook-content {{
            padding: 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Strataregula Performance Analysis</h1>
        <p>Comprehensive benchmark results and visualizations</p>
    </div>
    
    <div class="content">
        <div class="nav">
            <a href="https://github.com/unizontech/strataregula" target="_blank">📂 Repository</a>
            <a href="#performance-dashboard">📊 Dashboard</a>
            <a href="#recommendations">🎯 Recommendations</a>
            <a href="https://github.com/unizontech/strataregula/blob/main/scripts/run_benchmarks.py" target="_blank">⚡ Run Benchmarks</a>
        </div>
        
        <div class="notebook-content">
{html_content}
        </div>
    </div>
    
    <script>
        // Add smooth scrolling for internal links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({{
                    behavior: 'smooth'
                }});
            }});
        }});
    </script>
</body>
</html>"""
    
    # docs/benchmark.htmlとして保存（GitHub Pagesで直接アクセス可能）
    docs_path = Path('docs/benchmark.html')
    docs_path.parent.mkdir(exist_ok=True)
    
    with open(docs_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_html)
    
    print(f"Created GitHub Pages version: {docs_path}")
    print(f"Will be available at: https://unizontech.github.io/strataregula/benchmark.html")

def main():
    """メイン関数"""
    print("Jupyter Notebook to HTML Converter")
    print("=" * 40)
    
    if convert_notebook_to_html():
        print("\nConversion completed successfully!")
        print("Next steps:")
        print("1. git add notebooks/ docs/")
        print("2. git commit -m 'Add HTML benchmark analysis'") 
        print("3. git push")
        print("4. Enable GitHub Pages in repository settings")
        return 0
    else:
        print("\nConversion failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
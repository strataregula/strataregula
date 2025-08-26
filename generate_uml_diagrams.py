#!/usr/bin/env python3
"""
UML図生成スクリプト
SYSTEM_ARCHITECTURE_UML.mdファイルからPlantUML図を生成します
"""

import os
import re
import plantuml
from pathlib import Path

def extract_plantuml_blocks(markdown_file):
    """MarkdownファイルからPlantUMLブロックを抽出"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # PlantUMLブロックを検索
    pattern = r'```plantuml\s*\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    # 図の説明マッピング
    diagram_descriptions = {
        'StrataRegula_Component_Architecture': 'システム全体のコンポーネントアーキテクチャを示す図です。VS Code環境、LSP、Pythonコアエンジン、共有データレイヤーの関係を表現しています。',
        'Pattern_Learning_Sequence': '動的パターン学習のシーケンス図です。YAMLファイルの分析からパターンの学習、データベースへの保存までの流れを示しています。',
        'IntelliSense_Completion_Flow': 'IntelliSense補完フローのシーケンス図です。ユーザーの入力から適切な補完候補の生成までの処理を表現しています。',
        'Core_Data_Structures': 'コアデータ構造のクラス図です。LearnedPattern、DynamicHierarchy、StrataRegulaConfigなどの主要なデータ構造とその関係を示しています。',
        'YAML_Analysis_Activity': 'YAMLファイル分析プロセスのアクティビティ図です。ファイルの読み込みからパターン抽出、設定更新までの処理フローを表現しています。',
        'Deployment_Diagram': 'システム配備図です。VS Code拡張、LSPプロセス、Pythonプロセスの配置と通信関係を示しています。',
        'Pattern_Learning_States': 'パターン学習の状態図です。アイドル状態から分析、提供、シャットダウンまでの状態遷移を表現しています。',
        'Communication_Protocol': '通信プロトコル図です。VS Code拡張、LSP、Pythonコア、ファイルシステム間の通信フローを示しています。',
        'Performance_Analysis': 'パフォーマンス分析図です。YAMLファイル分析、補完応答、メモリ管理、スケーラビリティの制限と最適化手法を表現しています。',
        'Security_Architecture': 'セキュリティとプライバシーアーキテクチャです。ローカル処理ゾーン、ネットワーク境界、データ保護対策を示しています。',
        'System_Extensibility': 'システム拡張性アーキテクチャです。プラグインシステム、フックシステム、拡張レジストリの構造とライフサイクルを表現しています。'
    }
    
    diagrams = []
    for i, match in enumerate(matches):
        # 図の名前を抽出（@startumlの後の行から）
        lines = match.strip().split('\n')
        name = f"diagram_{i+1}"
        for line in lines:
            if line.startswith('@startuml'):
                name = line.split()[1] if len(line.split()) > 1 else f"diagram_{i+1}"
                break
        
        # 説明を取得（デフォルト説明も用意）
        description = diagram_descriptions.get(name, f"{name}のUML図です。システムアーキテクチャの詳細を確認できます。")
        
        diagrams.append({
            'name': name,
            'content': match.strip(),
            'description': description
        })
    
    return diagrams

def generate_diagrams(diagrams, output_dir="uml_diagrams"):
    """PlantUML図を生成"""
    # 出力ディレクトリを作成
    Path(output_dir).mkdir(exist_ok=True)
    
    # PlantUMLサーバーに接続
    server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')
    
    print(f"生成する図の数: {len(diagrams)}")
    
    for diagram in diagrams:
        try:
            print(f"図を生成中: {diagram['name']}")
            
            # PlantUMLコードを生成
            plantuml_code = f"@startuml\n{diagram['content']}\n@enduml"
            
            # 図を生成
            diagram_url = server.get_url(plantuml_code)
            
            # HTMLファイルを作成
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{diagram['name']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .source-info {{ 
            background: #e8f4fd; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0; 
            border-left: 4px solid #007acc;
            text-align: center;
        }}
        .source-file {{ 
            font-family: monospace; 
            background: #fff; 
            padding: 8px 12px; 
            border-radius: 4px; 
            border: 1px solid #ddd;
            display: inline-block;
            margin: 10px 0;
        }}
        .diagram {{ text-align: center; margin: 20px 0; }}
        .plantuml-code {{ 
            background: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px; 
            font-family: monospace; 
            white-space: pre-wrap; 
            margin: 20px 0;
            max-height: 400px;
            overflow-y: auto;
        }}
        .download-link {{ 
            display: inline-block; 
            background: #007acc; 
            color: white; 
            padding: 10px 20px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin: 10px;
        }}
        .download-link:hover {{ background: #005a9e; }}
        .back-link {{
            display: inline-block;
            background: #6c757d;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .back-link:hover {{ background: #5a6268; }}
    </style>
</head>
<body>
    <h1>{diagram['name']}</h1>
    
    <div class="source-info">
        <h3>📁 ソースファイル</h3>
        <div class="source-file">SYSTEM_ARCHITECTURE_UML.md</div>
        <p>この図は上記のファイルから生成されています</p>
    </div>
    
    <div class="diagram">
        <img src="{diagram_url}" alt="{diagram['name']}" style="max-width: 100%; height: auto;">
    </div>
    
    <div style="text-align: center;">
        <a href="{diagram_url}" class="download-link" download="{diagram['name']}.png">PNGとして保存</a>
        <a href="data:text/plain;charset=utf-8,{plantuml_code.replace('"', '&quot;')}" class="download-link" download="{diagram['name']}.puml">PlantUMLコードとして保存</a>
    </div>
    
    <div style="text-align: center;">
        <a href="index.html" class="back-link">← 図一覧に戻る</a>
    </div>
    
    <h2>PlantUMLコード:</h2>
    <div class="plantuml-code">{plantuml_code}</div>
</body>
</html>"""
            
            # HTMLファイルを保存
            html_file = Path(output_dir) / f"{diagram['name']}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"  ✓ {html_file} を生成しました")
            
        except Exception as e:
            print(f"  ✗ エラー: {e}")
    
    # インデックスHTMLファイルを作成
    create_index_html(diagrams, output_dir)
    
    print(f"\n完了！図は '{output_dir}' ディレクトリに生成されました。")
    print("各図のHTMLファイルをブラウザで開いて確認してください。")

def create_index_html(diagrams, output_dir):
    """インデックスHTMLファイルを作成"""
    index_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>StrataRegula UML図一覧</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f9f9f9; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #333; text-align: center; }}
        .source-info {{ 
            text-align: center; 
            background: #e8f4fd; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0; 
            border-left: 4px solid #007acc;
        }}
        .source-file {{ 
            font-family: monospace; 
            background: #fff; 
            padding: 8px 12px; 
            border-radius: 4px; 
            border: 1px solid #ddd;
            display: inline-block;
            margin: 10px 0;
        }}
        .diagram-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; 
            margin: 30px 0;
        }}
        .diagram-card {{ 
            background: white; 
            border-radius: 10px; 
            padding: 20px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .diagram-card:hover {{ transform: translateY(-2px); }}
        .diagram-title {{ 
            font-size: 18px; 
            font-weight: bold; 
            color: #007acc; 
            margin-bottom: 15px;
        }}
        .diagram-link {{ 
            display: inline-block; 
            background: #007acc; 
            color: white; 
            padding: 8px 16px; 
            text-decoration: none; 
            border-radius: 5px; 
            margin-top: 10px;
        }}
        .diagram-link:hover {{ background: #005a9e; }}
        .description {{ color: #666; margin-bottom: 15px; line-height: 1.5; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>StrataRegula システムアーキテクチャ UML図</h1>
        
        <div class="source-info">
            <h3>📁 ソースファイル</h3>
            <div class="source-file">SYSTEM_ARCHITECTURE_UML.md</div>
            <p>このファイルから {len(diagrams)} 個のUML図が生成されています</p>
        </div>
        
        <div class="diagram-grid">
"""
    
    # 各図のカードを追加
    for diagram in diagrams:
        index_content += f"""
            <div class="diagram-card">
                <div class="diagram-title">{diagram['name']}</div>
                <div class="description">
                    {diagram['description']}
                </div>
                <a href="{diagram['name']}.html" class="diagram-link">図を表示</a>
            </div>
"""
    
    index_content += """
        </div>
        
        <div style="text-align: center; margin: 40px 0; color: #666;">
            <p>これらの図は PlantUML を使用して生成されています。</p>
            <p>各図はインタラクティブで、PNGとして保存したり、PlantUMLコードを確認したりできます。</p>
        </div>
    </div>
</body>
</html>"""
    
    index_file = Path(output_dir) / "index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"  ✓ {index_file} を生成しました")

def main():
    """メイン関数"""
    uml_file = "SYSTEM_ARCHITECTURE_UML.md"
    
    if not os.path.exists(uml_file):
        print(f"エラー: {uml_file} が見つかりません。")
        return
    
    print("UML図の生成を開始します...")
    print(f"ソースファイル: {uml_file}")
    
    # PlantUMLブロックを抽出
    diagrams = extract_plantuml_blocks(uml_file)
    
    if not diagrams:
        print("PlantUMLブロックが見つかりませんでした。")
        return
    
    # 図を生成
    generate_diagrams(diagrams)

if __name__ == "__main__":
    main()

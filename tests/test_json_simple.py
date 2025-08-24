#!/usr/bin/env python3
"""
JSON処理の簡単なテスト

このファイルでJSON処理機能の動作を確認できます。
"""

import json
from strataregula.json_processor import (
    JSONValidator,
    JSONPathProcessor,
    FormatConverter,
    JSONTransformCommand,
    JSONPathCommand,
    ValidateJSONCommand,
    JSONFormatCommand
)


def test_json_validator():
    """JSON検証のテスト"""
    print("=== JSON検証のテスト ===")
    
    validator = JSONValidator()
    
    # 有効なJSONデータ
    valid_data = {
        "version": "1.0.0",
        "settings": {"debug": True},
        "data": [1, 2, 3]
    }
    
    # 無効なJSONデータ
    invalid_data = {
        "settings": {"debug": "not_boolean"},
        "data": "not_array"
    }
    
    # 基本スキーマで検証
    result1 = validator.validate(valid_data, "basic")
    print(f"有効データの検証: {result1.valid} - {result1.message}")
    
    result2 = validator.validate(invalid_data, "basic")
    print(f"無効データの検証: {result2.valid} - {result2.message}")
    
    # 設定スキーマで検証
    result3 = validator.validate(valid_data, "config")
    print(f"設定スキーマでの検証: {result3.valid} - {result3.message}")
    
    return result1.valid and result3.valid


def test_jsonpath_processor():
    """JSONPath処理のテスト"""
    print("\n=== JSONPath処理のテスト ===")
    
    processor = JSONPathProcessor()
    
    # テストデータ
    data = {
        "users": [
            {"name": "Alice", "age": 30, "city": "Tokyo"},
            {"name": "Bob", "age": 25, "city": "Osaka"},
            {"name": "Charlie", "age": 35, "city": "Tokyo"}
        ],
        "config": {
            "version": "2.0.0",
            "debug": True
        }
    }
    
    # JSONPathクエリのテスト
    names = processor.query_all(data, "$.users[*].name")
    print(f"全ユーザー名: {names}")
    
    tokyo_users = processor.query_all(data, "$.users[?(@.city == 'Tokyo')].name")
    print(f"東京のユーザー: {tokyo_users}")
    
    first_user = processor.query_first(data, "$.users[0].name")
    print(f"最初のユーザー: {first_user}")
    
    user_count = processor.count(data, "$.users[*]")
    print(f"ユーザー数: {user_count}")
    
    # 集約のテスト
    avg_age = processor.aggregate(data, "$.users[*].age", "avg")
    print(f"平均年齢: {avg_age}")
    
    return len(names) == 3 and len(tokyo_users) == 2


def test_format_converter():
    """形式変換のテスト"""
    print("\n=== 形式変換のテスト ===")
    
    converter = FormatConverter()
    
    # テストデータ
    data = {
        "app": {
            "name": "TestApp",
            "version": "1.0.0"
        },
        "features": ["auth", "logging"]
    }
    
    # JSON → YAML変換
    json_str = json.dumps(data, indent=2)
    yaml_result = converter.convert(json_str, "json", "yaml")
    
    if yaml_result.success:
        print("JSON → YAML変換成功:")
        print(yaml_result.data)
    else:
        print(f"JSON → YAML変換失敗: {yaml_result.error}")
    
    # YAML → JSON変換
    if yaml_result.success:
        json_result = converter.convert(yaml_result.data, "yaml", "json")
        if json_result.success:
            print("\nYAML → JSON変換成功:")
            print(json_result.data)
        else:
            print(f"YAML → JSON変換失敗: {json_result.error}")
    
    # 形式自動検出
    detected_format = converter.detect_format(json_str)
    print(f"\n自動検出された形式: {detected_format}")
    
    return yaml_result.success


async def test_json_commands():
    """JSONコマンドのテスト"""
    print("\n=== JSONコマンドのテスト ===")
    
    # テストデータ
    data = {
        "products": [
            {"id": 1, "name": "Product A", "price": 100, "category": "electronics"},
            {"id": 2, "name": "Product B", "price": 200, "category": "books"},
            {"id": 3, "name": "Product C", "price": 150, "category": "electronics"}
        ],
        "metadata": {
            "total": 3,
            "updated": "2024-01-01"
        }
    }
    
    # JSONPathコマンドのテスト
    jsonpath_cmd = JSONPathCommand()
    
    # 全商品名を取得
    names = await jsonpath_cmd.execute(data, path="$.products[*].name")
    print(f"商品名: {names}")
    
    # 電子機器カテゴリの商品数
    electronics_count = await jsonpath_cmd.execute(
        data, 
        path="$.products[?(@.category == 'electronics')]",
        operation="count"
    )
    print(f"電子機器商品数: {electronics_count}")
    
    # JSON変換コマンドのテスト
    transform_cmd = JSONTransformCommand()
    
    # 価格の合計を計算
    total_price = await transform_cmd.execute(
        data,
        transformations=[{
            "path": "$.products[*].price",
            "operation": "sum"
        }],
        output_format="dict"
    )
    print(f"価格合計: {total_price}")
    
    # JSON形式変換コマンドのテスト
    format_cmd = JSONFormatCommand()
    
    yaml_output = await format_cmd.execute(data, to_format="yaml")
    print(f"\nYAML形式:\n{yaml_output}")
    
    return len(names) == 3 and electronics_count == 2


def main():
    """メイン関数"""
    print("JSON処理機能のテストを開始します...\n")
    
    try:
        # 各テストを実行
        result1 = test_json_validator()
        result2 = test_jsonpath_processor()
        result3 = test_format_converter()
        
        # 非同期テスト
        import asyncio
        result4 = asyncio.run(test_json_commands())
        
        print(f"\n=== テスト結果 ===")
        print(f"JSON検証: {'✓' if result1 else '✗'}")
        print(f"JSONPath処理: {'✓' if result2 else '✗'}")
        print(f"形式変換: {'✓' if result3 else '✗'}")
        print(f"JSONコマンド: {'✓' if result4 else '✗'}")
        
        if all([result1, result2, result3, result4]):
            print("\n🎉 すべてのテストが成功しました！")
        else:
            print("\n❌ 一部のテストが失敗しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

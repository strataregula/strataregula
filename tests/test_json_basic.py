#!/usr/bin/env python3
"""
JSON処理の基本機能テスト（外部依存関係なし）
"""

import json
from strataregula.json_processor import FormatConverter, ConversionResult


def test_format_converter_comprehensive():
    """形式変換の包括的テスト"""
    print("=== 形式変換の包括的テスト ===")
    
    converter = FormatConverter()
    
    # テストデータ
    test_data = {
        "application": {
            "name": "StrataRegula",
            "version": "0.0.1",
            "config": {
                "debug": True,
                "port": 8080,
                "features": ["json", "yaml", "hierarchy"]
            }
        },
        "users": [
            {"id": 1, "name": "Alice", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"}
        ]
    }
    
    print("元データ:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    
    # JSON → YAML
    json_str = json.dumps(test_data)
    yaml_result = converter.convert(json_str, "json", "yaml")
    
    if yaml_result.success:
        print("\n✅ JSON → YAML変換成功:")
        print(yaml_result.data)
        
        # YAML → JSON (逆変換)
        json_result = converter.convert(yaml_result.data, "yaml", "json")
        if json_result.success:
            print("\n✅ YAML → JSON変換成功:")
            parsed_back = json.loads(json_result.data)
            print(json.dumps(parsed_back, indent=2, ensure_ascii=False))
            
            # データの整合性チェック
            if parsed_back == test_data:
                print("\n✅ データの整合性確認: 完全一致")
                return True
            else:
                print("\n❌ データの整合性確認: 不一致")
                return False
        else:
            print(f"\n❌ YAML → JSON変換失敗: {json_result.error}")
            return False
    else:
        print(f"\n❌ JSON → YAML変換失敗: {yaml_result.error}")
        return False


def test_format_detection():
    """形式自動検出のテスト"""
    print("\n=== 形式自動検出のテスト ===")
    
    converter = FormatConverter()
    
    # 各形式のテストデータ
    test_cases = [
        ('{"key": "value"}', 'json'),
        ('[1, 2, 3]', 'json'),
        ('key: value\nlist:\n  - item1\n  - item2', 'yaml'),
        ('<root><item>value</item></root>', 'xml'),
        ('name,age\nAlice,30\nBob,25', 'csv'),
        ('name\tage\nAlice\t30\nBob\t25', 'tsv')
    ]
    
    success_count = 0
    for data, expected in test_cases:
        detected = converter.detect_format(data)
        result = "✅" if detected == expected else "❌"
        print(f"{result} '{data[:20]}...' → 検出: {detected}, 期待: {expected}")
        if detected == expected:
            success_count += 1
    
    print(f"\n形式検出成功率: {success_count}/{len(test_cases)}")
    return success_count == len(test_cases)


def test_supported_formats():
    """サポート形式のテスト"""
    print("\n=== サポート形式のテスト ===")
    
    converter = FormatConverter()
    
    supported = converter.get_supported_formats()
    print(f"サポートされている形式: {supported}")
    
    # 各形式のサポート確認
    test_formats = ['json', 'yaml', 'xml', 'csv', 'tsv']
    for fmt in test_formats:
        is_supported = converter.is_format_supported(fmt)
        result = "✅" if is_supported else "❌"
        print(f"{result} {fmt}: {'サポート' if is_supported else '非サポート'}")
    
    return all(converter.is_format_supported(fmt) for fmt in test_formats)


def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n=== エラーハンドリングのテスト ===")
    
    converter = FormatConverter()
    
    # 無効なJSONデータ
    invalid_json = '{"invalid": json}'
    result = converter.convert(invalid_json, "json", "yaml")
    
    if not result.success:
        print(f"✅ 無効JSON検出: {result.error}")
        error_test1 = True
    else:
        print("❌ 無効JSONが検出されませんでした")
        error_test1 = False
    
    # サポートされていない形式
    valid_data = '{"key": "value"}'
    result2 = converter.convert(valid_data, "json", "unsupported_format")
    
    if not result2.success:
        print(f"✅ 非サポート形式検出: {result2.error}")
        error_test2 = True
    else:
        print("❌ 非サポート形式が検出されませんでした")
        error_test2 = False
    
    return error_test1 and error_test2


def main():
    """メイン関数"""
    print("JSON処理基本機能のテストを開始します...\n")
    
    try:
        # 各テストを実行
        result1 = test_format_converter_comprehensive()
        result2 = test_format_detection()
        result3 = test_supported_formats()
        result4 = test_error_handling()
        
        print(f"\n=== 最終テスト結果 ===")
        print(f"包括的形式変換: {'✅' if result1 else '❌'}")
        print(f"形式自動検出: {'✅' if result2 else '❌'}")
        print(f"サポート形式確認: {'✅' if result3 else '❌'}")
        print(f"エラーハンドリング: {'✅' if result4 else '❌'}")
        
        success_count = sum([result1, result2, result3, result4])
        print(f"\n成功率: {success_count}/4")
        
        if success_count == 4:
            print("\n🎉 すべてのテストが成功しました！")
            print("JSON処理の基本機能は正常に動作しています。")
        else:
            print(f"\n⚠️ {4-success_count}個のテストが失敗しました")
        
        return success_count == 4
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()

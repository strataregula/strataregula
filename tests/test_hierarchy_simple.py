#!/usr/bin/env python3
"""
簡単な階層処理テスト

このファイルを直接実行して階層処理の動作を確認できます。
"""

from strataregula.hierarchy import HierarchyMerger, MergeStrategy

def quick_test():
    """クイックテスト"""
    print("階層処理のクイックテスト")
    print("=" * 40)
    
    # 基本設定
    base = {
        'app': {
            'name': 'TestApp',
            'version': '1.0.0',
            'config': {
                'debug': False,
                'port': 8000
            }
        },
        'features': ['basic', 'simple']
    }
    
    # オーバーライド設定
    override = {
        'app': {
            'version': '2.0.0',
            'config': {
                'debug': True,
                'port': 9000,
                'new_option': 'value'
            }
        },
        'features': ['basic', 'simple', 'advanced']
    }
    
    print("基本設定:")
    print(f"  app.name: {base['app']['name']}")
    print(f"  app.version: {base['app']['version']}")
    print(f"  app.config.debug: {base['app']['config']['debug']}")
    print(f"  app.config.port: {base['app']['config']['port']}")
    print(f"  features: {base['features']}")
    
    print("\nオーバーライド設定:")
    print(f"  app.version: {override['app']['version']}")
    print(f"  app.config.debug: {override['app']['config']['debug']}")
    print(f"  app.config.port: {override['app']['config']['port']}")
    print(f"  app.config.new_option: {override['app']['config']['new_option']}")
    print(f"  features: {override['features']}")
    
    # マージ実行
    merger = HierarchyMerger(MergeStrategy.SMART)
    result = merger.merge(base, override)
    
    print("\nマージ結果:")
    print(f"  app.name: {result['app']['name']}")
    print(f"  app.version: {result['app']['version']}")
    print(f"  app.config.debug: {result['app']['config']['debug']}")
    print(f"  app.config.port: {result['app']['config']['port']}")
    print(f"  app.config.new_option: {result['app']['config']['new_option']}")
    print(f"  features: {result['features']}")
    
    print("\n✓ テスト完了！")
    return result

if __name__ == "__main__":
    quick_test()

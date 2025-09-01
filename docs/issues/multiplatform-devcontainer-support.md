# [0.5] マルチプラットフォーム対応（DevContainer）

**Labels**: `backlog`, `target-0.5`, `devcontainer`, `infrastructure`, `enhancement`, `priority-p1`  
**Milestone**: `v0.5.0`  
**Priority**: P1 (次期重要実装)

## 📋 目的
現在のWindows/Ubuntu限定環境から、DevContainer基盤によるフルマルチプラットフォーム対応へ拡張。macOS、各種Linux distro、ARM64アーキテクチャでの完全互換性を確保し、開発環境の統一とセキュリティ強化を実現する。

## 🎯 具体的な仕様

### 対応プラットフォーム Matrix
```
Platform Support Matrix (Target)
┌─────────────────┬──────────┬───────────┬─────────┬──────────┐
│ Platform        │ x64      │ ARM64     │ Status  │ Priority │
├─────────────────┼──────────┼───────────┼─────────┼──────────┤
│ Ubuntu 20.04+   │    ✅    │    ✅     │ Native  │   P0     │
│ Windows 10/11   │    ✅    │    🔄     │ WSL2    │   P0     │
│ macOS 12+       │    ✅    │    ✅     │ Docker  │   P1     │
│ Alpine Linux    │    ✅    │    ✅     │ Docker  │   P1     │
│ CentOS/RHEL     │    ✅    │    ❌     │ Docker  │   P2     │
│ Debian          │    ✅    │    ✅     │ Docker  │   P2     │
└─────────────────┴──────────┴───────────┴─────────┴──────────┘
```

### DevContainer設定階層
```
.devcontainer/
├─ devcontainer.json           # メイン設定
├─ docker-compose.yml          # 複数コンテナ構成
├─ Dockerfile                  # カスタムイメージ
├─ platforms/                  # プラットフォーム固有設定
│  ├─ ubuntu.json             # Ubuntu特化設定
│  ├─ windows.json            # Windows/WSL2設定  
│  ├─ macos.json              # macOS特化設定
│  └─ arm64.json              # ARM64最適化
├─ scripts/                    # セットアップスクリプト
│  ├─ post-create.sh          # コンテナ作成後スクリプト
│  ├─ post-start.sh           # 開始時スクリプト
│  └─ post-attach.sh          # アタッチ後スクリプト
└─ features/                   # Dev Container Features
   ├─ performance-tools.json   # Performance toolchain
   ├─ security-scanning.json   # Security toolchain  
   └─ python-optimization.json # Python最適化環境
```

## 🔧 技術仕様

### メインDevContainer設定
```json
// .devcontainer/devcontainer.json
{
  "name": "Strataregula Performance Engineering",
  "dockerComposeFile": "docker-compose.yml",
  "service": "strataregula-dev",
  "workspaceFolder": "/workspace",
  
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11",
      "installTools": true,
      "optimize": true
    },
    "ghcr.io/devcontainers/features/powershell:1": {
      "version": "latest"
    },
    "ghcr.io/devcontainers/features/git:1": {
      "version": "latest",
      "ppa": true
    }
  },
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.flake8",
        "ms-python.black-formatter",
        "ms-vscode.powershell",
        "github.vscode-github-actions"
      ],
      "settings": {
        "python.defaultInterpreterPath": "/usr/local/bin/python",
        "python.linting.enabled": true,
        "python.formatting.provider": "black"
      }
    }
  },
  
  "postCreateCommand": ".devcontainer/scripts/post-create.sh",
  "postStartCommand": ".devcontainer/scripts/post-start.sh",
  "postAttachCommand": ".devcontainer/scripts/post-attach.sh",
  
  "forwardPorts": [8000, 5000, 3000],
  "portsAttributes": {
    "8000": {
      "label": "Performance Dashboard",
      "onAutoForward": "notify"
    }
  },
  
  "remoteUser": "vscode",
  "containerUser": "vscode"
}
```

### Docker Compose構成
```yaml
# .devcontainer/docker-compose.yml
version: '3.8'

services:
  strataregula-dev:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        PLATFORM: ${PLATFORM:-linux/amd64}
        PYTHON_VERSION: "3.11"
    
    volumes:
      - ../:/workspace:cached
      - ~/.gitconfig:/home/vscode/.gitconfig:ro
      - ~/.ssh:/home/vscode/.ssh:ro
      
    environment:
      - PYTHONPATH=/workspace
      - PYTHONIOENCODING=utf-8
      - PYTHONUTF8=1
      - PERFORMANCE_ENV=development
      - CONTAINER_PLATFORM=${PLATFORM:-linux/amd64}
      
    platform: ${PLATFORM:-linux/amd64}
    
    # セキュリティ設定
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - SYS_PTRACE  # デバッガ・プロファイラ用
      
    networks:
      - strataregula-network

  # Performance monitoring service
  performance-monitor:
    image: prom/prometheus:latest
    platform: ${PLATFORM:-linux/amd64}
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - strataregula-network

networks:
  strataregula-network:
    driver: bridge
```

### Multi-arch Dockerfile
```dockerfile
# .devcontainer/Dockerfile
ARG PYTHON_VERSION=3.11
FROM --platform=$BUILDPLATFORM python:${PYTHON_VERSION}-slim

# プラットフォーム自動検出
ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG PLATFORM

# 共通パッケージインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# PowerShell Core インストール (プラットフォーム対応)
RUN if [ "$TARGETPLATFORM" = "linux/amd64" ]; then \
        curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg && \
        echo "deb [arch=amd64,armhf,arm64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/microsoft-debian-bullseye-prod bullseye main" > /etc/apt/sources.list.d/microsoft.list && \
        apt-get update && apt-get install -y powershell; \
    elif [ "$TARGETPLATFORM" = "linux/arm64" ]; then \
        curl -sSL https://github.com/PowerShell/PowerShell/releases/latest/download/powershell_arm64.deb -o powershell.deb && \
        dpkg -i powershell.deb && rm powershell.deb; \
    fi

# GitLeaks インストール (アーキテクチャ対応)  
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "amd64" ]; then GITLEAKS_ARCH="x64"; \
    elif [ "$ARCH" = "arm64" ]; then GITLEAKS_ARCH="arm64"; \
    else echo "Unsupported architecture: $ARCH" && exit 1; fi && \
    curl -sSL "https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_${GITLEAKS_ARCH}.tar.gz" | \
    tar xz && mv gitleaks /usr/local/bin/

# Python最適化・プロファイリングツール
RUN pip install --no-cache-dir \
    py-spy \
    memory-profiler \
    cprofilev \
    line-profiler

# ユーザー設定
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    usermod -aG sudo $USERNAME && \
    echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER $USERNAME
WORKDIR /workspace

# プラットフォーム固有の最適化
COPY .devcontainer/scripts/platform-optimize.sh /tmp/
RUN chmod +x /tmp/platform-optimize.sh && /tmp/platform-optimize.sh $TARGETPLATFORM
```

### プラットフォーム固有最適化
```bash
#!/bin/bash
# .devcontainer/scripts/platform-optimize.sh

PLATFORM=$1

case $PLATFORM in
    "linux/amd64")
        echo "Optimizing for x64 Linux..."
        # AVX2最適化
        export CFLAGS="-march=native -O3"
        # NumPy/SciPy最適化版インストール
        pip install --force-reinstall numpy scipy
        ;;
    "linux/arm64")  
        echo "Optimizing for ARM64 Linux..."
        # ARM NEON最適化
        export CFLAGS="-march=armv8-a+fp+simd -O3"
        # ARM最適化版ライブラリ
        pip install --extra-index-url https://www.piwheels.org/simple/ numpy scipy
        ;;
    "darwin/amd64"|"darwin/arm64")
        echo "Optimizing for macOS..."
        # macOS特有の最適化
        export MACOSX_DEPLOYMENT_TARGET=12.0
        ;;
    *)
        echo "Generic optimization for $PLATFORM"
        ;;
esac

# プラットフォーム共通最適化
echo "Applying common optimizations..."
pip install --upgrade pip setuptools wheel
```

## 🔄 プラットフォーム自動検出システム

### 実行環境判定
```python
# performance/utils/platform_detection.py
import platform
import os
import subprocess
from dataclasses import dataclass
from typing import Optional

@dataclass
class PlatformInfo:
    os_name: str           # "linux", "windows", "darwin"  
    arch: str              # "x86_64", "aarch64", "arm64"
    distro: Optional[str]  # "ubuntu", "alpine", "centos", etc.
    version: str           # OS version
    container: bool        # Running in container
    devcontainer: bool     # Running in DevContainer
    ci: bool              # Running in CI environment
    
    @property
    def platform_key(self) -> str:
        """プラットフォーム識別キー"""
        return f"{self.os_name}-{self.arch}"
    
    @property
    def performance_multiplier(self) -> float:
        """パフォーマンス補正値"""
        multipliers = {
            "linux-x86_64": 1.0,      # ベースライン
            "linux-aarch64": 0.85,    # ARM64は15%程度遅い
            "darwin-x86_64": 1.1,     # macOS Intelは10%高速  
            "darwin-arm64": 1.2,      # Apple Siliconは20%高速
            "windows-x86_64": 0.9,    # Windows/WSL2は10%遅い
        }
        return multipliers.get(self.platform_key, 1.0)

def detect_platform() -> PlatformInfo:
    """現在の実行プラットフォーム検出"""
    os_name = platform.system().lower()
    if os_name == "darwin":
        os_name = "macos"
    
    arch = platform.machine().lower()
    if arch in ["aarch64", "arm64"]:
        arch = "arm64"
    elif arch in ["x86_64", "amd64"]:
        arch = "x64"
        
    # コンテナ検出
    container = os.path.exists("/.dockerenv") or \
                os.environ.get("container") is not None
                
    # DevContainer検出
    devcontainer = os.environ.get("REMOTE_CONTAINERS") == "true" or \
                   os.environ.get("CODESPACES") == "true"
    
    # CI環境検出  
    ci = os.environ.get("CI") == "true" or \
         os.environ.get("GITHUB_ACTIONS") == "true"
         
    # Linux distro検出
    distro = None
    if os_name == "linux":
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        except FileNotFoundError:
            pass
            
    return PlatformInfo(
        os_name=os_name,
        arch=arch, 
        distro=distro,
        version=platform.release(),
        container=container,
        devcontainer=devcontainer,
        ci=ci
    )
```

### プラットフォーム適応ベンチマーク
```python
# performance/tools/adaptive_perf_suite.py
class AdaptivePerfSuite:
    def __init__(self):
        self.platform = detect_platform()
        self.config = self.load_platform_config()
    
    def load_platform_config(self) -> dict:
        """プラットフォーム固有設定読み込み"""
        config_file = f"performance/configs/{self.platform.platform_key}.yaml"
        if os.path.exists(config_file):
            return yaml.load(open(config_file))
        else:
            return self.get_default_config()
    
    def adjust_benchmark_parameters(self, base_params: dict) -> dict:
        """プラットフォーム応じたパラメータ調整"""
        adjusted = base_params.copy()
        
        # ARM64では反復回数を調整
        if self.platform.arch == "arm64":
            adjusted["iterations"] = int(base_params["iterations"] * 0.8)
            adjusted["warmup"] = int(base_params["warmup"] * 0.8)
        
        # CI環境では軽量化
        if self.platform.ci:
            adjusted["iterations"] = min(adjusted["iterations"], 500)
            adjusted["timeout"] = 60  # 1分制限
            
        # DevContainer環境では詳細ログ
        if self.platform.devcontainer:
            adjusted["verbose"] = True
            adjusted["include_system_info"] = True
            
        return adjusted
    
    def get_performance_baseline(self) -> dict:
        """プラットフォーム固有のベースライン値"""
        baselines = {
            "linux-x64": {"p50_target": 15.0, "p95_target": 12.0},
            "linux-arm64": {"p50_target": 12.8, "p95_target": 10.2},  # 15%調整
            "macos-x64": {"p50_target": 16.5, "p95_target": 13.2},    # 10%向上
            "macos-arm64": {"p50_target": 18.0, "p95_target": 14.4},  # 20%向上
            "windows-x64": {"p50_target": 13.5, "p95_target": 10.8},  # 10%低下
        }
        
        return baselines.get(
            self.platform.platform_key,
            {"p50_target": 15.0, "p95_target": 12.0}  # デフォルト
        )
```

## 📊 成功指標

### 互換性要件
- **Primary Platforms**: Ubuntu x64/ARM64, Windows WSL2, macOS x64/ARM64で100%動作
- **Secondary Platforms**: Alpine, Debian, CentOSで95%以上動作  
- **Architecture Support**: x64/ARM64両対応、自動検出・最適化
- **Container Compatibility**: Docker Desktop, Podman, containerdサポート

### パフォーマンス要件
- **Platform Parity**: 各プラットフォーム間での性能差 < 20%
- **Startup Time**: DevContainer起動時間 < 2分
- **Resource Usage**: メモリ使用量 < 2GB、CPU負荷 < 50%
- **Build Time**: マルチアーキテクチャビルド < 10分

### 開発体験要件
- **Zero Configuration**: `code .` でのワンクリック環境構築
- **Tool Consistency**: 全プラットフォームでの統一ツールチェーン
- **Debug Support**: プロファイラ・デバッガ完全対応
- **Extension Sync**: VS Code拡張の自動同期

## 🔧 セキュリティ強化

### コンテナセキュリティ設定
```json
// セキュリティ強化設定
{
  "runArgs": [
    "--security-opt=no-new-privileges:true",
    "--cap-drop=ALL", 
    "--cap-add=SYS_PTRACE",  // プロファイラ用のみ
    "--read-only",           // 読み取り専用ルートファイルシステム
    "--tmpfs=/tmp:rw,noexec,nosuid,size=1g"
  ],
  
  "mounts": [
    "source=/var/run/docker.sock,target=/var/run/docker-host.sock,type=bind,readonly"
  ],
  
  "containerEnv": {
    "DOCKER_HOST": "unix:///var/run/docker-host.sock",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONUNBUFFERED": "1"
  }
}
```

### Secret管理統合
```bash
# .devcontainer/scripts/post-create.sh
#!/bin/bash

# DevContainer固有のセキュリティスキャン設定
echo "Setting up DevContainer security..."

# セキュリティスキャンツール設定
python -m security.tools.sec_scan --setup-devcontainer

# Git hooks設定（セキュリティチェック）
git config core.hooksPath .devcontainer/git-hooks

# 環境固有allowlist設定
cp .devcontainer/security-allowlist-devcontainer.yaml security-allowlist.yaml

echo "DevContainer security setup completed!"
```

## 🔄 実装戦略

### Phase 1: 基盤構築 (Week 1-2)
1. DevContainer基本設定作成
2. Ubuntu/Windows/macOS基本対応確認
3. プラットフォーム自動検出システム実装
4. セキュリティ設定基盤整備

### Phase 2: Multi-arch対応 (Week 2-3)
1. Docker multi-platform buildシステム
2. ARM64最適化・テスト
3. プラットフォーム固有パフォーマンス調整
4. CI/CD統合・自動テスト

### Phase 3: 開発体験最適化 (Week 3-4)
1. VS Code統合・拡張セットアップ
2. デバッグ・プロファイリング環境
3. ドキュメント・チュートリアル整備
4. トラブルシューティングガイド

### Phase 4: Production準備 (Week 4-5)
1. セキュリティ監査・強化
2. パフォーマンステスト・最適化
3. Multi-platform CI validation
4. Migration guide・Rollout plan

## 🚫 非目標・制約事項

### 現在のスコープ外
- **Windows Native**: WSL2経由のみ対応
- **古いOS版**: 3年以内のLTSバージョンのみ  
- **Embedded Systems**: IoT・組み込み用途は非対象
- **GPU Acceleration**: CPU最適化のみ、GPU未対応
- **Kubernetes**: 単一コンテナのみ、オーケストレーション未対応

### 制約事項
- **Docker依存**: Docker Desktopまたは互換環境必須
- **VS Code前提**: DevContainerはVS Code統合中心
- **ネットワーク要件**: イメージプル・パッケージインストール要
- **ストレージ要件**: 最低5GB、推奨10GB以上

## 🔗 関連・依存 Issues

### 前提条件
- ✅ Performance Tools MVP (0.3.0) - 基盤ツール群
- ✅ Security強化 (0.4.0予定) - コンテナセキュリティ基盤
- ✅ CP932/UTF-8 compatibility - 国際化対応完了

### 依存関係
- ⏳ **CI完全統合** (0.4.0) - Multi-platform CI統合
- ⏳ **Performance ドキュメント** (0.4.0) - DevContainer使用ガイド

### 後続発展
- **Performance Dashboard** (0.5.0) - Web UI コンテナ化
- **Distributed Benchmarking** (0.6.0) - 複数コンテナ並列実行
- **Cloud Integration** (0.6.0) - クラウドDevContainer

## ✅ 完了条件 (Definition of Done)

### 技術要件
- [ ] 5+ プラットフォーム・アーキテクチャ対応確認
- [ ] プラットフォーム自動検出・最適化動作確認
- [ ] セキュリティ設定・スキャン統合完了
- [ ] Multi-arch Docker image build成功

### 互換性要件
- [ ] Ubuntu 20.04+ (x64/ARM64) 完全動作
- [ ] Windows 10/11 WSL2 完全動作
- [ ] macOS 12+ (Intel/Apple Silicon) 完全動作
- [ ] Alpine/Debian コンテナ動作確認

### 開発体験要件
- [ ] VS Code DevContainer統合確認
- [ ] ワンクリック環境構築動作
- [ ] デバッグ・プロファイリング機能確認
- [ ] Performance tools全機能動作確認

### セキュリティ要件
- [ ] コンテナセキュリティ設定監査通過
- [ ] Secret管理システム統合確認
- [ ] 最小権限原則適用確認
- [ ] セキュリティスキャン統合動作確認

---

**推定工数**: 4-5 weeks  
**担当者**: DevOps + Platform Engineering Team  
**レビュワー**: Security Team + Development Team  
**作成日**: 2025-09-01  
**最終更新**: 2025-09-01
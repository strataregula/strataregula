# [0.5] リアルタイム監視システム

**Labels**: `backlog`, `target-0.5`, `monitoring`, `observability`, `enhancement`, `priority-p1`  
**Milestone**: `v0.5.0`  
**Priority**: P1 (次期重要実装)

## 📋 目的
パフォーマンスメトリクスのライブ監視基盤を構築し、Prometheus/Grafana統合によるリアルタイム可視化とアラート機能付き回帰検出を実現。開発環境から本番環境まで一貫した監視体制を確立する。

## 🎯 具体的な仕様

### システムアーキテクチャ
```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Architecture                    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Application Layer                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ perf_suite   │  │ perf_guard   │  │ perf_analyze │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│  ┌──────▼──────────────────▼──────────────────▼───────┐     │
│  │          Metrics Exporter (Prometheus Client)       │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         │                                     │
│  Data Collection Layer  │                                     │
│  ┌──────────────────────▼──────────────────────────────┐     │
│  │              Prometheus Server                       │     │
│  │  - Time Series Database                             │     │
│  │  - Metrics Aggregation                              │     │
│  │  - AlertManager Integration                         │     │
│  └──────────────────────┬──────────────────────────────┘     │
│                         │                                     │
│  Visualization Layer    │                                     │
│  ┌──────────────────────▼──────────────────────────────┐     │
│  │                  Grafana                             │     │
│  │  - Real-time Dashboards                            │     │
│  │  - Historical Trends                                │     │
│  │  - Alert Visualization                              │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│  Alert Layer                                                  │
│  ┌────────────────────────────────────────────────────┐      │
│  │              AlertManager                          │      │
│  │  - Routing Rules                                   │      │
│  │  - Notification Channels (Email/Slack/PagerDuty)  │      │
│  └────────────────────────────────────────────────────┘      │
└───────────────────────────────────────────────────────────────┘
```

### メトリクス定義
```yaml
# monitoring/metrics.yaml
metrics:
  # パフォーマンスメトリクス
  performance:
    - name: benchmark_execution_time_ms
      type: histogram
      description: "ベンチマーク実行時間 (milliseconds)"
      labels: ["benchmark_name", "iteration", "environment"]
      buckets: [5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000]
    
    - name: speedup_ratio
      type: gauge
      description: "ベースライン対比スピードアップ率"
      labels: ["benchmark_name", "percentile", "baseline_version"]
    
    - name: performance_regression_detected
      type: counter
      description: "パフォーマンス回帰検出回数"
      labels: ["benchmark_name", "severity", "commit_hash"]
  
  # リソースメトリクス
  resources:
    - name: memory_usage_mb
      type: gauge
      description: "メモリ使用量 (MB)"
      labels: ["process", "phase"]
    
    - name: cpu_utilization_percent
      type: gauge
      description: "CPU使用率 (%)"
      labels: ["core", "process"]
  
  # システムメトリクス
  system:
    - name: benchmark_suite_duration_seconds
      type: summary
      description: "全ベンチマークスイート実行時間"
      quantiles: [0.5, 0.9, 0.95, 0.99]
    
    - name: ci_pipeline_status
      type: gauge
      description: "CIパイプラインステータス (0=fail, 1=pass)"
      labels: ["pipeline", "branch", "trigger"]
```

## 🔧 技術実装

### Prometheus Exporter統合
```python
# performance/monitoring/prometheus_exporter.py
from prometheus_client import (
    Histogram, Gauge, Counter, Summary,
    start_http_server, CollectorRegistry
)
import time
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class MetricsCollector:
    """Prometheusメトリクス収集・エクスポート"""
    
    def __init__(self, port: int = 8000):
        self.registry = CollectorRegistry()
        self.port = port
        self._setup_metrics()
    
    def _setup_metrics(self):
        """メトリクス定義"""
        # パフォーマンスメトリクス
        self.benchmark_time = Histogram(
            'benchmark_execution_time_ms',
            'Benchmark execution time in milliseconds',
            ['benchmark_name', 'iteration', 'environment'],
            buckets=[5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
            registry=self.registry
        )
        
        self.speedup_ratio = Gauge(
            'speedup_ratio',
            'Speedup ratio compared to baseline',
            ['benchmark_name', 'percentile', 'baseline_version'],
            registry=self.registry
        )
        
        self.regression_counter = Counter(
            'performance_regression_detected',
            'Number of performance regressions detected',
            ['benchmark_name', 'severity', 'commit_hash'],
            registry=self.registry
        )
        
        # リソースメトリクス
        self.memory_usage = Gauge(
            'memory_usage_mb',
            'Memory usage in megabytes',
            ['process', 'phase'],
            registry=self.registry
        )
        
        self.cpu_utilization = Gauge(
            'cpu_utilization_percent',
            'CPU utilization percentage',
            ['core', 'process'],
            registry=self.registry
        )
        
        # システムメトリクス
        self.suite_duration = Summary(
            'benchmark_suite_duration_seconds',
            'Total benchmark suite execution time',
            registry=self.registry
        )
    
    def start_server(self):
        """Prometheus HTTPサーバー起動"""
        start_http_server(self.port, registry=self.registry)
        print(f"Prometheus metrics available at http://localhost:{self.port}/metrics")
    
    def record_benchmark(self, benchmark_name: str, execution_time_ms: float, 
                        iteration: int, environment: str = "development"):
        """ベンチマーク結果記録"""
        self.benchmark_time.labels(
            benchmark_name=benchmark_name,
            iteration=iteration,
            environment=environment
        ).observe(execution_time_ms)
    
    def update_speedup(self, benchmark_name: str, percentile: str, 
                      ratio: float, baseline_version: str = "v0.3.0"):
        """スピードアップ率更新"""
        self.speedup_ratio.labels(
            benchmark_name=benchmark_name,
            percentile=percentile,
            baseline_version=baseline_version
        ).set(ratio)
    
    def record_regression(self, benchmark_name: str, severity: str, 
                         commit_hash: str):
        """回帰検出記録"""
        self.regression_counter.labels(
            benchmark_name=benchmark_name,
            severity=severity,
            commit_hash=commit_hash
        ).inc()

# Integration with perf_suite
class MonitoredPerfSuite:
    """監視機能付きベンチマークスイート"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.metrics.start_server()
    
    def run_benchmark_with_monitoring(self, benchmark_func, name: str):
        """監視付きベンチマーク実行"""
        start_time = time.time()
        
        # メモリ使用量監視開始
        import psutil
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # ベンチマーク実行
        result = benchmark_func()
        
        # メトリクス記録
        execution_time_ms = (time.time() - start_time) * 1000
        self.metrics.record_benchmark(name, execution_time_ms, 1)
        
        # メモリ使用量記録
        final_memory = process.memory_info().rss / 1024 / 1024
        self.metrics.memory_usage.labels(
            process=name, 
            phase="peak"
        ).set(final_memory - initial_memory)
        
        # CPU使用率記録
        cpu_percent = process.cpu_percent(interval=0.1)
        self.metrics.cpu_utilization.labels(
            core="all",
            process=name
        ).set(cpu_percent)
        
        return result
```

### Grafana Dashboard設定
```json
// monitoring/dashboards/performance-overview.json
{
  "dashboard": {
    "title": "Strataregula Performance Overview",
    "panels": [
      {
        "title": "Benchmark Execution Time (P50/P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(benchmark_execution_time_ms_bucket[5m]))",
            "legendFormat": "P50 - {{ benchmark_name }}"
          },
          {
            "expr": "histogram_quantile(0.95, rate(benchmark_execution_time_ms_bucket[5m]))",
            "legendFormat": "P95 - {{ benchmark_name }}"
          }
        ]
      },
      {
        "title": "Speedup Ratio Trend",
        "type": "graph",
        "targets": [
          {
            "expr": "speedup_ratio{percentile='p50'}",
            "legendFormat": "{{ benchmark_name }} - P50"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [15.0],
                "type": "lt"
              },
              "operator": {
                "type": "and"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "params": [],
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "name": "Performance Below Threshold"
        }
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "memory_usage_mb",
            "legendFormat": "{{ process }} - {{ phase }}"
          }
        ]
      },
      {
        "title": "Regression Detection Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(performance_regression_detected[1h])",
            "legendFormat": "Regressions/hour"
          }
        ]
      }
    ]
  }
}
```

### AlertManager設定
```yaml
# monitoring/alertmanager/alerts.yaml
groups:
  - name: performance_alerts
    interval: 30s
    rules:
      # 重大なパフォーマンス劣化
      - alert: CriticalPerformanceRegression
        expr: speedup_ratio{percentile="p50"} < 10.0
        for: 5m
        labels:
          severity: critical
          team: performance-engineering
        annotations:
          summary: "Critical performance regression detected"
          description: "{{ $labels.benchmark_name }} P50 speedup is {{ $value }}x (threshold: 10.0x)"
          
      # 高いメモリ使用量
      - alert: HighMemoryUsage
        expr: memory_usage_mb > 1000
        for: 10m
        labels:
          severity: warning
          team: performance-engineering
        annotations:
          summary: "High memory usage detected"
          description: "Process {{ $labels.process }} using {{ $value }}MB"
      
      # CI失敗率
      - alert: HighCIFailureRate
        expr: rate(ci_pipeline_status{status="0"}[1h]) > 0.2
        for: 30m
        labels:
          severity: warning
          team: devops
        annotations:
          summary: "High CI failure rate"
          description: "CI failure rate is {{ $value | humanizePercentage }}"

# 通知ルーティング
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: pagerduty
      continue: true
    - match:
        severity: warning
      receiver: slack
      
receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
      
  - name: 'slack'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#performance-alerts'
        title: 'Performance Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}{{ end }}'
        
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .GroupLabels.alertname }}'
```

### リアルタイムストリーミング実装
```python
# performance/monitoring/realtime_stream.py
import asyncio
import websockets
import json
from typing import AsyncGenerator, Dict, Any
from datetime import datetime

class RealtimeMetricsStream:
    """WebSocket経由のリアルタイムメトリクスストリーミング"""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.clients = set()
        self.metrics_buffer = []
        
    async def register_client(self, websocket):
        """クライアント登録"""
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
    
    async def broadcast_metrics(self, metrics: Dict[str, Any]):
        """全クライアントへメトリクスブロードキャスト"""
        if self.clients:
            message = json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics
            })
            
            # 並列送信
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
    
    async def stream_benchmark_progress(self, benchmark_name: str) -> AsyncGenerator:
        """ベンチマーク進捗のリアルタイムストリーミング"""
        for iteration in range(1000):
            # ベンチマーク実行
            result = await self.run_benchmark_iteration(benchmark_name, iteration)
            
            # メトリクス生成
            metrics = {
                "benchmark": benchmark_name,
                "iteration": iteration,
                "execution_time_ms": result["time_ms"],
                "memory_mb": result["memory_mb"],
                "status": "running"
            }
            
            # ブロードキャスト
            await self.broadcast_metrics(metrics)
            
            yield metrics
            
            # レート制限
            await asyncio.sleep(0.01)
    
    async def start_server(self):
        """WebSocketサーバー起動"""
        async with websockets.serve(self.register_client, "localhost", self.port):
            print(f"WebSocket server started on ws://localhost:{self.port}")
            await asyncio.Future()  # 永続実行

# CLI統合
class RealtimeMonitoringCLI:
    """リアルタイム監視CLI"""
    
    def __init__(self):
        self.stream = RealtimeMetricsStream()
        
    async def run_with_live_monitoring(self, benchmark_suite):
        """ライブ監視付きベンチマーク実行"""
        # WebSocketサーバー起動
        server_task = asyncio.create_task(self.stream.start_server())
        
        # 監視ダッシュボード起動案内
        print("🚀 Real-time monitoring available at:")
        print("   WebSocket: ws://localhost:8765")
        print("   Prometheus: http://localhost:8000/metrics")
        print("   Grafana: http://localhost:3000")
        
        # ベンチマーク実行with streaming
        async for metrics in self.stream.stream_benchmark_progress("pattern_compilation"):
            # コンソール出力
            print(f"⚡ Iteration {metrics['iteration']}: "
                  f"{metrics['execution_time_ms']:.2f}ms | "
                  f"Memory: {metrics['memory_mb']:.1f}MB")
```

## 📊 成功指標

### 監視要件
- **メトリクス収集頻度**: 1秒間隔でのリアルタイム収集
- **データ保持期間**: 30日間の履歴データ保持
- **ダッシュボード更新**: < 5秒のレイテンシ
- **アラート発火時間**: 異常検知から < 1分

### パフォーマンス要件
- **メトリクス収集オーバーヘッド**: < 3% CPU使用率増加
- **メモリフットプリント**: < 100MB追加メモリ
- **ネットワーク帯域**: < 1Mbps平均使用量
- **ストレージ使用量**: < 1GB/月の時系列データ

### 可用性要件
- **監視システムアップタイム**: 99.9% 以上
- **データ損失防止**: WAL(Write-Ahead Logging)による永続化
- **スケーラビリティ**: 100+ concurrent metricsハンドリング
- **災害復旧**: 15分以内の復旧時間目標(RTO)

## 🔄 Docker Compose統合
```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yaml:/etc/prometheus/alerts.yaml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    networks:
      - monitoring
      
  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./dashboards:/etc/grafana/provisioning/dashboards
      - ./datasources:/etc/grafana/provisioning/datasources
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    ports:
      - "3000:3000"
    networks:
      - monitoring
      
  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/config.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    networks:
      - monitoring
      
  node_exporter:
    image: prom/node-exporter:latest
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:

networks:
  monitoring:
    driver: bridge
```

## 🚫 非目標・制約事項

### 現在のスコープ外
- **分散トレーシング**: メトリクスのみ、トレース未対応
- **ログ集約**: メトリクス専用、ログはELK等別系統
- **APM統合**: Application Performance Monitoring未対応
- **機械学習**: 異常検知は閾値ベース、ML予測なし
- **マルチテナント**: 単一組織専用、マルチテナント未対応

### 制約事項
- **Prometheusメモリ**: 時系列データ量に比例したメモリ使用
- **Grafana依存**: 可視化はGrafanaに限定
- **Pull型収集**: Prometheus pull model制約
- **時系列専用**: イベントデータ・ログは別システム

## 🔗 関連・依存 Issues

### 前提条件
- ✅ Performance Tools MVP (0.3.0) - メトリクス生成基盤
- ✅ CI完全統合 (0.4.0予定) - CI環境での監視統合
- ⏳ DevContainer対応 (0.5.0) - コンテナ環境での監視

### 連携推奨
- **Performance Dashboard** (0.5.0) - Web UIとの統合
- **セキュリティ監視** - セキュリティメトリクス統合
- **コスト最適化** - リソース使用量からのコスト算出

### 後続展開
- **予測的アラート** (0.6.0) - ML基盤の異常予測
- **分散トレーシング** (0.6.0) - Jaeger統合
- **SLO/SLI管理** (0.6.0) - Service Level管理

## 🔄 実装戦略

### Phase 1: 基盤構築 (Week 1-2)
1. Prometheus Exporter実装
2. 基本メトリクス定義・収集開始
3. Docker Compose環境構築
4. 基本的なGrafanaダッシュボード作成

### Phase 2: 統合実装 (Week 2-3)
1. perf_suite/perf_guard統合
2. WebSocketリアルタイムストリーミング
3. AlertManager設定・テスト
4. CI環境での監視統合

### Phase 3: 高度な監視 (Week 3-4)
1. カスタムダッシュボード作成
2. アラートルール最適化
3. 履歴トレンド分析機能
4. パフォーマンステスト・最適化

### Phase 4: 運用準備 (Week 4-5)
1. 監視プレイブック作成
2. アラート対応手順整備
3. バックアップ・復旧手順
4. ドキュメント・トレーニング

## ✅ 完了条件 (Definition of Done)

### 技術要件
- [ ] Prometheus/Grafana/AlertManager起動確認
- [ ] 15+ メトリクス収集・可視化確認
- [ ] WebSocketリアルタイムストリーミング動作
- [ ] アラート発火・通知確認

### 監視要件
- [ ] 1秒間隔でのメトリクス収集確認
- [ ] 30日間データ保持確認
- [ ] ダッシュボード5秒以内更新確認
- [ ] アラート1分以内発火確認

### 統合要件
- [ ] perf_suite統合動作確認
- [ ] CI環境での監視動作確認
- [ ] DevContainer環境対応確認
- [ ] 複数環境での動作検証

### 運用要件
- [ ] 監視プレイブック作成完了
- [ ] アラート対応手順整備完了
- [ ] バックアップ・復旧テスト完了
- [ ] 運用ドキュメント完成

---

**推定工数**: 4-5 weeks  
**担当者**: SRE Team + Performance Engineering  
**レビュワー**: DevOps Team + Development Team  
**作成日**: 2025-09-01  
**最終更新**: 2025-09-01
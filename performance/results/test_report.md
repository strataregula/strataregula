## 📊 Performance Benchmark Report

**Status**: ❌ PENDING
**Project**: strataregula
**Profile**: github-hosted
**Commit**: c37171d

### Performance Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Speedup (p50) | 16.6x | ≥15x | ✅ |
| Speedup (p95) | 15.8x | ≥12x | ✅ |
| Absolute p95 | 0.1ms | ≤35ms | ✅ |

### Detailed Results

| Path | p50 (ms) | p95 (ms) | Hits | Rebuilds |
|------|----------|----------|------|----------|
| Compiled | 0.06 | 0.06 | 3 | 0 |
| Fallback | 1.03 | 1.03 | 3 | 0 |

---
*Generated: 2025-09-01 04:59:37 UTC*
*Headroom: 0.0%*

📚 **Documentation**:
- [Vision](docs/history/performance_acceleration_lecture.md)
- [Guard](docs/GOLDEN_METRICS_GUARD.md)
- [Bench](docs/bench/bench_guard_origin.md)
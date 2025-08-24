"""
Generated configuration module for strataregula.

This module provides O(1) lookup performance for compiled patterns.
Generated at: 2025-08-24T12:07:46.095254
Input files: examples\\sample_traffic.yaml, examples\\sample_prefectures.yaml
Compilation fingerprint: a225eb7e23d28422e0439d983d4b2bf3
"""

from typing import Dict, Any, List
import re

# Direct mapping for simple lookups
DIRECT_MAPPING = {}

# Component mapping for hierarchical lookups  
COMPONENT_MAPPING = {
    "service-hub.kanto": 0.08,
    "service-hub.kansai": 0.08,
    "service-hub.chubu": 0.08,
    "service-hub.kyushu": 0.08,
    "service-hub.hokkaido": 0.08,
    "service-hub.tohoku": 0.08,
    "service-hub.chugoku": 0.08,
    "service-hub.shikoku": 0.08,
    "edge.tokyo.gateway": 0.03,
    "edge.kanagawa.gateway": 0.03,
    "edge.saitama.gateway": 0.03,
    "edge.chiba.gateway": 0.03,
    "edge.ibaraki.gateway": 0.03,
    "edge.tochigi.gateway": 0.03,
    "edge.gunma.gateway": 0.03,
    "edge.osaka.gateway": 0.03,
    "edge.kyoto.gateway": 0.03,
    "edge.hyogo.gateway": 0.03,
    "edge.nara.gateway": 0.03,
    "edge.wakayama.gateway": 0.03,
    "edge.shiga.gateway": 0.03,
    "edge.aichi.gateway": 0.03,
    "edge.shizuoka.gateway": 0.03,
    "edge.gifu.gateway": 0.03,
    "edge.nagano.gateway": 0.03,
    "edge.yamanashi.gateway": 0.03,
    "edge.niigata.gateway": 0.03,
    "edge.toyama.gateway": 0.03,
    "edge.ishikawa.gateway": 0.03,
    "edge.fukui.gateway": 0.03,
    "edge.mie.gateway": 0.03,
    "edge.fukuoka.gateway": 0.03,
    "edge.saga.gateway": 0.03,
    "edge.nagasaki.gateway": 0.03,
    "edge.kumamoto.gateway": 0.03,
    "edge.oita.gateway": 0.03,
    "edge.miyazaki.gateway": 0.03,
    "edge.kagoshima.gateway": 0.03,
    "edge.okinawa.gateway": 0.03,
    "edge.hokkaido.gateway": 0.03,
    "edge.aomori.gateway": 0.03,
    "edge.iwate.gateway": 0.03,
    "edge.miyagi.gateway": 0.03,
    "edge.akita.gateway": 0.03,
    "edge.yamagata.gateway": 0.03,
    "edge.fukushima.gateway": 0.03,
    "edge.tottori.gateway": 0.03,
    "edge.shimane.gateway": 0.03,
    "edge.okayama.gateway": 0.03,
    "edge.hiroshima.gateway": 0.03,
    "edge.yamaguchi.gateway": 0.03,
    "edge.tokushima.gateway": 0.03,
    "edge.kagawa.gateway": 0.03,
    "edge.ehime.gateway": 0.03,
    "edge.kochi.gateway": 0.03,
    "edge.tokyo.api": 0.05,
    "edge.kanagawa.api": 0.05,
    "edge.saitama.api": 0.05,
    "edge.chiba.api": 0.05,
    "edge.ibaraki.api": 0.05,
    "edge.tochigi.api": 0.05,
    "edge.gunma.api": 0.05,
    "edge.osaka.api": 0.05,
    "edge.kyoto.api": 0.05,
    "edge.hyogo.api": 0.05,
    "edge.nara.api": 0.05,
    "edge.wakayama.api": 0.05,
    "edge.shiga.api": 0.05,
    "edge.aichi.api": 0.05,
    "edge.shizuoka.api": 0.05,
    "edge.gifu.api": 0.05,
    "edge.nagano.api": 0.05,
    "edge.yamanashi.api": 0.05,
    "edge.niigata.api": 0.05,
    "edge.toyama.api": 0.05,
    "edge.ishikawa.api": 0.05,
    "edge.fukui.api": 0.05,
    "edge.mie.api": 0.05,
    "edge.fukuoka.api": 0.05,
    "edge.saga.api": 0.05,
    "edge.nagasaki.api": 0.05,
    "edge.kumamoto.api": 0.05,
    "edge.oita.api": 0.05,
    "edge.miyazaki.api": 0.05,
    "edge.kagoshima.api": 0.05,
    "edge.okinawa.api": 0.05,
    "edge.hokkaido.api": 0.05,
    "edge.aomori.api": 0.05,
    "edge.iwate.api": 0.05,
    "edge.miyagi.api": 0.05,
    "edge.akita.api": 0.05,
    "edge.yamagata.api": 0.05,
    "edge.fukushima.api": 0.05,
    "edge.tottori.api": 0.05,
    "edge.shimane.api": 0.05,
    "edge.okayama.api": 0.05,
    "edge.hiroshima.api": 0.05,
    "edge.yamaguchi.api": 0.05,
    "edge.tokushima.api": 0.05,
    "edge.kagawa.api": 0.05,
    "edge.ehime.api": 0.05,
    "edge.kochi.api": 0.05,
    "edge.tokyo.web": 0.02,
    "edge.kanagawa.web": 0.02,
    "edge.saitama.web": 0.02,
    "edge.chiba.web": 0.02,
    "edge.ibaraki.web": 0.02,
    "edge.tochigi.web": 0.02,
    "edge.gunma.web": 0.02,
    "edge.osaka.web": 0.02,
    "edge.kyoto.web": 0.02,
    "edge.hyogo.web": 0.02,
    "edge.nara.web": 0.02,
    "edge.wakayama.web": 0.02,
    "edge.shiga.web": 0.02,
    "edge.aichi.web": 0.02,
    "edge.shizuoka.web": 0.02,
    "edge.gifu.web": 0.02,
    "edge.nagano.web": 0.02,
    "edge.yamanashi.web": 0.02,
    "edge.niigata.web": 0.02,
    "edge.toyama.web": 0.02,
    "edge.ishikawa.web": 0.02,
    "edge.fukui.web": 0.02,
    "edge.mie.web": 0.02,
    "edge.fukuoka.web": 0.02,
    "edge.saga.web": 0.02,
    "edge.nagasaki.web": 0.02,
    "edge.kumamoto.web": 0.02,
    "edge.oita.web": 0.02,
    "edge.miyazaki.web": 0.02,
    "edge.kagoshima.web": 0.02,
    "edge.okinawa.web": 0.02,
    "edge.hokkaido.web": 0.02,
    "edge.aomori.web": 0.02,
    "edge.iwate.web": 0.02,
    "edge.miyagi.web": 0.02,
    "edge.akita.web": 0.02,
    "edge.yamagata.web": 0.02,
    "edge.fukushima.web": 0.02,
    "edge.tottori.web": 0.02,
    "edge.shimane.web": 0.02,
    "edge.okayama.web": 0.02,
    "edge.hiroshima.web": 0.02,
    "edge.yamaguchi.web": 0.02,
    "edge.tokushima.web": 0.02,
    "edge.kagawa.web": 0.02,
    "edge.ehime.web": 0.02,
    "edge.kochi.web": 0.02,
    "service-hub.kanto.processing": 0.12,
    "service-hub.kansai.processing": 0.12,
    "service-hub.chubu.processing": 0.12,
    "service-hub.kyushu.processing": 0.12,
    "service-hub.hokkaido.processing": 0.12,
    "service-hub.tohoku.processing": 0.12,
    "service-hub.chugoku.processing": 0.12,
    "service-hub.shikoku.processing": 0.12,
    "corebrain.kanto.analytics": 0.15,
    "corebrain.kansai.analytics": 0.15,
    "corebrain.chubu.analytics": 0.15,
    "corebrain.kyushu.analytics": 0.15,
    "corebrain.hokkaido.analytics": 0.15,
    "corebrain.tohoku.analytics": 0.15,
    "corebrain.chugoku.analytics": 0.15,
    "corebrain.shikoku.analytics": 0.15,
    "corebrain.kanto.storage": 0.2,
    "corebrain.kansai.storage": 0.2,
    "corebrain.chubu.storage": 0.2,
    "corebrain.kyushu.storage": 0.2,
    "corebrain.hokkaido.storage": 0.2,
    "corebrain.tohoku.storage": 0.2,
    "corebrain.chugoku.storage": 0.2,
    "corebrain.shikoku.storage": 0.2,
    "global.auth": 0.01,
    "global.metrics": 0.005,
    "global.health": 0.001,
    "monitor.*.*.critical": 0.25,
    "backup.*.*.daily": 1.5,
    "cache.*.*.hot": 0.002
}

# Metadata and provenance
METADATA = {
    "expansion_rules_count": 6,
    "total_patterns": 179,
    "cache_size": 13,
    "hierarchy": {"regions": 8, "prefectures": 47, "cities": 0, "services": 9, "roles": 12},
    "provenance": {"timestamp": "2025-08-24T12:07:46.095254", "version": "0.1.0", "input_files": ["examples\\sample_traffic.yaml", "examples\\sample_prefectures.yaml"], "execution_fingerprint": "a225eb7e23d28422e0439d983d4b2bf3", "performance_stats": {"compilation_time_seconds": 0.007383823394775391, "peak_memory_mb": 44.15625, "patterns_processed": 13, "cache_size": 13}}
}

# Performance-optimized lookup functions
def get_service_time(service_name: str, default: float = 0.0) -> float:
    """Get service time with O(1) lookup."""
    # Try direct mapping first
    if service_name in DIRECT_MAPPING:
        return DIRECT_MAPPING[service_name]
    
    # Try component mapping
    if service_name in COMPONENT_MAPPING:
        return COMPONENT_MAPPING[service_name]
    
    return default

def get_service_info(service_name: str) -> Dict[str, Any]:
    """Get comprehensive service information."""
    service_time = get_service_time(service_name)
    
    return {
        "service_name": service_name,
        "service_time": service_time,
        "found_in": "direct" if service_name in DIRECT_MAPPING else "component" if service_name in COMPONENT_MAPPING else "default",
        "metadata": METADATA
    }

def list_all_services() -> List[str]:
    """List all available service names."""
    return sorted(set(list(DIRECT_MAPPING.keys()) + list(COMPONENT_MAPPING.keys())))

def get_services_by_pattern(pattern: str) -> Dict[str, float]:
    """Get services matching a pattern."""
    regex_pattern = pattern.replace('.', r'\.').replace('*', r'[^.]*')
    compiled_regex = re.compile(f"^{regex_pattern}$")
    
    result = {}
    
    # Search direct mapping
    for service, time_val in DIRECT_MAPPING.items():
        if compiled_regex.match(service):
            result[service] = time_val
    
    # Search component mapping
    for service, time_val in COMPONENT_MAPPING.items():
        if compiled_regex.match(service):
            result[service] = time_val
    
    return result

# Regional and hierarchical lookup functions

def get_services_by_region(region: str) -> Dict[str, float]:
    """Get all services in a specific region."""
    result = {}
    region_prefectures = {'kanto': ['tokyo', 'kanagawa', 'saitama', 'chiba', 'ibaraki', 'tochigi', 'gunma'], 'kansai': ['osaka', 'kyoto', 'hyogo', 'nara', 'wakayama', 'shiga'], 'chubu': ['aichi', 'shizuoka', 'gifu', 'nagano', 'yamanashi', 'niigata', 'toyama', 'ishikawa', 'fukui', 'mie'], 'kyushu': ['fukuoka', 'saga', 'nagasaki', 'kumamoto', 'oita', 'miyazaki', 'kagoshima', 'okinawa'], 'hokkaido': ['hokkaido'], 'tohoku': ['aomori', 'iwate', 'miyagi', 'akita', 'yamagata', 'fukushima'], 'chugoku': ['tottori', 'shimane', 'okayama', 'hiroshima', 'yamaguchi'], 'shikoku': ['tokushima', 'kagawa', 'ehime', 'kochi']}
    
    for service, time_val in COMPONENT_MAPPING.items():
        parts = service.split('.')
        if len(parts) >= 2 and parts[1] in region_prefectures.get(region, []):
            result[service] = time_val
    
    return result

def get_services_by_prefecture(prefecture: str) -> Dict[str, float]:
    """Get all services in a specific prefecture."""
    result = {}
    
    for service, time_val in COMPONENT_MAPPING.items():
        if f'.{prefecture}.' in service:
            result[service] = time_val
    
    return result


# Statistics and introspection
def get_compilation_stats() -> Dict[str, Any]:
    """Get compilation statistics."""
    return {
        "total_services": len(DIRECT_MAPPING) + len(COMPONENT_MAPPING),
        "direct_mappings": len(DIRECT_MAPPING),
        "component_mappings": len(COMPONENT_MAPPING),
        "compilation_time": METADATA.get("performance_stats", {}).get("compilation_time_seconds", 0),
        "memory_usage_mb": METADATA.get("performance_stats", {}).get("peak_memory_mb", 0),
        "input_files": METADATA.get("provenance", {}).get("input_files", []),
        "fingerprint": METADATA.get("provenance", {}).get("execution_fingerprint", "")
    }

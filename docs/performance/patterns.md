# Performance Optimization Patterns

## Overview
Proven performance patterns and anti-patterns for Strataregula development, covering algorithmic optimizations, caching strategies, and resource management.

## Algorithmic Optimization Patterns

### 1. Complexity Reduction Patterns

#### Replace O(n²) with O(n log n) or O(n)

```python
# ❌ Quadratic complexity - nested loops
def slow_duplicate_detection(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

# ✅ Linear complexity - hash set
def fast_duplicate_detection(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)

# 📊 Performance improvement: O(n²) → O(n)
# For 10,000 items: ~50,000,000 operations → ~10,000 operations (5000x speedup)
```

#### Optimize Search Operations

```python
# ❌ Linear search in lists
class SlowPatternMatcher:
    def __init__(self, patterns):
        self.patterns = patterns  # List
    
    def match(self, target):
        for pattern in self.patterns:  # O(n) search
            if fnmatch.fnmatch(target, pattern):
                return True
        return False

# ✅ Hierarchical matching with early termination
class FastPatternMatcher:
    def __init__(self, patterns):
        # Pre-process patterns by type for optimal matching
        self.exact_patterns = set()
        self.prefix_patterns = {}
        self.complex_patterns = []
        
        for pattern in patterns:
            if '*' not in pattern and '?' not in pattern:
                self.exact_patterns.add(pattern)  # O(1) lookup
            elif pattern.endswith('*') and '*' not in pattern[:-1]:
                prefix = pattern[:-1]
                self.prefix_patterns[prefix] = True
            else:
                self.complex_patterns.append(pattern)  # Fallback to fnmatch
    
    def match(self, target):
        # 1. Exact match (fastest)
        if target in self.exact_patterns:  # O(1)
            return True
        
        # 2. Prefix match (fast)
        for prefix in self.prefix_patterns:  # Usually small set
            if target.startswith(prefix):
                return True
        
        # 3. Complex pattern match (slower, but limited set)
        for pattern in self.complex_patterns:
            if fnmatch.fnmatch(target, pattern):
                return True
        
        return False

# 📊 Performance improvement: O(n) → O(1) average case
# 1000 patterns, 10000 queries: ~10M operations → ~10K operations (1000x speedup)
```

### 2. Data Structure Optimization Patterns

#### Choose Appropriate Collections

```python
# Pattern: Match data structure to access pattern
class OptimizedConfigLoader:
    """Optimized configuration loading with appropriate data structures"""
    
    def __init__(self):
        # Different structures for different access patterns
        self.config_by_key = {}           # O(1) key lookup
        self.config_by_prefix = {}        # O(1) prefix lookup
        self.ordered_configs = []         # O(1) index access
        self.config_search_index = {}     # O(1) search by property
    
    def load_config_optimized(self, config_data):
        """Load configuration with optimal data structure population"""
        
        for config_item in config_data:
            key = config_item['key']
            
            # Populate multiple indexes for different access patterns
            self.config_by_key[key] = config_item                    # Direct lookup
            
            # Prefix index for hierarchical lookups
            parts = key.split('.')
            for i in range(1, len(parts) + 1):
                prefix = '.'.join(parts[:i])
                if prefix not in self.config_by_prefix:
                    self.config_by_prefix[prefix] = []
                self.config_by_prefix[prefix].append(config_item)
            
            # Ordered index for iteration
            self.ordered_configs.append(config_item)
            
            # Search index for property-based queries
            for prop, value in config_item.items():
                if prop not in self.config_search_index:
                    self.config_search_index[prop] = {}
                if value not in self.config_search_index[prop]:
                    self.config_search_index[prop][value] = []
                self.config_search_index[prop][value].append(config_item)
    
    def get_config(self, key):
        """O(1) config lookup"""
        return self.config_by_key.get(key)
    
    def get_configs_by_prefix(self, prefix):
        """O(1) prefix-based lookup"""
        return self.config_by_prefix.get(prefix, [])
    
    def search_configs_by_property(self, property_name, value):
        """O(1) property-based search"""
        return self.config_search_index.get(property_name, {}).get(value, [])
```

#### Memory-Efficient Collections

```python
# Pattern: Use generators and iterators for large datasets
class MemoryEfficientProcessor:
    """Memory-efficient processing patterns"""
    
    def process_large_stream(self, data_source):
        """Process large datasets without loading everything into memory"""
        
        # ❌ Memory-intensive approach
        # all_data = list(data_source)  # Loads everything
        # return [self.process_item(item) for item in all_data]
        
        # ✅ Memory-efficient approach  
        return (self.process_item(item) for item in data_source)
    
    def batch_process_stream(self, data_source, batch_size=1000):
        """Process in batches for balanced memory/performance"""
        
        batch = []
        for item in data_source:
            batch.append(item)
            
            if len(batch) >= batch_size:
                # Process complete batch
                yield from self.process_batch(batch)
                batch.clear()  # Free memory
        
        # Process remaining items
        if batch:
            yield from self.process_batch(batch)
    
    def adaptive_batch_processing(self, data_source, target_memory_mb=50):
        """Adaptive batch sizing based on memory usage"""
        
        batch = []
        current_memory_mb = 0
        
        for item in data_source:
            item_size_mb = sys.getsizeof(item) / (1024 * 1024)
            
            if current_memory_mb + item_size_mb > target_memory_mb and batch:
                # Process current batch
                yield from self.process_batch(batch)
                batch.clear()
                current_memory_mb = 0
            
            batch.append(item)
            current_memory_mb += item_size_mb
        
        if batch:
            yield from self.process_batch(batch)
```

## Caching Optimization Patterns

### 1. Multi-Level Caching

```python
# Pattern: Hierarchical caching with different eviction strategies
class MultiLevelCache:
    """Multi-level caching system for performance optimization"""
    
    def __init__(self):
        # L1: Small, fast cache for immediate lookups
        self.l1_cache = {}  # Direct dict for fastest access
        self.l1_max_size = 100
        
        # L2: Larger cache with LRU eviction
        from functools import lru_cache
        self.l2_cache = {}
        self.l2_max_size = 1000
        self.l2_access_order = []
        
        # L3: Persistent cache for expensive computations
        self.l3_cache_file = Path("cache/l3_cache.json")
        self.l3_cache = self._load_l3_cache()
    
    def get(self, key, factory_func):
        """Get value with multi-level cache checking"""
        
        # L1 Cache check (fastest)
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # L2 Cache check
        if key in self.l2_cache:
            value = self.l2_cache[key]
            # Promote to L1
            self._promote_to_l1(key, value)
            return value
        
        # L3 Cache check
        if key in self.l3_cache:
            value = self.l3_cache[key]
            # Promote to L2
            self._promote_to_l2(key, value)
            return value
        
        # Cache miss - compute value
        value = factory_func()
        
        # Store in all levels
        self._store_in_all_levels(key, value)
        
        return value
    
    def _promote_to_l1(self, key, value):
        """Promote frequently accessed items to L1"""
        if len(self.l1_cache) >= self.l1_max_size:
            # Evict oldest from L1
            oldest_key = next(iter(self.l1_cache))
            self.l1_cache.pop(oldest_key)
        
        self.l1_cache[key] = value
    
    def _promote_to_l2(self, key, value):
        """Promote to L2 with LRU management"""
        if len(self.l2_cache) >= self.l2_max_size:
            # LRU eviction
            lru_key = self.l2_access_order.pop(0)
            self.l2_cache.pop(lru_key, None)
        
        self.l2_cache[key] = value
        self.l2_access_order.append(key)
    
    def _store_in_all_levels(self, key, value):
        """Store new value in appropriate cache levels"""
        
        # Store in L1 (most recent)
        self._promote_to_l1(key, value)
        
        # Store in L3 if expensive to compute
        if self._is_expensive_computation(value):
            self.l3_cache[key] = value
            self._save_l3_cache()
```

### 2. Context-Aware Caching

```python
# Pattern: Cache based on usage context and patterns
class ContextAwareCache:
    """Cache that adapts to usage patterns"""
    
    def __init__(self):
        self.access_patterns = {}  # Track access frequency
        self.cache_tiers = {
            'hot': {},      # Frequently accessed (keep in memory)
            'warm': {},     # Occasionally accessed (LRU eviction)
            'cold': {}      # Rarely accessed (limited storage)
        }
        self.access_counts = {}
    
    def get(self, key, factory_func):
        """Context-aware cache retrieval"""
        
        # Update access pattern
        self.access_counts[key] = self.access_counts.get(key, 0) + 1
        access_count = self.access_counts[key]
        
        # Determine cache tier based on access pattern
        if access_count > 100:
            tier = 'hot'
        elif access_count > 10:
            tier = 'warm'
        else:
            tier = 'cold'
        
        # Check appropriate tier first
        if key in self.cache_tiers[tier]:
            return self.cache_tiers[tier][key]
        
        # Check other tiers
        for tier_name, cache in self.cache_tiers.items():
            if key in cache:
                value = cache.pop(key)  # Remove from current tier
                self._store_in_tier(key, value, tier)  # Store in appropriate tier
                return value
        
        # Cache miss - compute and store
        value = factory_func()
        self._store_in_tier(key, value, tier)
        
        return value
    
    def _store_in_tier(self, key, value, tier):
        """Store value in appropriate cache tier"""
        
        tier_limits = {'hot': 50, 'warm': 200, 'cold': 500}
        
        if len(self.cache_tiers[tier]) >= tier_limits[tier]:
            # Tier-specific eviction strategy
            if tier == 'hot':
                # Demote least accessed to warm
                lru_key = min(self.cache_tiers[tier].keys(), 
                            key=lambda k: self.access_counts.get(k, 0))
                value_to_demote = self.cache_tiers[tier].pop(lru_key)
                self._store_in_tier(lru_key, value_to_demote, 'warm')
            
            elif tier == 'warm':
                # LRU eviction to cold
                oldest_key = next(iter(self.cache_tiers[tier]))
                old_value = self.cache_tiers[tier].pop(oldest_key)
                self._store_in_tier(oldest_key, old_value, 'cold')
            
            else:  # cold tier
                # Remove oldest entry
                oldest_key = next(iter(self.cache_tiers[tier]))
                self.cache_tiers[tier].pop(oldest_key)
        
        self.cache_tiers[tier][key] = value
```

### 3. Time-To-Live (TTL) Caching

```python
# Pattern: Cache with automatic expiration for time-sensitive data
import time
from typing import Any, Callable, Optional

class TTLCache:
    """Time-based cache with automatic expiration"""
    
    def __init__(self, default_ttl_seconds: int = 300):
        self.cache = {}  # key -> (value, expiry_time)
        self.default_ttl = default_ttl_seconds
        self.access_stats = {'hits': 0, 'misses': 0, 'expired': 0}
    
    def get(self, key: str, factory_func: Callable, ttl_seconds: Optional[int] = None) -> Any:
        """Get cached value or compute with TTL"""
        
        current_time = time.time()
        ttl = ttl_seconds or self.default_ttl
        
        if key in self.cache:
            value, expiry_time = self.cache[key]
            
            if current_time < expiry_time:
                # Cache hit
                self.access_stats['hits'] += 1
                return value
            else:
                # Expired entry
                del self.cache[key]
                self.access_stats['expired'] += 1
        
        # Cache miss or expired - compute new value
        self.access_stats['misses'] += 1
        value = factory_func()
        
        # Store with expiration time
        expiry_time = current_time + ttl
        self.cache[key] = (value, expiry_time)
        
        return value
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self.cache.items()
            if current_time >= expiry_time
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.access_stats['hits'] + self.access_stats['misses']
        hit_rate = (self.access_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hit_rate_pct': hit_rate,
            'cache_size': len(self.cache),
            'total_requests': total_requests,
            **self.access_stats
        }

# Usage for pattern compilation caching
pattern_cache = TTLCache(default_ttl_seconds=600)  # 10 minute cache

def get_compiled_pattern(pattern_text):
    """Get compiled pattern with TTL caching"""
    return pattern_cache.get(
        pattern_text,
        lambda: compile_pattern_expensive(pattern_text),
        ttl_seconds=1800  # 30 minutes for complex patterns
    )
```

## Resource Management Patterns

### 1. Object Pooling Pattern

```python
# Pattern: Reuse expensive objects to reduce GC pressure
from typing import TypeVar, Generic, Queue
import threading

T = TypeVar('T')

class ObjectPool(Generic[T]):
    """Thread-safe object pool for expensive resources"""
    
    def __init__(self, factory: Callable[[], T], max_size: int = 20, min_size: int = 5):
        self.factory = factory
        self.max_size = max_size
        self.min_size = min_size
        
        # Thread-safe queue for pooled objects
        self.pool = Queue(maxsize=max_size)
        self.lock = threading.Lock()
        
        # Pre-populate with minimum objects
        for _ in range(min_size):
            self.pool.put(self.factory())
        
        # Statistics
        self.stats = {
            'created': min_size,
            'reused': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
    
    def acquire(self) -> T:
        """Get object from pool or create new one"""
        try:
            # Try to get from pool (non-blocking)
            obj = self.pool.get_nowait()
            self.stats['pool_hits'] += 1
            self.stats['reused'] += 1
            return obj
            
        except Queue.Empty:
            # Pool empty - create new object
            self.stats['pool_misses'] += 1
            with self.lock:
                self.stats['created'] += 1
            return self.factory()
    
    def release(self, obj: T) -> bool:
        """Return object to pool for reuse"""
        try:
            # Reset object state if possible
            if hasattr(obj, 'reset'):
                obj.reset()
            
            # Return to pool (non-blocking)
            self.pool.put_nowait(obj)
            return True
            
        except Queue.Full:
            # Pool full - discard object
            return False
    
    def get_efficiency_stats(self) -> Dict[str, Any]:
        """Get pool efficiency statistics"""
        total_acquisitions = self.stats['pool_hits'] + self.stats['pool_misses']
        reuse_rate = (self.stats['reused'] / self.stats['created'] * 100) if self.stats['created'] > 0 else 0
        
        return {
            'reuse_rate_pct': reuse_rate,
            'pool_hit_rate_pct': (self.stats['pool_hits'] / total_acquisitions * 100) if total_acquisitions > 0 else 0,
            'current_pool_size': self.pool.qsize(),
            'total_objects_created': self.stats['created'],
            'total_reuses': self.stats['reused']
        }

# Usage for pattern matcher objects
class PatternMatcher:
    def __init__(self):
        self.compiled_patterns = {}
    
    def reset(self):
        """Reset for pool reuse"""
        self.compiled_patterns.clear()
    
    def compile_and_match(self, patterns, target):
        # Expensive pattern compilation and matching
        return self._match_with_compiled_patterns(patterns, target)

# Create pool for pattern matchers
pattern_matcher_pool = ObjectPool(PatternMatcher, max_size=10, min_size=3)

def process_with_pooled_matcher(patterns, targets):
    """Use pooled pattern matcher for processing"""
    matcher = pattern_matcher_pool.acquire()
    try:
        results = []
        for target in targets:
            results.append(matcher.compile_and_match(patterns, target))
        return results
    finally:
        pattern_matcher_pool.release(matcher)
```

### 2. Lazy Initialization Pattern

```python
# Pattern: Defer expensive operations until needed
class LazyResourceManager:
    """Lazy initialization for expensive resources"""
    
    def __init__(self):
        self._compiled_patterns = None
        self._search_index = None
        self._config_cache = None
        
        # Track what has been initialized
        self._initialized = set()
    
    @property
    def compiled_patterns(self):
        """Lazy initialization of compiled patterns"""
        if self._compiled_patterns is None:
            print("Initializing compiled patterns...")  # Only happens once
            self._compiled_patterns = self._compile_all_patterns()
            self._initialized.add('compiled_patterns')
        return self._compiled_patterns
    
    @property
    def search_index(self):
        """Lazy initialization of search index"""
        if self._search_index is None:
            print("Building search index...")  # Only happens once
            self._search_index = self._build_search_index()
            self._initialized.add('search_index')
        return self._search_index
    
    @property
    def config_cache(self):
        """Lazy initialization of configuration cache"""
        if self._config_cache is None:
            print("Loading configuration cache...")  # Only happens once
            self._config_cache = self._load_config_cache()
            self._initialized.add('config_cache')
        return self._config_cache
    
    def get_initialization_stats(self) -> Dict[str, Any]:
        """Get statistics about what has been initialized"""
        available_resources = ['compiled_patterns', 'search_index', 'config_cache']
        
        return {
            'total_resources': len(available_resources),
            'initialized_resources': len(self._initialized),
            'initialization_rate_pct': (len(self._initialized) / len(available_resources)) * 100,
            'initialized_list': list(self._initialized),
            'memory_saved': self._estimate_memory_savings()
        }
    
    def _estimate_memory_savings(self) -> str:
        """Estimate memory saved by lazy initialization"""
        total_resources = 3
        initialized_resources = len(self._initialized)
        
        estimated_savings_mb = (total_resources - initialized_resources) * 10  # Rough estimate
        return f"~{estimated_savings_mb}MB"
```

### 3. Asynchronous Preloading Pattern

```python
# Pattern: Preload resources asynchronously while processing
import asyncio
import concurrent.futures
from typing import Awaitable

class AsyncPreloader:
    """Asynchronous resource preloading for improved user experience"""
    
    def __init__(self, max_workers: int = 4):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.preload_cache = {}
        self.preload_futures = {}
    
    def preload_resource(self, key: str, factory_func: Callable) -> None:
        """Start preloading resource asynchronously"""
        if key not in self.preload_futures:
            future = self.executor.submit(factory_func)
            self.preload_futures[key] = future
    
    def get_resource(self, key: str, factory_func: Callable) -> Any:
        """Get resource, using preloaded version if available"""
        
        # Check if already cached
        if key in self.preload_cache:
            return self.preload_cache[key]
        
        # Check if preloading in progress
        if key in self.preload_futures:
            future = self.preload_futures[key]
            
            if future.done():
                # Preloading completed
                try:
                    value = future.result()
                    self.preload_cache[key] = value
                    del self.preload_futures[key]
                    return value
                except Exception as e:
                    # Preloading failed - fall back to synchronous
                    del self.preload_futures[key]
                    return factory_func()
            else:
                # Still preloading - wait for completion
                return future.result(timeout=30)  # 30 second timeout
        
        # No preloading - compute synchronously
        return factory_func()
    
    def preload_common_resources(self):
        """Preload commonly used resources"""
        
        # Preload based on usage patterns
        common_resources = {
            'default_patterns': lambda: load_default_patterns(),
            'config_schema': lambda: load_configuration_schema(),
            'index_templates': lambda: load_index_templates()
        }
        
        for key, factory in common_resources.items():
            self.preload_resource(key, factory)
    
    def get_preload_stats(self) -> Dict[str, Any]:
        """Get preloading performance statistics"""
        
        completed_preloads = sum(1 for future in self.preload_futures.values() if future.done())
        failed_preloads = sum(1 for future in self.preload_futures.values() 
                            if future.done() and future.exception() is not None)
        
        return {
            'cached_resources': len(self.preload_cache),
            'pending_preloads': len(self.preload_futures) - completed_preloads,
            'completed_preloads': completed_preloads,
            'failed_preloads': failed_preloads,
            'preload_success_rate': ((completed_preloads - failed_preloads) / max(1, completed_preloads)) * 100
        }

# Usage in strataregula initialization
async def initialize_with_preloading():
    """Initialize system with async preloading"""
    
    preloader = AsyncPreloader()
    
    # Start preloading common resources
    preloader.preload_common_resources()
    
    # Continue with other initialization while preloading happens
    initialize_core_components()
    
    # Resources will be ready when needed
    patterns = preloader.get_resource('default_patterns', load_default_patterns)
    config = preloader.get_resource('config_schema', load_configuration_schema)
    
    return patterns, config
```

## I/O Optimization Patterns

### 1. Batch I/O Operations

```python
# Pattern: Minimize system calls through batching
class BatchFileProcessor:
    """Optimized file processing with batching"""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.file_cache = {}
    
    def process_files_optimized(self, file_paths: List[str]) -> Dict[str, Any]:
        """Process multiple files with optimized I/O"""
        
        results = {}
        
        # Process files in batches to optimize I/O
        for i in range(0, len(file_paths), self.batch_size):
            batch = file_paths[i:i + self.batch_size]
            
            # Read all files in batch concurrently
            batch_contents = self._read_files_batch(batch)
            
            # Process batch contents
            for file_path, content in batch_contents.items():
                if content is not None:
                    results[file_path] = self._process_single_file_content(content)
        
        return results
    
    def _read_files_batch(self, file_paths: List[str]) -> Dict[str, Optional[str]]:
        """Read multiple files efficiently"""
        
        # Use concurrent file reading for I/O bound operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.batch_size) as executor:
            # Submit all read operations
            future_to_file = {
                executor.submit(self._read_single_file, file_path): file_path
                for file_path in file_paths
            }
            
            # Collect results
            batch_contents = {}
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    content = future.result()
                    batch_contents[file_path] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    batch_contents[file_path] = None
            
            return batch_contents
    
    def _read_single_file(self, file_path: str) -> Optional[str]:
        """Read single file with caching"""
        try:
            # Simple file-based caching
            file_stat = Path(file_path).stat()
            cache_key = f"{file_path}_{file_stat.st_mtime}"
            
            if cache_key in self.file_cache:
                return self.file_cache[cache_key]
            
            # Read file
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
            
            # Cache content (with size limit)
            if len(content) < 1024 * 1024:  # Cache files smaller than 1MB
                self.file_cache[cache_key] = content
            
            return content
            
        except Exception as e:
            return None
```

### 2. Memory-Mapped File Processing

```python
# Pattern: Use memory mapping for large file processing
import mmap
from contextlib import contextmanager

class MemoryMappedProcessor:
    """Efficient large file processing using memory mapping"""
    
    @contextmanager
    def open_mapped_file(self, file_path: str):
        """Context manager for memory-mapped file access"""
        
        file_obj = None
        mapped_file = None
        
        try:
            file_obj = open(file_path, 'rb')
            mapped_file = mmap.mmap(file_obj.fileno(), 0, access=mmap.ACCESS_READ)
            yield mapped_file
            
        finally:
            if mapped_file:
                mapped_file.close()
            if file_obj:
                file_obj.close()
    
    def search_large_file(self, file_path: str, search_patterns: List[bytes]) -> Dict[bytes, List[int]]:
        """Search for patterns in large file without loading into memory"""
        
        results = {pattern: [] for pattern in search_patterns}
        
        with self.open_mapped_file(file_path) as mapped_file:
            # Search each pattern efficiently
            for pattern in search_patterns:
                positions = []
                start_pos = 0
                
                while True:
                    pos = mapped_file.find(pattern, start_pos)
                    if pos == -1:
                        break
                    
                    positions.append(pos)
                    start_pos = pos + 1
                
                results[pattern] = positions
        
        return results
    
    def process_large_file_in_chunks(self, file_path: str, chunk_size: int = 8192) -> Iterator[bytes]:
        """Process large file in memory-efficient chunks"""
        
        with self.open_mapped_file(file_path) as mapped_file:
            file_size = len(mapped_file)
            
            for offset in range(0, file_size, chunk_size):
                end_offset = min(offset + chunk_size, file_size)
                chunk = mapped_file[offset:end_offset]
                yield chunk

# Usage for secret scanning optimization
def optimized_secret_scanning(file_paths: List[str], secret_patterns: List[str]) -> Dict[str, Any]:
    """Optimized secret scanning using memory mapping"""
    
    processor = MemoryMappedProcessor()
    results = {}
    
    # Convert patterns to bytes for efficient searching
    byte_patterns = [pattern.encode('utf-8') for pattern in secret_patterns]
    
    for file_path in file_paths:
        try:
            file_results = processor.search_large_file(file_path, byte_patterns)
            
            # Convert back to string patterns for result reporting
            string_results = {}
            for byte_pattern, positions in file_results.items():
                pattern_str = byte_pattern.decode('utf-8')
                if positions:  # Only include files with matches
                    string_results[pattern_str] = positions
            
            if string_results:
                results[file_path] = string_results
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return results
```

## PowerShell Performance Patterns

### 1. Pipeline Optimization

```powershell
# Pattern: Optimize PowerShell pipelines for performance
function Optimize-PowerShellPipeline {
    param([string[]]$InputData)
    
    # ❌ Inefficient: Multiple pipeline passes
    $step1 = $InputData | Where-Object { $_.Length -gt 5 }
    $step2 = $step1 | ForEach-Object { $_.ToUpper() }
    $step3 = $step2 | Sort-Object
    
    # ✅ Efficient: Single pipeline pass
    $optimized = $InputData | 
        Where-Object { $_.Length -gt 5 } |
        ForEach-Object { $_.ToUpper() } |
        Sort-Object
    
    return $optimized
}

# Pattern: Use calculated properties for complex transformations
function Use-CalculatedProperties {
    param($InputObjects)
    
    # ✅ Efficient: Single pass with calculated properties
    return $InputObjects | Select-Object Name, 
        @{Name='UpperName'; Expression={$_.Name.ToUpper()}},
        @{Name='NameLength'; Expression={$_.Name.Length}},
        @{Name='ProcessedDate'; Expression={Get-Date}}
}
```

### 2. String Processing Optimization

```powershell
# Pattern: Efficient string operations in PowerShell
function Optimize-StringProcessing {
    param([string[]]$Strings)
    
    # ❌ Slow: String concatenation in loop
    $result = ""
    foreach ($str in $Strings) {
        $result += $str + "`n"  # Creates new string each time
    }
    
    # ✅ Fast: Join operation
    $optimized = $Strings -join "`n"
    
    # ✅ For complex string building: StringBuilder
    $sb = [System.Text.StringBuilder]::new()
    foreach ($str in $Strings) {
        [void]$sb.AppendLine($str)
    }
    $stringBuilderResult = $sb.ToString()
    
    return @{
        JoinResult = $optimized
        StringBuilderResult = $stringBuilderResult
        Performance = "Join: fastest for simple concatenation, StringBuilder: best for complex building"
    }
}

# Pattern: Regex optimization for repeated matching
function Optimize-RegexOperations {
    param([string[]]$Content, [string[]]$Patterns)
    
    # ✅ Pre-compile regex patterns for reuse
    $compiledPatterns = foreach ($pattern in $Patterns) {
        @{
            Pattern = $pattern
            Regex = [regex]::new($pattern, [System.Text.RegularExpressions.RegexOptions]::Compiled)
        }
    }
    
    # Process content with compiled patterns
    $matches = foreach ($line in $Content) {
        foreach ($patternInfo in $compiledPatterns) {
            $regexMatches = $patternInfo.Regex.Matches($line)
            if ($regexMatches.Count -gt 0) {
                foreach ($match in $regexMatches) {
                    @{
                        Content = $line
                        Pattern = $patternInfo.Pattern
                        Match = $match.Value
                        Index = $match.Index
                    }
                }
            }
        }
    }
    
    return $matches
}
```

### 3. Collection Optimization

```powershell
# Pattern: Use appropriate collections for performance
function Use-OptimizedCollections {
    param([int]$Size = 10000)
    
    # ❌ Slow: Array concatenation
    $slowArray = @()
    for ($i = 0; $i -lt $Size; $i++) {
        $slowArray += $i  # O(n) operation each time
    }
    
    # ✅ Fast: ArrayList
    $fastList = [System.Collections.ArrayList]::new()
    for ($i = 0; $i -lt $Size; $i++) {
        [void]$fastList.Add($i)  # O(1) amortized
    }
    
    # ✅ Fastest: Generic List
    $genericList = [System.Collections.Generic.List[int]]::new()
    for ($i = 0; $i -lt $Size; $i++) {
        $genericList.Add($i)  # O(1) amortized, type-safe
    }
    
    # ✅ For lookups: HashSet
    $hashSet = [System.Collections.Generic.HashSet[int]]::new()
    for ($i = 0; $i -lt $Size; $i++) {
        [void]$hashSet.Add($i)  # O(1) operations, fast lookups
    }
    
    return @{
        ArrayCount = $slowArray.Count
        ArrayListCount = $fastList.Count
        GenericListCount = $genericList.Count
        HashSetCount = $hashSet.Count
        Recommendation = "Use Generic collections for best performance"
    }
}
```

## Anti-Patterns to Avoid

### 1. Premature Optimization Anti-Pattern

```python
# ❌ Anti-pattern: Over-optimizing before measuring
class PrematureOptimization:
    def __init__(self):
        # Complex optimization before knowing if it's needed
        self.ultra_optimized_cache = UltraComplexCache()
        self.micro_optimized_algorithms = MicroOptimizedProcessor()
        self.premature_concurrency = ThreadPoolWithComplexLogic()
    
    def process(self, data):
        # Overly complex solution for simple problem
        return self.ultra_optimized_cache.get_or_compute(
            data, 
            lambda: self.micro_optimized_algorithms.process_with_concurrency(
                data, 
                self.premature_concurrency
            )
        )

# ✅ Correct pattern: Measure first, optimize proven bottlenecks
class MeasuredOptimization:
    def __init__(self):
        self.simple_cache = {}  # Start simple
    
    def process(self, data):
        # Simple, working solution first
        if data in self.simple_cache:
            return self.simple_cache[data]
        
        result = self._simple_process(data)
        self.simple_cache[data] = result
        return result
    
    def optimize_after_profiling(self, bottleneck_function):
        """Only optimize after identifying bottlenecks"""
        # Profile shows this function is slow -> optimize it
        return self._optimized_version_of_bottleneck(bottleneck_function)
```

### 2. Memory Leak Anti-Patterns

```python
# ❌ Anti-pattern: Unbounded caches
class MemoryLeakingCache:
    def __init__(self):
        self.cache = {}  # Never evicts entries
    
    def get(self, key, factory_func):
        if key not in self.cache:
            self.cache[key] = factory_func()  # Accumulates forever
        return self.cache[key]

# ✅ Correct pattern: Bounded caches with eviction
class BoundedCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.access_order = []
        self.max_size = max_size
    
    def get(self, key, factory_func):
        if key in self.cache:
            # Move to end (most recent)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        
        # Evict if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = self.access_order.pop(0)
            del self.cache[oldest_key]
        
        # Compute and cache
        value = factory_func()
        self.cache[key] = value
        self.access_order.append(key)
        
        return value
```

### 3. Inefficient Loop Anti-Patterns

```python
# ❌ Anti-pattern: Inefficient nested loops
def inefficient_data_processing(data):
    results = []
    for item in data:
        # Expensive operation in inner loop
        for i in range(len(data)):  # Unnecessary nesting
            if expensive_condition(item, data[i]):
                results.append(transform(item, data[i]))
    return results

# ✅ Correct pattern: Optimize loop structure
def efficient_data_processing(data):
    # Pre-compute expensive operations outside loop
    transformed_data = [precompute(item) for item in data]
    
    # Use appropriate data structures
    data_index = {get_key(item): item for item in transformed_data}
    
    # Efficient processing
    results = []
    for item in transformed_data:
        key = get_lookup_key(item)
        if key in data_index:  # O(1) lookup
            results.append(fast_transform(item, data_index[key]))
    
    return results
```

## Pattern Application Examples

### 1. Secret Audit Script Optimization

Based on the existing `secret-audit.ps1`, here are optimization patterns:

```powershell
# ✅ Optimized secret scanning with performance patterns
function Invoke-OptimizedSecretScan {
    param(
        [string]$ScanPath,
        [string[]]$SecretPatterns,
        [int]$ParallelismLevel = 10
    )
    
    # Pattern: Pre-compiled regex for performance
    $compiledPatterns = foreach ($pattern in $SecretPatterns) {
        @{
            Description = $pattern.Description
            Regex = [regex]::new($pattern.Pattern, 'Compiled,IgnoreCase')
        }
    }
    
    # Pattern: Efficient file filtering
    $files = Get-ChildItem -Path $ScanPath -Recurse -File |
        Where-Object { 
            $_.Length -le 2MB -and
            $_.Extension -notin @('.exe', '.dll', '.bin', '.jpg', '.png') -and
            $_.FullName -notmatch '(\.git|node_modules|__pycache__|\.cache)'
        }
    
    Write-Host "Processing $($files.Count) files with $ParallelismLevel parallel workers..."
    
    # Pattern: Parallel processing for I/O bound operations
    $results = $files | ForEach-Object -Parallel {
        $patterns = $using:compiledPatterns
        $filePath = $_.FullName
        
        try {
            # Pattern: Memory-efficient file reading
            $content = [System.IO.File]::ReadAllText($filePath)
            
            # Pattern: Early termination on first match (for security scanning)
            $fileMatches = @()
            foreach ($patternInfo in $patterns) {
                $matches = $patternInfo.Regex.Matches($content)
                
                foreach ($match in $matches) {
                    $fileMatches += @{
                        File = $filePath
                        Type = $patternInfo.Description
                        Match = $match.Value
                        Position = $match.Index
                    }
                    
                    # Early exit for security scanning (one match is enough)
                    if ($fileMatches.Count -ge 5) { break }
                }
                
                if ($fileMatches.Count -ge 5) { break }
            }
            
            return $fileMatches
        }
        catch {
            # Silent skip for unreadable files
            return @()
        }
    } -ThrottleLimit $ParallelismLevel
    
    return $results
}
```

### 2. Pattern Compilation Optimization

```python
# ✅ Optimized pattern compilation with performance patterns
class OptimizedPatternCompiler:
    """Pattern compiler optimized with performance patterns"""
    
    def __init__(self):
        # Pattern: Multi-level caching
        self.l1_cache = {}  # Recent patterns
        self.l2_cache = TTLCache(ttl_seconds=3600)  # Compiled patterns
        
        # Pattern: Pre-compiled common patterns
        self.common_patterns = self._precompile_common_patterns()
        
        # Pattern: Object pooling for regex objects
        self.regex_pool = ObjectPool(lambda: re.compile(''), max_size=20)
    
    def compile_patterns_optimized(self, patterns: Dict[str, Any]) -> Iterator[Any]:
        """Compile patterns using multiple optimization patterns"""
        
        # Pattern: Sort by complexity for optimal processing order
        sorted_patterns = self._sort_patterns_by_complexity(patterns)
        
        # Pattern: Batch processing similar patterns
        pattern_batches = self._group_patterns_by_similarity(sorted_patterns)
        
        for batch in pattern_batches:
            # Pattern: Vectorized operations for similar patterns
            yield from self._compile_pattern_batch(batch)
    
    def _sort_patterns_by_complexity(self, patterns: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """Sort patterns by complexity for optimal processing"""
        
        def complexity_score(pattern_key: str) -> int:
            # Simple patterns first (can be cached more effectively)
            score = 0
            score += pattern_key.count('*') * 2
            score += pattern_key.count('?') * 1
            score += pattern_key.count('{') * 4
            score += pattern_key.count('[') * 3
            return score
        
        return sorted(patterns.items(), key=lambda x: complexity_score(x[0]))
    
    def _group_patterns_by_similarity(self, sorted_patterns: List[Tuple[str, Any]]) -> List[List[Tuple[str, Any]]]:
        """Group similar patterns for batch processing"""
        
        batches = []
        current_batch = []
        current_prefix = ""
        
        for pattern_key, pattern_value in sorted_patterns:
            # Group by common prefix for cache locality
            pattern_prefix = pattern_key.split('.')[0] if '.' in pattern_key else pattern_key[:3]
            
            if pattern_prefix != current_prefix and current_batch:
                batches.append(current_batch)
                current_batch = []
            
            current_batch.append((pattern_key, pattern_value))
            current_prefix = pattern_prefix
        
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _compile_pattern_batch(self, batch: List[Tuple[str, Any]]) -> Iterator[Any]:
        """Compile batch of similar patterns efficiently"""
        
        # Pattern: Shared regex compilation for similar patterns
        if len(batch) > 1:
            # Try to create shared regex for batch
            shared_regex = self._try_create_shared_regex(batch)
            
            if shared_regex:
                # Use shared regex for entire batch
                for pattern_key, pattern_value in batch:
                    yield self._apply_shared_regex(shared_regex, pattern_key, pattern_value)
                return
        
        # Fall back to individual compilation
        for pattern_key, pattern_value in batch:
            yield self._compile_single_pattern(pattern_key, pattern_value)
```

## Performance Testing Patterns

### 1. Gradual Load Testing

```python
# Pattern: Gradually increase load to find performance limits
def gradual_load_test(operation_func, start_size=100, max_size=100000, growth_factor=2):
    """Find performance breaking point through gradual load increase"""
    
    current_size = start_size
    results = []
    
    while current_size <= max_size:
        print(f"Testing with load size: {current_size:,}")
        
        # Create test data of current size
        test_data = create_test_data(current_size)
        
        try:
            # Measure performance at this load level
            start_time = time.perf_counter()
            result = operation_func(test_data)
            end_time = time.perf_counter()
            
            duration = end_time - start_time
            throughput = len(result) / duration if duration > 0 else 0
            
            load_result = {
                'load_size': current_size,
                'duration_seconds': duration,
                'throughput_ops_per_sec': throughput,
                'memory_usage_mb': get_memory_usage(),
                'success': True
            }
            
            results.append(load_result)
            
            # Check if performance is degrading significantly
            if len(results) > 1:
                prev_throughput = results[-2]['throughput_ops_per_sec']
                current_throughput = load_result['throughput_ops_per_sec']
                
                if current_throughput < prev_throughput * 0.5:  # 50% degradation
                    print(f"⚠️ Significant performance degradation detected at size {current_size:,}")
                    break
            
            current_size = int(current_size * growth_factor)
            
        except MemoryError:
            print(f"🚨 Memory limit reached at size {current_size:,}")
            break
            
        except Exception as e:
            print(f"❌ Error at size {current_size:,}: {e}")
            break
    
    return analyze_load_test_results(results)

def analyze_load_test_results(results):
    """Analyze gradual load test results"""
    
    if not results:
        return {'error': 'No successful load test results'}
    
    # Find optimal load point
    throughputs = [r['throughput_ops_per_sec'] for r in results]
    peak_throughput_idx = throughputs.index(max(throughputs))
    optimal_load = results[peak_throughput_idx]
    
    # Find efficiency point (best throughput/memory ratio)
    efficiency_scores = [
        r['throughput_ops_per_sec'] / max(r['memory_usage_mb'], 1)
        for r in results
    ]
    best_efficiency_idx = efficiency_scores.index(max(efficiency_scores))
    efficient_load = results[best_efficiency_idx]
    
    return {
        'max_successful_load': results[-1]['load_size'],
        'optimal_load_point': optimal_load,
        'most_efficient_load': efficient_load,
        'load_test_summary': {
            'total_loads_tested': len(results),
            'peak_throughput': max(throughputs),
            'throughput_degradation_point': find_degradation_point(results),
            'memory_scaling_factor': calculate_memory_scaling(results)
        }
    }
```

### 2. A/B Testing Pattern for Optimizations

```python
# Pattern: Scientific A/B testing for optimization validation
class PerformanceABTester:
    """A/B test performance optimizations scientifically"""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.alpha = 1 - confidence_level
    
    def ab_test_optimization(
        self, 
        control_func: Callable,
        treatment_func: Callable,
        test_data_generator: Callable,
        sample_size: int = 100
    ) -> Dict[str, Any]:
        """Run A/B test to validate optimization"""
        
        control_samples = []
        treatment_samples = []
        
        print(f"Running A/B test with {sample_size} samples per group...")
        
        # Collect samples in randomized order to avoid bias
        import random
        test_order = ['control', 'treatment'] * (sample_size // 2)
        if sample_size % 2 == 1:
            test_order.append(random.choice(['control', 'treatment']))
        random.shuffle(test_order)
        
        for test_type in test_order:
            # Generate fresh test data for each sample
            test_data = test_data_generator()
            
            if test_type == 'control':
                sample_time = self._measure_single_execution(control_func, test_data)
                control_samples.append(sample_time)
            else:
                sample_time = self._measure_single_execution(treatment_func, test_data)
                treatment_samples.append(sample_time)
        
        # Statistical analysis
        return self._analyze_ab_results(control_samples, treatment_samples)
    
    def _measure_single_execution(self, func: Callable, test_data: Any) -> float:
        """Measure single function execution"""
        start = time.perf_counter()
        func(test_data)
        return (time.perf_counter() - start) * 1_000_000  # microseconds
    
    def _analyze_ab_results(self, control_samples: List[float], treatment_samples: List[float]) -> Dict[str, Any]:
        """Analyze A/B test results with statistical significance"""
        
        # Descriptive statistics
        control_mean = statistics.mean(control_samples)
        treatment_mean = statistics.mean(treatment_samples)
        
        control_std = statistics.stdev(control_samples)
        treatment_std = statistics.stdev(treatment_samples)
        
        # Effect size (percentage improvement)
        effect_size_pct = ((control_mean - treatment_mean) / control_mean) * 100
        
        # Statistical significance test
        try:
            from scipy.stats import ttest_ind
            t_stat, p_value = ttest_ind(control_samples, treatment_samples)
            is_significant = p_value < self.alpha
        except ImportError:
            # Fallback to simple comparison if scipy not available
            is_significant = abs(effect_size_pct) > 10  # Simple 10% threshold
            p_value = None
            t_stat = None
        
        # Practical significance (minimum meaningful improvement)
        practical_threshold = 5.0  # 5% minimum improvement to be meaningful
        is_practically_significant = abs(effect_size_pct) >= practical_threshold
        
        # Determine recommendation
        recommendation = self._generate_ab_recommendation(
            effect_size_pct, is_significant, is_practically_significant
        )
        
        return {
            'control_performance': {
                'mean_us': control_mean,
                'std_us': control_std,
                'sample_size': len(control_samples)
            },
            'treatment_performance': {
                'mean_us': treatment_mean,
                'std_us': treatment_std,
                'sample_size': len(treatment_samples)
            },
            'effect_analysis': {
                'effect_size_percent': effect_size_pct,
                'improvement_direction': 'treatment_better' if effect_size_pct > 0 else 'control_better',
                'statistical_significance': {
                    'is_significant': is_significant,
                    'p_value': p_value,
                    't_statistic': t_stat,
                    'confidence_level': self.confidence_level
                },
                'practical_significance': is_practically_significant
            },
            'recommendation': recommendation
        }
    
    def _generate_ab_recommendation(
        self, 
        effect_size_pct: float, 
        statistically_significant: bool, 
        practically_significant: bool
    ) -> str:
        """Generate recommendation based on A/B test results"""
        
        if statistically_significant and practically_significant:
            if effect_size_pct > 0:
                return f"ADOPT: Treatment is {effect_size_pct:.1f}% faster with statistical confidence"
            else:
                return f"REJECT: Treatment is {abs(effect_size_pct):.1f}% slower with statistical confidence"
        
        elif practically_significant and not statistically_significant:
            return f"INVESTIGATE: {abs(effect_size_pct):.1f}% difference detected but needs more data for confidence"
        
        elif statistically_significant and not practically_significant:
            return f"NO ACTION: Statistically significant but practically insignificant ({effect_size_pct:.1f}%)"
        
        else:
            return "NO DIFFERENCE: No meaningful performance difference detected"
```

### 2. Stream Processing Optimization

```python
# ✅ Optimized stream processing with multiple patterns
class OptimizedStreamProcessor:
    """Stream processor using multiple optimization patterns"""
    
    def __init__(self, chunk_size: int = 1000, cache_size: int = 500):
        # Pattern: Configurable chunk size for memory management
        self.chunk_size = chunk_size
        
        # Pattern: LRU cache for processed chunks
        from functools import lru_cache
        self.process_item = lru_cache(maxsize=cache_size)(self._process_item_uncached)
        
        # Pattern: Object pooling for chunk processors
        self.chunk_processor_pool = ObjectPool(
            lambda: ChunkProcessor(), 
            max_size=10
        )
        
        # Pattern: Adaptive processing based on system resources
        self.adaptive_sizing = True
        self.memory_pressure_threshold = 0.8
    
    def process_stream_optimized(self, data_stream: Iterator[Any]) -> Iterator[Any]:
        """Process stream with multiple optimization patterns"""
        
        chunk = []
        chunk_memory_estimate = 0
        
        for item in data_stream:
            # Pattern: Memory pressure detection
            if self.adaptive_sizing:
                current_memory_pressure = self._get_memory_pressure()
                if current_memory_pressure > self.memory_pressure_threshold:
                    # Reduce chunk size under memory pressure
                    effective_chunk_size = self.chunk_size // 2
                else:
                    effective_chunk_size = self.chunk_size
            else:
                effective_chunk_size = self.chunk_size
            
            # Add item to chunk
            chunk.append(item)
            chunk_memory_estimate += sys.getsizeof(item)
            
            # Pattern: Process when chunk is full or memory limit reached
            if (len(chunk) >= effective_chunk_size or 
                chunk_memory_estimate > 10 * 1024 * 1024):  # 10MB limit
                
                yield from self._process_chunk_with_pooling(chunk)
                chunk.clear()
                chunk_memory_estimate = 0
        
        # Process remaining items
        if chunk:
            yield from self._process_chunk_with_pooling(chunk)
    
    def _process_chunk_with_pooling(self, chunk: List[Any]) -> Iterator[Any]:
        """Process chunk using object pooling pattern"""
        
        processor = self.chunk_processor_pool.acquire()
        try:
            # Pattern: Batch processing with pooled object
            yield from processor.process_batch(chunk)
        finally:
            self.chunk_processor_pool.release(processor)
    
    def _get_memory_pressure(self) -> float:
        """Get current memory pressure (0.0 to 1.0)"""
        try:
            import psutil
            return psutil.virtual_memory().percent / 100.0
        except ImportError:
            return 0.5  # Assume moderate pressure if can't measure
    
    @staticmethod
    def _process_item_uncached(item: Any) -> Any:
        """Uncached version of item processing for LRU cache"""
        # Actual item processing logic
        return transform_item(item)
```

## Performance Pattern Selection Guide

### When to Use Each Pattern

| Use Case | Recommended Pattern | Reasoning |
|----------|-------------------|-----------|
| Frequent lookups | Hash-based data structures | O(1) vs O(n) lookup time |
| Large datasets | Streaming/chunking | Memory efficiency |
| Expensive computations | Caching (LRU/TTL) | Avoid recomputation |
| I/O operations | Batching/pooling | Reduce system call overhead |
| CPU-intensive | Algorithmic optimization | Reduce computational complexity |
| Memory pressure | Lazy loading/generators | Defer allocation until needed |
| Repeated operations | Object pooling | Reduce GC pressure |
| Variable load | Adaptive algorithms | Optimize for current conditions |

### Pattern Combination Strategies

```python
# Example: Combining multiple patterns effectively
class HighPerformancePatternEngine:
    """Combines multiple optimization patterns"""
    
    def __init__(self):
        # Caching pattern
        self.pattern_cache = TTLCache(default_ttl_seconds=1800)
        
        # Object pooling pattern
        self.processor_pool = ObjectPool(lambda: PatternProcessor(), max_size=15)
        
        # Batching pattern
        self.batch_size = 1000
        
        # Lazy initialization pattern
        self._search_index = None
        
        # Adaptive sizing pattern
        self.adaptive_enabled = True
    
    def process_patterns_high_performance(self, patterns: Iterator[str]) -> Iterator[Any]:
        """Process patterns using combined optimization patterns"""
        
        # Streaming + batching pattern
        batch = []
        
        for pattern in patterns:
            # Caching pattern - check cache first
            cached_result = self.pattern_cache.get(
                pattern, 
                lambda: None  # Don't compute yet, just check cache
            )
            
            if cached_result is not None:
                yield cached_result
                continue
            
            # Add to batch for processing
            batch.append(pattern)
            
            # Adaptive batching - adjust size based on system state
            effective_batch_size = self._get_adaptive_batch_size()
            
            if len(batch) >= effective_batch_size:
                yield from self._process_batch_with_all_patterns(batch)
                batch.clear()
        
        # Process remaining patterns
        if batch:
            yield from self._process_batch_with_all_patterns(batch)
    
    def _process_batch_with_all_patterns(self, batch: List[str]) -> Iterator[Any]:
        """Process batch using object pooling and caching"""
        
        # Object pooling pattern
        processor = self.processor_pool.acquire()
        
        try:
            # Lazy initialization pattern
            if self._search_index is None:
                self._search_index = self._build_search_index()
            
            # Process batch with optimized processor
            for pattern in batch:
                result = processor.process_with_index(pattern, self._search_index)
                
                # Cache result
                self.pattern_cache.get(pattern, lambda: result)  # Store in cache
                
                yield result
        
        finally:
            # Return processor to pool
            self.processor_pool.release(processor)
    
    def _get_adaptive_batch_size(self) -> int:
        """Adaptive batch sizing based on system conditions"""
        if not self.adaptive_enabled:
            return self.batch_size
        
        # Adjust based on memory pressure
        memory_pressure = self._get_memory_pressure()
        
        if memory_pressure > 0.8:
            return self.batch_size // 4  # Small batches under pressure
        elif memory_pressure > 0.6:
            return self.batch_size // 2  # Medium batches
        else:
            return self.batch_size      # Full batches when resources available
```

## Performance Metrics and KPIs

### Key Performance Indicators

```python
# Performance KPI tracking for optimization decisions
class PerformanceKPITracker:
    """Track key performance indicators for optimization decisions"""
    
    def __init__(self):
        self.kpis = {
            'throughput_ops_per_second': {'target': 1000, 'critical': 100},
            'latency_p95_microseconds': {'target': 100, 'critical': 1000},
            'memory_usage_mb': {'target': 50, 'critical': 200},
            'cpu_utilization_percent': {'target': 70, 'critical': 90},
            'error_rate_percent': {'target': 0.1, 'critical': 1.0}
        }
    
    def evaluate_performance(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate performance against KPI targets"""
        
        evaluation = {
            'overall_status': 'good',
            'kpi_results': {},
            'priority_issues': [],
            'optimization_opportunities': []
        }
        
        critical_failures = 0
        target_misses = 0
        
        for kpi_name, kpi_config in self.kpis.items():
            if kpi_name in metrics:
                actual_value = metrics[kpi_name]
                target_value = kpi_config['target']
                critical_value = kpi_config['critical']
                
                # Determine if higher or lower is better
                if 'ops_per_second' in kpi_name or 'throughput' in kpi_name:
                    # Higher is better
                    status = 'critical' if actual_value < critical_value else \
                            'miss' if actual_value < target_value else 'good'
                else:
                    # Lower is better
                    status = 'critical' if actual_value > critical_value else \
                            'miss' if actual_value > target_value else 'good'
                
                evaluation['kpi_results'][kpi_name] = {
                    'actual': actual_value,
                    'target': target_value,
                    'critical': critical_value,
                    'status': status,
                    'gap_percent': abs(actual_value - target_value) / target_value * 100
                }
                
                if status == 'critical':
                    critical_failures += 1
                    evaluation['priority_issues'].append(f"CRITICAL: {kpi_name} = {actual_value} (critical threshold: {critical_value})")
                elif status == 'miss':
                    target_misses += 1
                    evaluation['optimization_opportunities'].append(f"OPTIMIZE: {kpi_name} = {actual_value} (target: {target_value})")
        
        # Overall status assessment
        if critical_failures > 0:
            evaluation['overall_status'] = 'critical'
        elif target_misses > len(self.kpis) // 2:
            evaluation['overall_status'] = 'needs_optimization'
        elif target_misses > 0:
            evaluation['overall_status'] = 'good_with_opportunities'
        
        return evaluation
```

## Pattern Implementation Checklist

### Before Implementing Optimization Pattern
- [ ] **Profile first** - Identify actual bottlenecks with measurement
- [ ] **Choose appropriate pattern** - Match pattern to specific performance problem
- [ ] **Consider complexity trade-off** - Ensure optimization justifies added complexity
- [ ] **Plan for measurement** - Design benchmarks to validate improvement

### During Implementation
- [ ] **Implement incrementally** - Apply one pattern at a time
- [ ] **Maintain functionality** - Ensure optimized version produces same results
- [ ] **Add monitoring** - Include performance measurement in optimized code
- [ ] **Document decisions** - Record why specific pattern was chosen

### After Implementation
- [ ] **Validate improvement** - Measure actual performance gain
- [ ] **Test edge cases** - Ensure optimization doesn't break edge cases
- [ ] **Monitor in production** - Track real-world performance impact
- [ ] **Document patterns used** - Help future optimization efforts

The performance patterns in this guide provide proven approaches for optimizing Strataregula components while maintaining code quality and reliability. Apply patterns incrementally and always validate improvements with comprehensive benchmarking.
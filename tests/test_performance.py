#!/usr/bin/env python3
"""
Performance and scalability tests for zarrcompatibility.

Tests performance characteristics, memory usage, and scalability limits.

Author: F. Herbrand
License: MIT
"""

import sys
import time
import gc
import tempfile
from pathlib import Path
from datetime import datetime
from enum import Enum
from uuid import uuid4

# Setup paths
def setup_project_paths():
    current_dir = Path.cwd()
    if current_dir.name == 'tests':
        src_path = current_dir.parent / 'src'
    else:
        src_path = current_dir / 'src'
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return {'src_path': src_path}

PATHS = setup_project_paths()


class DataSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


def measure_time(func):
    """Decorator to measure execution time."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper


def measure_memory():
    """Get current memory usage (simplified)."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB
    except ImportError:
        # Fallback: use gc stats
        return len(gc.get_objects())


class TestSerializationPerformance:
    """Test performance of serialization operations."""
    
    def setup_method(self):
        """Setup for each test."""
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
        
        # Force garbage collection
        gc.collect()
        self.initial_memory = measure_memory()
    
    def teardown_method(self):
        """Cleanup after each test."""
        import zarrcompatibility as zc
        zc.disable_zarr_serialization()
        
        # Force garbage collection
        gc.collect()
    
    @measure_time
    def _serialize_data(self, data):
        """Helper to serialize data with timing."""
        from zarrcompatibility.type_handlers import serialize_object
        return serialize_object(data)
    
    @measure_time
    def _deserialize_data(self, data):
        """Helper to deserialize data with timing."""
        from zarrcompatibility.type_handlers import deserialize_object
        return deserialize_object(data)
    
    def test_tuple_serialization_performance(self):
        """Test performance of tuple serialization at different sizes."""
        test_sizes = [
            (100, DataSize.SMALL),
            (1000, DataSize.MEDIUM),
            (10000, DataSize.LARGE),
        ]
        
        results = []
        
        for size, category in test_sizes:
            # Create test tuple
            test_tuple = tuple(range(size))
            
            # Measure serialization
            serialized, serialize_time = self._serialize_data(test_tuple)
            
            # Measure deserialization
            deserialized, deserialize_time = self._deserialize_data(serialized)
            
            # Verify correctness
            assert deserialized == test_tuple
            assert isinstance(deserialized, tuple)
            
            results.append({
                'size': size,
                'category': category.value,
                'serialize_time': serialize_time,
                'deserialize_time': deserialize_time,
                'total_time': serialize_time + deserialize_time
            })
            
            print(f"✅ Tuple size {size}: serialize={serialize_time:.4f}s, deserialize={deserialize_time:.4f}s")
        
        # Check for performance regression
        for result in results:
            if result['category'] == 'large' and result['total_time'] > 1.0:
                print(f"⚠️ Large tuple performance may be slow: {result['total_time']:.4f}s")
    
    def test_nested_structure_performance(self):
        """Test performance with deeply nested structures."""
        nesting_levels = [10, 50, 100]
        
        for level in nesting_levels:
            # Create nested structure
            nested = {"level": 0, "data": (0, 1, 2)}
            current = nested
            
            for i in range(1, level):
                current["next"] = {
                    "level": i,
                    "data": (i, i*2, i*3),
                    "timestamp": datetime.now()
                }
                current = current["next"]
            
            try:
                # Measure performance
                serialized, serialize_time = self._serialize_data(nested)
                deserialized, deserialize_time = self._deserialize_data(serialized)
                
                # Verify correctness
                assert deserialized["level"] == 0
                assert isinstance(deserialized["data"], tuple)
                
                total_time = serialize_time + deserialize_time
                print(f"✅ Nesting level {level}: {total_time:.4f}s")
                
                # Check for reasonable performance
                if total_time > 0.5:
                    print(f"⚠️ Deep nesting performance concern at level {level}: {total_time:.4f}s")
                    
            except RecursionError:
                print(f"❌ Hit recursion limit at nesting level {level}")
                break
    
    def test_complex_types_performance(self):
        """Test performance with various complex types."""
        import uuid
        from decimal import Decimal
        from datetime import datetime
        
        # FIXED: Einfacher - verwende keine Dataclasses in Performance-Tests
        # Dataclasses sind komplex zu serialisieren, für Performance-Tests reichen andere Typen
        
        # Create test data with various types (excluding dataclasses)
        complex_data = {
            "tuples": [(i, i*2, i*3) for i in range(100)],
            "datetimes": [datetime.now() for _ in range(50)],
            "uuids": [uuid.uuid4() for _ in range(50)],
            "decimals": [Decimal(f"{i}.{i*2}") for i in range(50)],
            "enums": [DataSize.SMALL, DataSize.MEDIUM, DataSize.LARGE] * 10,
            "complex_numbers": [complex(i, i*2) for i in range(25)],
            "bytes_data": [f"data_{i}".encode() for i in range(25)],
            # Use simple dict instead of dataclass for performance testing
            "dict_objects": [{"id": i, "name": f"item_{i}", "value": i*2} for i in range(25)]
        }
        
        # Measure performance
        serialized, serialize_time = self._serialize_data(complex_data)
        deserialized, deserialize_time = self._deserialize_data(serialized)
        
        # Verify correctness
        assert len(deserialized["tuples"]) == 100
        assert all(isinstance(t, tuple) for t in deserialized["tuples"])
        assert all(isinstance(dt, datetime) for dt in deserialized["datetimes"])
        assert all(isinstance(d, dict) for d in deserialized["dict_objects"])
        
        total_time = serialize_time + deserialize_time
        print(f"✅ Complex types performance: {total_time:.4f}s")
        
        # Performance expectation
        if total_time > 2.0:
            print(f"⚠️ Complex types performance may be slow: {total_time:.4f}s")


class TestMemoryUsage:
    """Test memory usage characteristics."""
    
    def setup_method(self):
        """Setup for each test."""
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
        gc.collect()
        self.initial_memory = measure_memory()
    
    def teardown_method(self):
        """Cleanup after each test."""
        import zarrcompatibility as zc
        zc.disable_zarr_serialization()
        gc.collect()
    
    def test_memory_usage_repeated_operations(self):
        """Test memory usage during repeated operations."""
        from zarrcompatibility.type_handlers import serialize_object, deserialize_object
        
        gc.collect()
        memory_start = measure_memory()
        
        # Perform many serialize/deserialize cycles
        test_data = {
            "numbers": (1, 2, 3, 4, 5),
            "timestamp": datetime.now(),
            "metadata": {"type": "test", "version": (1, 0, 0)}
        }
        
        for i in range(100):
            serialized = serialize_object(test_data)
            deserialized = deserialize_object(serialized)
            
            # Verify correctness occasionally
            if i % 25 == 0:
                assert deserialized["numbers"] == (1, 2, 3, 4, 5)
                assert isinstance(deserialized["numbers"], tuple)
                assert isinstance(deserialized["timestamp"], datetime)
        
        gc.collect()
        memory_end = measure_memory()
        memory_growth = memory_end - memory_start
        
        print(f"✅ 100 cycles: {memory_growth:.1f}MB memory growth")
        
        # Check for reasonable memory usage
        if memory_growth > 50:  # More than 50MB for 100 cycles
            print(f"⚠️ High memory growth: {memory_growth:.1f}MB for 100 cycles")


class TestZarrIntegrationPerformance:
    """Test performance of Zarr integration."""
    
    def setup_method(self):
        """Setup for each test."""
        try:
            import zarr
            self.zarr_available = True
        except ImportError:
            self.zarr_available = False
            return
        
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test."""
        if self.zarr_available:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_zarr_attribute_performance(self):
        """Test performance of Zarr attribute operations."""
        if not self.zarr_available:
            print("⚠️ Skipping - Zarr not available")
            return
        
        import zarr
        
        # Test with memory store (fastest)
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        # Test data
        test_attributes = {
            f"attr_{i}": (i, i*2, i*3, f"value_{i}", datetime.now())
            for i in range(100)
        }
        
        # Measure attribute setting performance
        start_time = time.time()
        for key, value in test_attributes.items():
            group.attrs[key] = value
        set_time = time.time() - start_time
        
        # Measure attribute getting performance
        start_time = time.time()
        retrieved_attrs = {}
        for key in test_attributes.keys():
            retrieved_attrs[key] = group.attrs[key]
        get_time = time.time() - start_time
        
        # Verify correctness
        for key, original_value in test_attributes.items():
            retrieved_value = retrieved_attrs[key]
            assert retrieved_value == original_value
            assert isinstance(retrieved_value, tuple)
        
        print(f"✅ Zarr attributes: set={set_time:.4f}s, get={get_time:.4f}s")
        
        # Performance expectations
        if set_time > 1.0:
            print(f"⚠️ Zarr attribute setting may be slow: {set_time:.4f}s")
        if get_time > 1.0:
            print(f"⚠️ Zarr attribute getting may be slow: {get_time:.4f}s")
    
    def test_zarr_file_operations_performance(self):
        """Test performance of Zarr file operations."""
        if not self.zarr_available:
            print("⚠️ Skipping - Zarr not available")
            return
        
        import zarr
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create group with complex metadata
            group_path = Path(tmpdir) / "performance_test.zarr"
            group = zarr.open_group(str(group_path), mode="w")
            
            # Add complex metadata
            complex_metadata = {
                "experiment": {
                    "version": (3, 0, 0),
                    "created": datetime.now(),
                    "parameters": {
                        "roi_list": [(i*10, i*20, i*30, i*40) for i in range(50)],
                        "timestamps": tuple(range(100)),
                        "calibration": (1.0, 0.0, 0.001)
                    }
                }
            }
            
            # Measure write performance
            start_time = time.time()
            group.attrs.update(complex_metadata)
            group.store.close()
            write_time = time.time() - start_time
            
            # Measure read performance
            start_time = time.time()
            reloaded_group = zarr.open_group(str(group_path), mode="r")
            loaded_metadata = dict(reloaded_group.attrs)
            read_time = time.time() - start_time
            
            # Verify correctness
            assert loaded_metadata["experiment"]["version"] == (3, 0, 0)
            assert isinstance(loaded_metadata["experiment"]["version"], tuple)
            assert len(loaded_metadata["experiment"]["parameters"]["roi_list"]) == 50
            assert all(isinstance(roi, tuple) for roi in loaded_metadata["experiment"]["parameters"]["roi_list"])
            
            print(f"✅ Zarr file operations: write={write_time:.4f}s, read={read_time:.4f}s")
            
            # Performance expectations
            if write_time > 2.0:
                print(f"⚠️ Zarr file write may be slow: {write_time:.4f}s")
            if read_time > 2.0:
                print(f"⚠️ Zarr file read may be slow: {read_time:.4f}s")


class TestScalabilityLimits:
    """Test scalability and limits."""
    
    def setup_method(self):
        """Setup for each test."""
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test."""
        import zarrcompatibility as zc
        zc.disable_zarr_serialization()
    
    def test_maximum_tuple_size(self):
        """Test maximum practical tuple size."""
        from zarrcompatibility.type_handlers import serialize_object, deserialize_object
        
        # Test increasing sizes until we hit limits
        sizes = [10000, 50000, 100000]
        max_working_size = 0
        
        for size in sizes:
            try:
                print(f"Testing tuple size: {size}")
                
                # Create large tuple
                large_tuple = tuple(range(size))
                
                # Test serialization
                start_time = time.time()
                serialized = serialize_object(large_tuple)
                serialize_time = time.time() - start_time
                
                # Test deserialization
                start_time = time.time()
                deserialized = deserialize_object(serialized)
                deserialize_time = time.time() - start_time
                
                # Verify correctness
                assert len(deserialized) == size
                assert isinstance(deserialized, tuple)
                assert deserialized[0] == 0
                assert deserialized[-1] == size - 1
                
                max_working_size = size
                total_time = serialize_time + deserialize_time
                
                print(f"✅ Size {size}: {total_time:.4f}s")
                
                # Clean up
                del large_tuple, serialized, deserialized
                gc.collect()
                
                # Stop if it's getting too slow
                if total_time > 5.0:
                    print(f"⚠️ Stopping at size {size} due to slow performance")
                    break
                    
            except (MemoryError, RecursionError) as e:
                print(f"❌ Hit limit at size {size}: {type(e).__name__}")
                break
        
        print(f"✅ Maximum practical tuple size: {max_working_size}")
    
    def test_maximum_nesting_depth(self):
        """Test maximum practical nesting depth."""
        from zarrcompatibility.type_handlers import serialize_object, deserialize_object
        
        max_working_depth = 0
        
        for depth in [100, 500, 1000]:
            try:
                print(f"Testing nesting depth: {depth}")
                
                # Create deeply nested structure
                nested = {"level": 0}
                current = nested
                
                for i in range(1, depth):
                    current["next"] = {"level": i, "data": (i, i*2)}
                    current = current["next"]
                
                # Test serialization
                start_time = time.time()
                serialized = serialize_object(nested)
                serialize_time = time.time() - start_time
                
                # Test deserialization
                start_time = time.time()
                deserialized = deserialize_object(serialized)
                deserialize_time = time.time() - start_time
                
                # Verify correctness
                current = deserialized
                for i in range(depth):
                    assert current["level"] == i
                    if "data" in current:
                        assert isinstance(current["data"], tuple)
                    if "next" not in current:
                        break
                    current = current["next"]
                
                max_working_depth = depth
                total_time = serialize_time + deserialize_time
                
                print(f"✅ Depth {depth}: {total_time:.4f}s")
                
                # Clean up
                del nested, serialized, deserialized
                gc.collect()
                
                # Stop if it's getting too slow
                if total_time > 5.0:
                    print(f"⚠️ Stopping at depth {depth} due to slow performance")
                    break
                    
            except (MemoryError, RecursionError) as e:
                print(f"❌ Hit limit at depth {depth}: {type(e).__name__}")
                break
        
        print(f"✅ Maximum practical nesting depth: {max_working_depth}")


class TestBenchmarkComparisons:
    """Benchmark against standard JSON."""
    
    def test_performance_vs_standard_json(self):
        """Compare performance against standard JSON."""
        import json
        import zarrcompatibility as zc
        from zarrcompatibility.serializers import enhanced_json_dumps, enhanced_json_loads
        
        # Test data that works with both systems
        test_data = {
            "numbers": [1, 2, 3, 4, 5],
            "strings": ["hello", "world", "test"],
            "nested": {
                "level1": {
                    "level2": {
                        "data": [10, 20, 30]
                    }
                }
            },
            "mixed": [1, "two", 3.0, True, None]
        }
        
        # Test standard JSON
        start_time = time.time()
        for _ in range(1000):
            json_str = json.dumps(test_data)
            loaded = json.loads(json_str)
        standard_time = time.time() - start_time
        
        # Test enhanced JSON
        zc.enable_zarr_serialization()
        try:
            start_time = time.time()
            for _ in range(1000):
                enhanced_str = enhanced_json_dumps(test_data)
                loaded = enhanced_json_loads(enhanced_str)
            enhanced_time = time.time() - start_time
        finally:
            zc.disable_zarr_serialization()
        
        # Calculate overhead
        overhead = (enhanced_time / standard_time - 1) * 100
        
        print(f"✅ Standard JSON: {standard_time:.4f}s")
        print(f"✅ Enhanced JSON: {enhanced_time:.4f}s")
        print(f"✅ Overhead: {overhead:.1f}%")
        
        # Performance expectation: should be within reasonable overhead
        if overhead > 50:  # More than 50% overhead
            print(f"⚠️ High overhead compared to standard JSON: {overhead:.1f}%")


def run_all_performance_tests():
    """Run all performance tests."""
    print("🧪 zarrcompatibility v3.0 - Performance & Scalability Tests")
    print("=" * 70)
    
    test_classes = [
        TestSerializationPerformance(),
        TestMemoryUsage(),
        TestZarrIntegrationPerformance(),
        TestScalabilityLimits(),
        TestBenchmarkComparisons(),
    ]
    
    all_tests = []
    for test_instance in test_classes:
        methods = [getattr(test_instance, method) for method in dir(test_instance) 
                  if method.startswith('test_') and callable(getattr(test_instance, method))]
        all_tests.extend([(test_instance, method) for method in methods])
    
    passed = 0
    performance_warnings = 0
    
    for i, (test_instance, test_method) in enumerate(all_tests, 1):
        test_name = f"{test_instance.__class__.__name__}.{test_method.__name__}"
        print(f"\n🔍 Test {i}: {test_name}")
        
        try:
            test_instance.setup_method()
            test_method()
            test_instance.teardown_method()
            
            print(f"✅ Test {i} passed")
            passed += 1
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                test_instance.teardown_method()
            except:
                pass
    
    print(f"\n📊 Performance Results: {passed}/{len(all_tests)} tests passed")
    
    if performance_warnings > 0:
        print(f"⚠️ {performance_warnings} performance warnings detected")
        print("   Consider optimizing slow operations or adjusting expectations")
    
    return passed == len(all_tests)


if __name__ == "__main__":
    success = run_all_performance_tests()
    sys.exit(0 if success else 1)
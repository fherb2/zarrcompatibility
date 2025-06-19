"""
Comprehensive Unit Tests for zarrcompatibility Module

This test suite serves dual purposes:
1. Thorough testing of all module functionality
2. Living documentation with practical usage examples

Each test method demonstrates specific use cases and can be used
as reference for how to use the zarrcompatibility module.

Run tests with: python -m pytest tests/test_serialization.py -v
"""

import json
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import the module under test
import zarrcompatibility as zc

# Optional: Test with actual zarr if available
try:
    import zarr
    HAS_ZARR = True
except ImportError:
    HAS_ZARR = False


class TestBasicSerialization(unittest.TestCase):
    """
    Test basic serialization functionality.
    
    These examples show how to serialize common Python objects.
    """
    
    def setUp(self):
        """Enable universal serialization for each test."""
        zc.enable_universal_serialization()
    
    def tearDown(self):
        """Clean up after each test."""
        zc.disable_universal_serialization()
    
    def test_basic_types_passthrough(self):
        """
        EXAMPLE: Basic JSON types should pass through unchanged.
        
        This demonstrates that the serializer doesn't interfere
        with standard JSON-compatible types.
        """
        # Test data
        test_cases = [
            None,           # null
            True,           # boolean
            False,          # boolean  
            42,             # integer
            3.14,           # float
            "hello world",  # string
        ]
        
        for original in test_cases:
            with self.subTest(value=original):
                # Serialize using our function
                serialized = zc.serialize_object(original)
                
                # Should be identical to original
                self.assertEqual(serialized, original)
                
                # Should work with json.dumps after enabling universal serialization
                json_str = json.dumps(original)
                self.assertIsInstance(json_str, str)
    
    def test_builtin_types_serialization(self):
        """
        EXAMPLE: How to serialize Python built-in types that aren't JSON-compatible.
        
        This shows automatic handling of datetime, UUID, Decimal, etc.
        """
        # Test datetime serialization
        now = datetime(2024, 1, 15, 14, 30, 45)
        serialized_dt = zc.serialize_object(now)
        self.assertEqual(serialized_dt, "2024-01-15T14:30:45")
        
        # Test date serialization  
        today = date(2024, 1, 15)
        serialized_date = zc.serialize_object(today)
        self.assertEqual(serialized_date, "2024-01-15")
        
        # Test time serialization
        current_time = time(14, 30, 45)
        serialized_time = zc.serialize_object(current_time)
        self.assertEqual(serialized_time, "14:30:45")
        
        # Test UUID serialization
        test_uuid = UUID('12345678-1234-5678-1234-567812345678')
        serialized_uuid = zc.serialize_object(test_uuid)
        self.assertEqual(serialized_uuid, '12345678-1234-5678-1234-567812345678')
        
        # Test Decimal serialization
        decimal_val = Decimal('123.456')
        serialized_decimal = zc.serialize_object(decimal_val)
        self.assertEqual(serialized_decimal, '123.456')
        
        # Test complex number serialization
        complex_num = complex(3, 4)
        serialized_complex = zc.serialize_object(complex_num)
        expected_complex = {'real': 3.0, 'imag': 4.0, '_type': 'complex'}
        self.assertEqual(serialized_complex, expected_complex)
        
        # Test bytes serialization (base64 encoded)
        test_bytes = b'hello world'
        serialized_bytes = zc.serialize_object(test_bytes)
        import base64
        expected_bytes = base64.b64encode(test_bytes).decode('ascii')
        self.assertEqual(serialized_bytes, expected_bytes)


class TestEnumSerialization(unittest.TestCase):
    """
    Test enum serialization with practical examples.
    
    This demonstrates how to work with Python enums in Zarr.
    """
    
    def setUp(self):
        zc.enable_universal_serialization()
    
    def tearDown(self):
        zc.disable_universal_serialization()
    
    def test_string_enum_serialization(self):
        """
        EXAMPLE: Serializing string-based enums.
        
        Common pattern for status flags, categories, etc.
        """
        class ProcessingStatus(Enum):
            PENDING = "pending"
            PROCESSING = "processing" 
            COMPLETED = "completed"
            FAILED = "failed"
        
        # Test serialization
        status = ProcessingStatus.COMPLETED
        serialized = zc.serialize_object(status)
        self.assertEqual(serialized, "completed")
        
        # Test that it works with json.dumps
        json_result = json.dumps(status)
        self.assertEqual(json_result, '"completed"')
    
    def test_numeric_enum_serialization(self):
        """
        EXAMPLE: Serializing numeric enums.
        
        Useful for priority levels, error codes, etc.
        """
        class Priority(Enum):
            LOW = 1
            MEDIUM = 5
            HIGH = 10
            CRITICAL = 20
        
        priority = Priority.HIGH
        serialized = zc.serialize_object(priority)
        self.assertEqual(serialized, 10)
        
        # Verify JSON compatibility
        json_result = json.dumps(priority)
        self.assertEqual(json_result, "10")


class TestDataclassSerialization(unittest.TestCase):
    """
    Test dataclass serialization with real-world examples.
    
    Shows how to use dataclasses with Zarr metadata.
    """
    
    def setUp(self):
        zc.enable_universal_serialization()
    
    def tearDown(self):
        zc.disable_universal_serialization()
    
    def test_simple_dataclass(self):
        """
        EXAMPLE: Simple dataclass serialization.
        
        Perfect for storing experiment parameters, configuration, etc.
        """
        @dataclass
        class ExperimentConfig:
            name: str
            iterations: int
            learning_rate: float
            use_cuda: bool
        
        config = ExperimentConfig(
            name="test_experiment",
            iterations=1000,
            learning_rate=0.001,
            use_cuda=True
        )
        
        # Serialize the dataclass
        serialized = zc.serialize_object(config)
        expected = {
            'name': 'test_experiment',
            'iterations': 1000,
            'learning_rate': 0.001,
            'use_cuda': True
        }
        self.assertEqual(serialized, expected)
        
        # Test JSON compatibility
        json_str = json.dumps(config)
        reconstructed = json.loads(json_str)
        self.assertEqual(reconstructed, expected)
    
    def test_nested_dataclass(self):
        """
        EXAMPLE: Nested dataclasses with complex types.
        
        Shows handling of nested structures common in scientific computing.
        """
        @dataclass
        class Dimensions:
            height: int
            width: int
            depth: int
        
        @dataclass
        class Dataset:
            name: str
            created: datetime
            dimensions: Dimensions
            tags: List[str]
        
        dims = Dimensions(height=512, width=512, depth=100)
        dataset = Dataset(
            name="brain_scan_001",
            created=datetime(2024, 1, 15, 10, 30),
            dimensions=dims,
            tags=["medical", "mri", "brain"]
        )
        
        serialized = zc.serialize_object(dataset)
        
        # Verify structure
        self.assertEqual(serialized['name'], "brain_scan_001")
        self.assertEqual(serialized['created'], "2024-01-15T10:30:00")
        self.assertEqual(serialized['dimensions']['height'], 512)
        self.assertEqual(serialized['tags'], ["medical", "mri", "brain"])


class TestRegularClassSerialization(unittest.TestCase):
    """
    Test serialization of regular Python classes.
    
    Demonstrates working with custom classes that aren't dataclasses.
    """
    
    def setUp(self):
        zc.enable_universal_serialization()
    
    def tearDown(self):
        zc.disable_universal_serialization()
    
    def test_simple_class_serialization(self):
        """
        EXAMPLE: Serializing a regular Python class.
        
        Shows automatic attribute extraction from __dict__.
        """
        class ImageProcessor:
            def __init__(self, algorithm, threshold=0.5):
                self.algorithm = algorithm
                self.threshold = threshold
                self.processed_count = 0
            
            def process(self):
                """This method won't be serialized (it's callable)."""
                self.processed_count += 1
        
        processor = ImageProcessor("gaussian_blur", threshold=0.7)
        processor.process()  # Increment counter
        
        serialized = zc.serialize_object(processor)
        expected = {
            'algorithm': 'gaussian_blur',
            'threshold': 0.7,
            'processed_count': 1
        }
        self.assertEqual(serialized, expected)
    
    def test_class_with_json_method(self):
        """
        EXAMPLE: Class with custom __json__ method.
        
        Shows how to provide custom serialization logic.
        """
        class SmartConfig:
            def __init__(self, values):
                self._values = values
                self._secret = "don't serialize this"
            
            def __json__(self):
                """Custom serialization - only expose values, not secrets."""
                return {
                    'values': self._values,
                    'serialized_at': datetime.now().isoformat()
                }
        
        config = SmartConfig({'setting1': 'value1', 'setting2': 42})
        serialized = zc.serialize_object(config)
        
        # Should use custom __json__ method
        self.assertIn('values', serialized)
        self.assertIn('serialized_at', serialized)
        self.assertNotIn('_secret', str(serialized))
        self.assertEqual(serialized['values'], {'setting1': 'value1', 'setting2': 42})


class TestCollectionSerialization(unittest.TestCase):
    """
    Test serialization of Python collections.
    
    Demonstrates handling of lists, sets, tuples, and dictionaries.
    """
    
    def setUp(self):
        zc.enable_universal_serialization()
    
    def tearDown(self):
        zc.disable_universal_serialization()
    
    def test_list_serialization(self):
        """
        EXAMPLE: Serializing lists with mixed content.
        
        Shows recursive serialization of list elements.
        """
        @dataclass
        class Point:
            x: float
            y: float
        
        mixed_list = [
            42,
            "hello",
            Point(1.0, 2.0),
            datetime(2024, 1, 15),
            {'nested': 'dict'}
        ]
        
        serialized = zc.serialize_object(mixed_list)
        
        # Verify each element is properly serialized
        self.assertEqual(serialized[0], 42)
        self.assertEqual(serialized[1], "hello")
        self.assertEqual(serialized[2], {'x': 1.0, 'y': 2.0})
        self.assertEqual(serialized[3], "2024-01-15T00:00:00")
        self.assertEqual(serialized[4], {'nested': 'dict'})
    
    def test_set_serialization(self):
        """
        EXAMPLE: Serializing sets (converted to lists).
        
        Note: Sets become lists since JSON doesn't have sets.
        """
        test_set = {1, 2, 3, "hello", "world"}
        serialized = zc.serialize_object(test_set)
        
        # Should be a list
        self.assertIsInstance(serialized, list)
        # Should contain all original elements
        self.assertEqual(set(serialized), test_set)
    
    def test_dict_serialization(self):
        """
        EXAMPLE: Serializing complex dictionaries.
        
        Shows handling of nested structures and complex values.
        """
        complex_dict = {
            'config': {
                'name': 'experiment_1',
                'params': [1, 2, 3]
            },
            'timestamp': datetime(2024, 1, 15),
            'status': 'active',
            'results': None
        }
        
        serialized = zc.serialize_object(complex_dict)
        
        self.assertEqual(serialized['config']['name'], 'experiment_1')
        self.assertEqual(serialized['config']['params'], [1, 2, 3])
        self.assertEqual(serialized['timestamp'], '2024-01-15T00:00:00')
        self.assertEqual(serialized['status'], 'active')
        self.assertEqual(serialized['results'], None)


class TestMixinClasses(unittest.TestCase):
    """
    Test the provided mixin classes.
    
    Shows how to use JSONSerializable and ZarrCompatible mixins.
    """
    
    def test_json_serializable_mixin(self):
        """
        EXAMPLE: Using the JSONSerializable mixin.
        
        Adds convenient methods to any class.
        """
        class DataContainer(zc.JSONSerializable):
            def __init__(self, data, metadata=None):
                self.data = data
                self.metadata = metadata or {}
        
        container = DataContainer([1, 2, 3], {'source': 'test'})
        
        # Test to_dict method
        as_dict = container.to_dict()
        expected = {
            'data': [1, 2, 3],
            'metadata': {'source': 'test'}
        }
        self.assertEqual(as_dict, expected)
        
        # Test to_json method
        json_str = container.to_json()
        self.assertIsInstance(json_str, str)
        reconstructed = json.loads(json_str)
        self.assertEqual(reconstructed, expected)
        
        # Test __json__ method
        json_repr = container.__json__()
        self.assertEqual(json_repr, expected)
    
    def test_zarr_compatible_mixin(self):
        """
        EXAMPLE: Using the ZarrCompatible mixin.
        
        Perfect for storing metadata in Zarr arrays.
        """
        class ExperimentMetadata(zc.ZarrCompatible):
            def __init__(self, name, date, parameters):
                self.name = name
                self.date = date
                self.parameters = parameters
        
        metadata = ExperimentMetadata(
            name="test_experiment",
            date=datetime(2024, 1, 15),
            parameters={'lr': 0.001, 'batch_size': 32}
        )
        
        # Test Zarr-specific methods
        zarr_attrs = metadata.to_zarr_attrs()
        self.assertIn('name', zarr_attrs)
        self.assertEqual(zarr_attrs['name'], 'test_experiment')
        self.assertEqual(zarr_attrs['date'], '2024-01-15T00:00:00')
        
        # Test round-trip through Zarr attributes
        reconstructed = ExperimentMetadata.from_zarr_attrs(zarr_attrs)
        self.assertEqual(reconstructed.name, metadata.name)


class TestDecorator(unittest.TestCase):
    """
    Test the @make_serializable decorator.
    
    Shows how to add serialization to existing classes.
    """
    
    def test_make_serializable_decorator(self):
        """
        EXAMPLE: Using the @make_serializable decorator.
        
        Alternative to mixins for adding serialization capabilities.
        """
        @zc.make_serializable
        class ProcessingJob:
            def __init__(self, job_id, status, progress=0.0):
                self.job_id = job_id
                self.status = status
                self.progress = progress
        
        job = ProcessingJob("job_123", "running", 0.75)
        
        # Should now have serialization methods
        self.assertTrue(hasattr(job, '__json__'))
        self.assertTrue(hasattr(job, 'to_dict'))
        self.assertTrue(hasattr(job, 'to_json'))
        
        # Test the methods work
        as_dict = job.to_dict()
        expected = {
            'job_id': 'job_123',
            'status': 'running',
            'progress': 0.75
        }
        self.assertEqual(as_dict, expected)
        
        # Test JSON serialization works
        json_str = job.to_json()
        reconstructed = json.loads(json_str)
        self.assertEqual(reconstructed, expected)


class TestUtilityFunctions(unittest.TestCase):
    """
    Test utility functions.
    
    Shows how to use helper functions for testing and preparation.
    """
    
    def test_is_json_serializable(self):
        """
        EXAMPLE: Testing if objects are JSON serializable.
        
        Useful for validation before storing in Zarr.
        """
        # Enable universal serialization
        zc.enable_universal_serialization()
        
        try:
            # These should be serializable
            self.assertTrue(zc.is_json_serializable("hello"))
            self.assertTrue(zc.is_json_serializable(42))
            self.assertTrue(zc.is_json_serializable([1, 2, 3]))
            
            # After enabling universal serialization, these should work too
            self.assertTrue(zc.is_json_serializable(datetime.now()))
            
            @dataclass
            class TestData:
                value: int
            
            self.assertTrue(zc.is_json_serializable(TestData(42)))
        
        finally:
            zc.disable_universal_serialization()
    
    def test_prepare_for_zarr(self):
        """
        EXAMPLE: Preparing objects for Zarr storage.
        
        Explicit conversion without global patching.
        """
        @dataclass
        class SampleData:
            name: str
            timestamp: datetime
            values: List[int]
        
        sample = SampleData(
            name="test_sample",
            timestamp=datetime(2024, 1, 15),
            values=[1, 2, 3, 4, 5]
        )
        
        # Prepare for Zarr (explicit serialization)
        zarr_ready = zc.prepare_for_zarr(sample)
        
        expected = {
            'name': 'test_sample',
            'timestamp': '2024-01-15T00:00:00',
            'values': [1, 2, 3, 4, 5]
        }
        self.assertEqual(zarr_ready, expected)
        
        # Should be JSON serializable
        json_str = json.dumps(zarr_ready)
        self.assertIsInstance(json_str, str)
    
    def test_serialization_testing(self):
        """
        EXAMPLE: Testing serialization with test_serialization function.
        
        Useful for debugging serialization issues.
        """
        @dataclass
        class TestObject:
            name: str
            value: int
        
        obj = TestObject("test", 42)
        
        # Test serialization (returns True/False)
        result = zc.test_serialization(obj, verbose=False)
        self.assertTrue(result)
        
        # Test with verbose output (useful for debugging)
        # This would print detailed information in real usage
        verbose_result = zc.test_serialization(obj, verbose=True)
        self.assertTrue(verbose_result)


@unittest.skipUnless(HAS_ZARR, "Zarr not available")
class TestZarrIntegration(unittest.TestCase):
    """
    Integration tests with actual Zarr arrays.
    
    These tests require zarr to be installed and demonstrate
    real-world usage with Zarr arrays and groups.
    """
    
    def setUp(self):
        """Set up temporary directory for Zarr tests."""
        self.temp_dir = tempfile.mkdtemp()
        zc.enable_universal_serialization()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)
        zc.disable_universal_serialization()
    
    def test_zarr_array_metadata(self):
        """
        EXAMPLE: Storing complex metadata in Zarr arrays.
        
        Shows how to attach rich metadata to Zarr arrays.
        """
        # Create a Zarr array
        store_path = Path(self.temp_dir) / "test_array.zarr"
        z = zarr.open(str(store_path), mode='w', shape=(100, 100), dtype='f4')
        
        # Create complex metadata
        @dataclass
        class ArrayMetadata:
            experiment_name: str
            created_date: datetime
            parameters: Dict[str, Any]
            processing_steps: List[str]
        
        metadata = ArrayMetadata(
            experiment_name="image_analysis_001",
            created_date=datetime(2024, 1, 15, 14, 30),
            parameters={
                "threshold": 0.5,
                "kernel_size": 3,
                "iterations": 10
            },
            processing_steps=["normalize", "blur", "threshold", "dilate"]
        )
        
        # Store metadata in Zarr attributes
        z.attrs['experiment_metadata'] = metadata
        
        # Verify storage worked
        self.assertIn('experiment_metadata', z.attrs)
        
        # Read back and verify
        stored_metadata = z.attrs['experiment_metadata']
        
        # Handle both cases: if it's stored as object or as dict
        if hasattr(stored_metadata, 'experiment_name'):
            # Stored as object
            self.assertEqual(stored_metadata.experiment_name, "image_analysis_001")
            self.assertEqual(stored_metadata.created_date, datetime(2024, 1, 15, 14, 30))
            self.assertEqual(stored_metadata.parameters['threshold'], 0.5)
            self.assertEqual(len(stored_metadata.processing_steps), 4)
        else:
            # Stored as dict
            self.assertEqual(stored_metadata['experiment_name'], "image_analysis_001")
            self.assertEqual(stored_metadata['created_date'], "2024-01-15T14:30:00")
            self.assertEqual(stored_metadata['parameters']['threshold'], 0.5)
            self.assertEqual(len(stored_metadata['processing_steps']), 4)
    
    def test_zarr_group_with_mixin(self):
        """
        EXAMPLE: Using ZarrCompatible mixin with Zarr groups.
        
        Shows convenient methods for Zarr integration.
        """
        # Create Zarr group
        store_path = Path(self.temp_dir) / "test_group.zarr"
        group = zarr.open_group(str(store_path), mode='w')
        
        # Create metadata using ZarrCompatible mixin
        class DatasetInfo(zc.ZarrCompatible):
            def __init__(self, name, version, description):
                self.name = name
                self.version = version
                self.description = description
                self.created_at = datetime.now()
        
        info = DatasetInfo(
            name="brain_mri_dataset",
            version="1.2.0",
            description="High-resolution brain MRI scans"
        )
        
        # Use convenient method to save to Zarr
        info.save_to_zarr_group(group, 'dataset_info')
        
        # Verify it was saved
        self.assertIn('dataset_info', group.attrs)
        
        # Use convenient method to load from Zarr
        loaded_info = DatasetInfo.load_from_zarr_group(group, 'dataset_info')
        
        self.assertEqual(loaded_info.name, info.name)
        self.assertEqual(loaded_info.version, info.version)
        self.assertEqual(loaded_info.description, info.description)


class TestEdgeCases(unittest.TestCase):
    """
    Test edge cases and error handling.
    
    Shows how the module handles unusual or problematic inputs.
    """
    
    def setUp(self):
        zc.enable_universal_serialization()
    
    def tearDown(self):
        zc.disable_universal_serialization()
    
    def test_circular_references(self):
        """
        EXAMPLE: Handling objects with circular references.
        
        Shows graceful degradation for problematic objects.
        """
        class CircularRef:
            def __init__(self, name):
                self.name = name
                self.ref = self  # Circular reference!
        
        obj = CircularRef("test")
        
        # Should not crash, but will fall back to string representation
        try:
            serialized = zc.serialize_object(obj)
            # Should get some kind of result (likely string fallback)
            self.assertIsNotNone(serialized)
        except RecursionError:
            # This is acceptable behavior for circular references
            pass
    
    def test_unserializable_objects(self):
        """
        EXAMPLE: Handling truly unserializable objects.
        
        Shows fallback behavior for problematic objects.
        """
        # Lambda functions can't be serialized
        lambda_func = lambda x: x + 1
        
        serialized = zc.serialize_object(lambda_func)
        # Should fall back to string representation
        self.assertIsInstance(serialized, str)
        self.assertIn("function", serialized.lower())
    
    def test_empty_objects(self):
        """
        EXAMPLE: Handling empty or minimal objects.
        
        Shows behavior with edge case inputs.
        """
        class EmptyClass:
            pass
        
        empty_obj = EmptyClass()
        serialized = zc.serialize_object(empty_obj)
        
        # Should serialize to empty dict
        self.assertEqual(serialized, {})
        
        # Test with None
        self.assertIsNone(zc.serialize_object(None))
        
        # Test with empty containers
        self.assertEqual(zc.serialize_object([]), [])
        self.assertEqual(zc.serialize_object({}), {})


class TestPerformance(unittest.TestCase):
    """
    Basic performance tests.
    
    Shows that serialization works efficiently with larger datasets.
    """
    
    def setUp(self):
        zc.enable_universal_serialization()
    
    def tearDown(self):
        zc.disable_universal_serialization()
    
    def test_large_list_serialization(self):
        """
        EXAMPLE: Serializing large lists efficiently.
        
        Demonstrates performance with substantial data.
        """
        # Create large list with mixed types
        large_list = []
        for i in range(1000):
            large_list.append({
                'id': i,
                'timestamp': datetime(2024, 1, 15, i % 24, i % 60),
                'data': [j for j in range(i % 10)]
            })
        
        # Should complete without timeout
        import time
        start_time = time.time()
        serialized = zc.serialize_object(large_list)
        end_time = time.time()
        
        # Verify it worked
        self.assertEqual(len(serialized), 1000)
        self.assertLess(end_time - start_time, 5.0)  # Should complete in <5 seconds
    
    def test_deep_nesting_serialization(self):
        """
        EXAMPLE: Handling deeply nested structures.
        
        Shows recursive serialization works with reasonable depth.
        """
        # Create nested structure
        nested = {"level": 0}
        current = nested
        
        for i in range(1, 50):  # 50 levels deep
            current["next"] = {"level": i}
            current = current["next"]
        
        # Should handle reasonable nesting depth
        serialized = zc.serialize_object(nested)
        self.assertEqual(serialized["level"], 0)
        self.assertEqual(serialized["next"]["level"], 1)
        

def test_zarrwlr_scenario():
    """
    Test the original zarrwlr problem is solved.
    
    This test verifies that tuple types are preserved when storing
    and retrieving metadata from Zarr arrays, eliminating the need
    for manual type conversion workarounds.
    """
    import tempfile
    import zarr
    import zarrcompatibility as zc
    
    # Enable universal serialization (with automatic tuple preservation)
    zc.enable_universal_serialization()
    
    # Simulate zarrwlr Config class
    class Config:
        original_audio_group_version = (1, 0)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Zarr group with tuple metadata
        audio_group = zarr.open_group(f"{tmpdir}/audio.zarr", mode="w")
        audio_group.attrs["version"] = Config.original_audio_group_version
        
        # Reload and test - should work without manual conversion
        reloaded = zarr.open_group(f"{tmpdir}/audio.zarr", mode="r")
        stored_version = reloaded.attrs["version"]
        
        # These assertions should now pass without workarounds
        assert isinstance(stored_version, tuple), f"Expected tuple, got {type(stored_version)}"
        assert stored_version == Config.original_audio_group_version
        
        # Test the comparison that was failing before
        if stored_version == Config.original_audio_group_version:
            print("✓ Version matches - no manual conversion needed!")
        else:
            raise AssertionError("Version comparison failed")
    
    print("✓ zarrwlr scenario test passed - tuple preservation working!")


def test_basic_tuple_roundtrip():
    """Test basic tuple serialization and deserialization."""
    import json
    import zarrcompatibility as zc
    
    zc.enable_universal_serialization()
    
    # Test simple tuple
    original = (1, 0)
    serialized = json.dumps(original)
    deserialized = json.loads(serialized)
    
    assert isinstance(deserialized, tuple), f"Expected tuple, got {type(deserialized)}"
    assert deserialized == original
    print(f"✓ Basic tuple test: {original} -> {serialized} -> {deserialized}")
    
    # Test nested structure
    data = {
        "version": (1, 0),
        "coordinates": (10.5, 20.3),
        "items": [1, 2, 3]  # Should remain list
    }
    
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)
    
    assert isinstance(deserialized["version"], tuple)
    assert isinstance(deserialized["coordinates"], tuple)
    assert isinstance(deserialized["items"], list)
    print("✓ Nested structure test passed")

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
    test_basic_tuple_roundtrip()
    test_zarrwlr_scenario()
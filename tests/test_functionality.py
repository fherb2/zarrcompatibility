#!/usr/bin/env python3
"""
Functionality tests for zarrcompatibility v2.1.

This test module verifies that zarrcompatibility correctly enhances Zarr
operations while preserving all expected functionality. These tests focus
on end-to-end Zarr workflows to ensure tuple preservation and type support
work correctly in real usage scenarios.

Test Categories:
    1. Zarr tuple preservation (main feature)
    2. Zarr complex type support
    3. Zarr metadata roundtrip testing
    4. Zarr v3 specific functionality
    5. Edge cases and error handling

The tests can be run with pytest or directly from command line:
    python test_functionality.py -v

Author: F. Herbrand
License: MIT
"""

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, date, time
from enum import Enum
from uuid import uuid4, UUID
from dataclasses import dataclass
from decimal import Decimal

# Test framework setup
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    
try:
    import zarr
    ZARR_AVAILABLE = True
except ImportError:
    ZARR_AVAILABLE = False


class TestStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


@dataclass
class TestMetadata:
    name: str
    version: tuple
    created: datetime
    

class TestZarrTuplePreservation:
    """Test the main feature: tuple preservation in Zarr metadata."""
    
    def setup_method(self):
        """Setup for each test method."""
        if not ZARR_AVAILABLE:
            pytest.skip("Zarr not available")
        
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_simple_tuple_preservation(self):
        """Test that simple tuples are preserved in Zarr group attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Zarr group
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store tuple in attributes
            test_tuple = (1, 2, 3)
            group.attrs["version"] = test_tuple
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            stored_version = reloaded_group.attrs["version"]
            
            # Verify tuple is preserved
            assert stored_version == test_tuple
            assert isinstance(stored_version, tuple)
            assert type(stored_version) is tuple
    
    def test_nested_tuple_preservation(self):
        """Test that nested tuples are preserved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Zarr group
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store nested tuple structure
            nested_data = {
                "shape": (100, 200, 300),
                "chunks": (10, 20, 30),
                "coordinates": ((0, 0), (1, 1), (2, 2)),
                "metadata": {
                    "version": (2, 1, 0),
                    "dimensions": ("x", "y", "z")
                }
            }
            
            group.attrs.update(nested_data)
            group.store.close()
            
            # Reload and verify all tuples preserved
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            assert attrs["shape"] == (100, 200, 300)
            assert isinstance(attrs["shape"], tuple)
            
            assert attrs["chunks"] == (10, 20, 30)
            assert isinstance(attrs["chunks"], tuple)
            
            assert attrs["coordinates"] == ((0, 0), (1, 1), (2, 2))
            assert all(isinstance(coord, tuple) for coord in attrs["coordinates"])
            
            assert attrs["metadata"]["version"] == (2, 1, 0)
            assert isinstance(attrs["metadata"]["version"], tuple)
            
            assert attrs["metadata"]["dimensions"] == ("x", "y", "z")
            assert isinstance(attrs["metadata"]["dimensions"], tuple)
    
    def test_array_attribute_tuple_preservation(self):
        """Test tuple preservation in array attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Zarr array
            arr = zarr.open_array(f"{tmpdir}/test_array.zarr", mode="w", 
                                 shape=(10, 10), dtype="f4")
            
            # Store tuple in array attributes
            arr.attrs["shape_info"] = (10, 10)
            arr.attrs["processing_steps"] = ("normalize", "filter", "analyze")
            
            # Close and reopen
            arr.store.close()
            reloaded_arr = zarr.open_array(f"{tmpdir}/test_array.zarr", mode="r")
            
            # Verify tuples preserved
            assert reloaded_arr.attrs["shape_info"] == (10, 10)
            assert isinstance(reloaded_arr.attrs["shape_info"], tuple)
            
            assert reloaded_arr.attrs["processing_steps"] == ("normalize", "filter", "analyze")
            assert isinstance(reloaded_arr.attrs["processing_steps"], tuple)
    
    def test_mixed_types_with_tuples(self):
        """Test tuples mixed with other types work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Mix of types including tuples
            mixed_data = {
                "tuple_data": (1, 2, 3),
                "list_data": [4, 5, 6], 
                "dict_data": {"nested": (7, 8)},
                "string_data": "test",
                "number_data": 42,
                "bool_data": True,
                "none_data": None
            }
            
            group.attrs.update(mixed_data)
            group.store.close()
            
            # Reload and verify types
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            assert attrs["tuple_data"] == (1, 2, 3)
            assert isinstance(attrs["tuple_data"], tuple)
            
            assert attrs["list_data"] == [4, 5, 6]
            assert isinstance(attrs["list_data"], list)
            
            assert attrs["dict_data"]["nested"] == (7, 8)
            assert isinstance(attrs["dict_data"]["nested"], tuple)
            
            assert attrs["string_data"] == "test"
            assert isinstance(attrs["string_data"], str)
            
            assert attrs["number_data"] == 42
            assert isinstance(attrs["number_data"], int)
            
            assert attrs["bool_data"] is True
            assert isinstance(attrs["bool_data"], bool)
            
            assert attrs["none_data"] is None


class TestZarrComplexTypes:
    """Test support for complex types in Zarr metadata."""
    
    def setup_method(self):
        """Setup for each test method."""
        if not ZARR_AVAILABLE:
            pytest.skip("Zarr not available")
            
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_datetime_preservation(self):
        """Test datetime objects in Zarr metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store datetime objects
            now = datetime(2025, 1, 19, 12, 30, 45)
            today = date(2025, 1, 19)
            current_time = time(12, 30, 45)
            
            group.attrs["created"] = now
            group.attrs["date_only"] = today
            group.attrs["time_only"] = current_time
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            assert attrs["created"] == now
            assert isinstance(attrs["created"], datetime)
            
            assert attrs["date_only"] == today
            assert isinstance(attrs["date_only"], date)
            
            assert attrs["time_only"] == current_time
            assert isinstance(attrs["time_only"], time)
    
    def test_enum_preservation(self):
        """Test enum objects in Zarr metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store enum
            group.attrs["status"] = TestStatus.ACTIVE
            group.attrs["states"] = [TestStatus.ACTIVE, TestStatus.PENDING]
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            assert attrs["status"] == TestStatus.ACTIVE
            assert isinstance(attrs["status"], TestStatus)
            
            assert attrs["states"] == [TestStatus.ACTIVE, TestStatus.PENDING]
            assert all(isinstance(state, TestStatus) for state in attrs["states"])
    
    def test_uuid_preservation(self):
        """Test UUID objects in Zarr metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store UUID
            test_uuid = uuid4()
            group.attrs["id"] = test_uuid
            group.attrs["related_ids"] = [uuid4(), uuid4()]
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            assert attrs["id"] == test_uuid
            assert isinstance(attrs["id"], UUID)
            
            assert len(attrs["related_ids"]) == 2
            assert all(isinstance(uid, UUID) for uid in attrs["related_ids"])
    
    def test_dataclass_preservation(self):
        """Test dataclass objects in Zarr metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store dataclass
            metadata = TestMetadata(
                name="test_experiment",
                version=(1, 0, 0),
                created=datetime(2025, 1, 19, 12, 0)
            )
            group.attrs["metadata"] = metadata
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            stored_metadata = reloaded_group.attrs["metadata"]
            
            assert isinstance(stored_metadata, TestMetadata)
            assert stored_metadata.name == "test_experiment"
            assert stored_metadata.version == (1, 0, 0)
            assert isinstance(stored_metadata.version, tuple)
            assert stored_metadata.created == datetime(2025, 1, 19, 12, 0)
            assert isinstance(stored_metadata.created, datetime)
    
    def test_complex_numbers(self):
        """Test complex number support."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store complex numbers
            group.attrs["impedance"] = 3 + 4j
            group.attrs["frequency_response"] = [1+0j, 0.5+0.5j, 0+1j]
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            assert attrs["impedance"] == 3 + 4j
            assert isinstance(attrs["impedance"], complex)
            
            expected_response = [1+0j, 0.5+0.5j, 0+1j]
            assert attrs["frequency_response"] == expected_response
            assert all(isinstance(c, complex) for c in attrs["frequency_response"])
    
    def test_bytes_and_decimal(self):
        """Test bytes and Decimal support."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store bytes and decimal
            group.attrs["binary_data"] = b"test binary data"
            group.attrs["precision_value"] = Decimal("123.456789")
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            assert attrs["binary_data"] == b"test binary data"
            assert isinstance(attrs["binary_data"], bytes)
            
            assert attrs["precision_value"] == Decimal("123.456789")
            assert isinstance(attrs["precision_value"], Decimal)


class TestZarrMetadataRoundtrip:
    """Test complete metadata roundtrip scenarios."""
    
    def setup_method(self):
        """Setup for each test method."""
        if not ZARR_AVAILABLE:
            pytest.skip("Zarr not available")
            
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_comprehensive_metadata_roundtrip(self):
        """Test roundtrip of comprehensive metadata with all supported types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Comprehensive metadata with all types
            comprehensive_metadata = {
                # Basic types
                "string": "test_string",
                "integer": 42,
                "float": 3.14159,
                "boolean": True,
                "none_value": None,
                
                # Collections
                "list": [1, 2, 3],
                "tuple": (4, 5, 6),
                "set": {7, 8, 9},
                "dict": {"nested": "value"},
                
                # Complex types
                "datetime": datetime(2025, 1, 19, 15, 30),
                "date": date(2025, 1, 19),
                "time": time(15, 30, 45),
                "uuid": uuid4(),
                "enum": TestStatus.ACTIVE,
                "complex": 2 + 3j,
                "decimal": Decimal("999.999"),
                "bytes": b"binary_data",
                
                # Nested structures
                "nested_tuples": ((1, 2), (3, 4), (5, 6)),
                "mixed_list": [1, (2, 3), {"key": (4, 5)}],
                "complex_dict": {
                    "version": (1, 0, 0),
                    "created": datetime.now(),
                    "status": TestStatus.PENDING,
                    "config": {
                        "dimensions": (100, 200, 300),
                        "chunk_size": (10, 20, 30)
                    }
                }
            }
            
            # Store all metadata
            group.attrs.update(comprehensive_metadata)
            group.store.close()
            
            # Reload and verify everything
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            attrs = reloaded_group.attrs
            
            # Verify basic types
            assert attrs["string"] == "test_string"
            assert attrs["integer"] == 42
            assert attrs["float"] == 3.14159
            assert attrs["boolean"] is True
            assert attrs["none_value"] is None
            
            # Verify collections with type preservation
            assert attrs["list"] == [1, 2, 3]
            assert isinstance(attrs["list"], list)
            
            assert attrs["tuple"] == (4, 5, 6)
            assert isinstance(attrs["tuple"], tuple)
            
            assert attrs["set"] == {7, 8, 9}
            assert isinstance(attrs["set"], set)
            
            # Verify complex types
            assert isinstance(attrs["datetime"], datetime)
            assert isinstance(attrs["date"], date)
            assert isinstance(attrs["time"], time)
            assert isinstance(attrs["uuid"], UUID)
            assert isinstance(attrs["enum"], TestStatus)
            assert isinstance(attrs["complex"], complex)
            assert isinstance(attrs["decimal"], Decimal)
            assert isinstance(attrs["bytes"], bytes)
            
            # Verify nested structures
            assert attrs["nested_tuples"] == ((1, 2), (3, 4), (5, 6))
            assert all(isinstance(t, tuple) for t in attrs["nested_tuples"])
            
            assert attrs["mixed_list"][1] == (2, 3)
            assert isinstance(attrs["mixed_list"][1], tuple)
            assert attrs["mixed_list"][2]["key"] == (4, 5)
            assert isinstance(attrs["mixed_list"][2]["key"], tuple)
            
            # Verify complex nested dict
            config = attrs["complex_dict"]
            assert config["version"] == (1, 0, 0)
            assert isinstance(config["version"], tuple)
            assert isinstance(config["created"], datetime)
            assert isinstance(config["status"], TestStatus)
            assert config["config"]["dimensions"] == (100, 200, 300)
            assert isinstance(config["config"]["dimensions"], tuple)
    
    def test_multiple_group_independence(self):
        """Test that multiple groups maintain independent metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple groups with different metadata
            group1 = zarr.open_group(f"{tmpdir}/group1.zarr", mode="w")
            group2 = zarr.open_group(f"{tmpdir}/group2.zarr", mode="w")
            
            group1.attrs["version"] = (1, 0, 0)
            group1.attrs["status"] = TestStatus.ACTIVE
            
            group2.attrs["version"] = (2, 1, 0)
            group2.attrs["status"] = TestStatus.PENDING
            
            group1.store.close()
            group2.store.close()
            
            # Reload and verify independence
            reloaded1 = zarr.open_group(f"{tmpdir}/group1.zarr", mode="r")
            reloaded2 = zarr.open_group(f"{tmpdir}/group2.zarr", mode="r")
            
            assert reloaded1.attrs["version"] == (1, 0, 0)
            assert reloaded1.attrs["status"] == TestStatus.ACTIVE
            
            assert reloaded2.attrs["version"] == (2, 1, 0)
            assert reloaded2.attrs["status"] == TestStatus.PENDING
            
            # Verify types preserved independently
            assert isinstance(reloaded1.attrs["version"], tuple)
            assert isinstance(reloaded2.attrs["version"], tuple)
            assert isinstance(reloaded1.attrs["status"], TestStatus)
            assert isinstance(reloaded2.attrs["status"], TestStatus)


class TestZarrV3Specific:
    """Test Zarr v3 specific functionality."""
    
    def setup_method(self):
        """Setup for each test method.""" 
        if not ZARR_AVAILABLE:
            pytest.skip("Zarr not available")
            
        # Check if we have Zarr v3
        import zarr
        if not hasattr(zarr, '__version__') or not zarr.__version__.startswith('3'):
            pytest.skip("Zarr v3 not available")
            
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_zarr_v3_group_hierarchy(self):
        """Test tuple preservation in Zarr v3 group hierarchies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested group structure
            root = zarr.open_group(f"{tmpdir}/hierarchy.zarr", mode="w")
            
            # Add metadata to root
            root.attrs["root_version"] = (1, 0, 0)
            
            # Create subgroups
            subgroup1 = root.create_group("experiments")
            subgroup1.attrs["experiment_ids"] = (101, 102, 103)
            
            subgroup2 = subgroup1.create_group("trial_001")
            subgroup2.attrs["parameters"] = {
                "dimensions": (50, 100, 150),
                "sampling_rate": (1000, 2000)
            }
            
            root.store.close()
            
            # Reload and verify hierarchy
            reloaded_root = zarr.open_group(f"{tmpdir}/hierarchy.zarr", mode="r")
            
            assert reloaded_root.attrs["root_version"] == (1, 0, 0)
            assert isinstance(reloaded_root.attrs["root_version"], tuple)
            
            reloaded_exp = reloaded_root["experiments"]
            assert reloaded_exp.attrs["experiment_ids"] == (101, 102, 103)
            assert isinstance(reloaded_exp.attrs["experiment_ids"], tuple)
            
            reloaded_trial = reloaded_exp["trial_001"]
            params = reloaded_trial.attrs["parameters"]
            assert params["dimensions"] == (50, 100, 150)
            assert isinstance(params["dimensions"], tuple)
            assert params["sampling_rate"] == (1000, 2000)
            assert isinstance(params["sampling_rate"], tuple)
    
    def test_zarr_v3_array_metadata_integration(self):
        """Test integration with Zarr v3 array metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create array with enhanced metadata
            arr = zarr.open_array(f"{tmpdir}/array.zarr", mode="w",
                                 shape=(100, 200), chunks=(10, 20), dtype="f4")
            
            # Add metadata that includes tuples
            arr.attrs["original_shape"] = (1000, 2000)
            arr.attrs["processing_chain"] = [
                {"operation": "resize", "from": (1000, 2000), "to": (100, 200)},
                {"operation": "normalize", "range": (0.0, 1.0)}
            ]
            arr.attrs["created"] = datetime.now()
            
            arr.store.close()
            
            # Reload and verify
            reloaded_arr = zarr.open_array(f"{tmpdir}/array.zarr", mode="r")
            
            assert reloaded_arr.attrs["original_shape"] == (1000, 2000)
            assert isinstance(reloaded_arr.attrs["original_shape"], tuple)
            
            chain = reloaded_arr.attrs["processing_chain"]
            assert chain[0]["from"] == (1000, 2000)
            assert isinstance(chain[0]["from"], tuple)
            assert chain[0]["to"] == (100, 200)
            assert isinstance(chain[0]["to"], tuple)
            assert chain[1]["range"] == (0.0, 1.0)
            assert isinstance(chain[1]["range"], tuple)
            
            assert isinstance(reloaded_arr.attrs["created"], datetime)


class TestEdgeCasesAndErrors:
    """Test edge cases and error handling."""
    
    def setup_method(self):
        """Setup for each test method."""
        if not ZARR_AVAILABLE:
            pytest.skip("Zarr not available")
            
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_empty_tuple_preservation(self):
        """Test empty tuple preservation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store empty tuple
            group.attrs["empty"] = ()
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            assert reloaded_group.attrs["empty"] == ()
            assert isinstance(reloaded_group.attrs["empty"], tuple)
    
    def test_single_element_tuple_preservation(self):
        """Test single-element tuple preservation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Store single-element tuple (tricky case)
            group.attrs["single"] = (42,)
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            assert reloaded_group.attrs["single"] == (42,)
            assert isinstance(reloaded_group.attrs["single"], tuple)
            assert len(reloaded_group.attrs["single"]) == 1
    
    def test_deeply_nested_structures(self):
        """Test deeply nested structures with tuples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Create deeply nested structure
            deep_structure = {
                "level1": {
                    "level2": {
                        "level3": {
                            "coordinates": (1, 2, 3),
                            "nested_tuples": ((4, 5), (6, 7), (8, 9))
                        }
                    }
                }
            }
            
            group.attrs["deep"] = deep_structure
            group.store.close()
            
            # Reload and verify deep nesting preserved
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            deep = reloaded_group.attrs["deep"]
            
            coords = deep["level1"]["level2"]["level3"]["coordinates"]
            assert coords == (1, 2, 3)
            assert isinstance(coords, tuple)
            
            nested = deep["level1"]["level2"]["level3"]["nested_tuples"]
            assert nested == ((4, 5), (6, 7), (8, 9))
            assert all(isinstance(t, tuple) for t in nested)
    
    def test_large_tuple_handling(self):
        """Test handling of large tuples."""
        with tempfile.TemporaryDirectory() as tmpdir:
            group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
            
            # Create large tuple
            large_tuple = tuple(range(1000))
            group.attrs["large"] = large_tuple
            group.store.close()
            
            # Reload and verify
            reloaded_group = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
            stored_large = reloaded_group.attrs["large"]
            
            assert stored_large == large_tuple
            assert isinstance(stored_large, tuple)
            assert len(stored_large) == 1000


# Utility functions for standalone execution
def run_test_function(test_func, verbose=False):
    """Run a single test function with error handling."""
    try:
        if verbose:
            print(f"Running {test_func.__name__}...")
        
        test_func()
        
        if verbose:
            print(f"✅ {test_func.__name__} passed")
        return True
    except Exception as e:
        if verbose:
            print(f"❌ {test_func.__name__} failed: {e}")
        return False


def run_test_class(test_class, verbose=False):
    """Run all tests in a test class."""
    instance = test_class()
    passed = 0
    total = 0
    
    # Run setup if available
    if hasattr(instance, 'setup_method'):
        try:
            instance.setup_method()
        except Exception as e:
            if verbose:
                print(f"⚠️  Setup failed for {test_class.__name__}: {e}")
            return 0, 0
    
    for attr_name in dir(instance):
        if attr_name.startswith('test_'):
            total += 1
            test_method = getattr(instance, attr_name)
            
            # Run individual test setup if needed
            if hasattr(instance, 'setup_method'):
                try:
                    instance.setup_method()
                except:
                    pass
            
            if run_test_function(test_method, verbose):
                passed += 1
            
            # Run individual test teardown if needed
            if hasattr(instance, 'teardown_method'):
                try:
                    instance.teardown_method()
                except:
                    pass
    
    # Run teardown if available
    if hasattr(instance, 'teardown_method'):
        try:
            instance.teardown_method()
        except:
            pass
    
    return passed, total


def main():
    """Main function for standalone execution."""
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    print("🧪 zarrcompatibility v2.1 - Functionality Tests")
    print("=" * 50)
    
    if not ZARR_AVAILABLE:
        print("❌ Zarr not available. Install with: pip install zarr>=3.0.0")
        return 1
    
    print("Testing Zarr integration and tuple preservation...")
    print()
    
    test_classes = [
        TestZarrTuplePreservation,
        TestZarrComplexTypes,
        TestZarrMetadataRoundtrip,
        TestZarrV3Specific,
        TestEdgeCasesAndErrors,
    ]
    
    total_passed = 0
    total_tests = 0
    
    for test_class in test_classes:
        if verbose:
            print(f"📋 Running {test_class.__name__}...")
        
        passed, tests = run_test_class(test_class, verbose)
        total_passed += passed
        total_tests += tests
        
        if verbose:
            print(f"   {passed}/{tests} tests passed")
            print()
    
    print(f"📊 Overall Results: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 All functionality tests passed! Zarr integration working perfectly.")
        return 0
    else:
        print("❌ Some tests failed. Zarr integration may have issues.")
        return 1


if __name__ == "__main__":
    # Support both direct execution and pytest
    if PYTEST_AVAILABLE and len(sys.argv) == 1:
        # Run with pytest if available and no command line args
        pytest.main([__file__, "-v"])
    else:
        # Run standalone
        sys.exit(main())
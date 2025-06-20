#!/usr/bin/env python3
"""
Functionality tests for zarrcompatibility v3.0.

UPDATED VERSION - Fixed paths and added tests for new Attributes patches.

This test module verifies that the core functionality of zarrcompatibility
works correctly across different scenarios and edge cases.

Test Categories:
    1. Basic tuple preservation (Memory Store vs File Store)
    2. Complex type serialization
    3. Nested structure handling
    4. Attributes patching verification
    5. Error conditions and edge cases

Author: F. Herbrand
License: MIT
"""

import json
import sys
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, date, time
from enum import Enum
from uuid import uuid4, UUID
from dataclasses import dataclass
from decimal import Decimal

# FIXED: Consistent path setup that works from any directory
def setup_project_paths():
    """Setup paths consistently regardless of execution directory."""
    current_dir = Path.cwd()
    
    # Find project root by looking for src directory
    project_root = current_dir
    while project_root != project_root.parent:
        if (project_root / 'src').exists():
            break
        project_root = project_root.parent
    else:
        # Fallback: assume we're in project root or tests
        if current_dir.name == 'tests':
            project_root = current_dir.parent
        else:
            project_root = current_dir
    
    src_path = project_root / 'src'
    tests_path = project_root / 'tests'
    testresults_path = tests_path / 'testresults'
    
    # Create testresults directory
    testresults_path.mkdir(parents=True, exist_ok=True)
    
    # Add src to path if not already there
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return {
        'project_root': project_root,
        'src_path': src_path,
        'tests_path': tests_path,
        'testresults_path': testresults_path
    }

# Setup paths
PATHS = setup_project_paths()
print(f"🔧 Functionality test paths:")
print(f"   Project root: {PATHS['project_root']}")
print(f"   Source path: {PATHS['src_path']}")
print(f"   Test results: {PATHS['testresults_path']}")

# Test framework setup
try:
    import zarr
    ZARR_AVAILABLE = True
    # Verify Zarr v3
    if not hasattr(zarr, '__version__') or not zarr.__version__.startswith('3'):
        print(f"⚠️ Warning: Zarr v{zarr.__version__} detected. Tests require Zarr v3.")
        ZARR_AVAILABLE = False
    else:
        print(f"✅ Zarr v{zarr.__version__} available")
except ImportError:
    ZARR_AVAILABLE = False
    print("❌ Zarr not available")

# Try to import our package
try:
    import zarrcompatibility as zc
    print(f"✅ zarrcompatibility v{zc.__version__} imported successfully")
except Exception as e:
    print(f"❌ Failed to import zarrcompatibility: {e}")
    ZARR_AVAILABLE = False


class MetricStatus(Enum):  # RENAMED from MetricStatus
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

@dataclass
class ExperimentMetadata:  # RENAMED from  ExperimentMetadata
    name: str
    version: tuple
    created: datetime


class TestBasicFunctionality:
    """Test basic functionality including new Attributes patches."""
    
    def setup_method(self):
        """Setup for each test method."""
        if not ZARR_AVAILABLE:
            print("⚠️ Skipping test - Zarr not available")
            return
        
        try:
            import zarrcompatibility as zc
            print("🔧 Enabling zarr serialization...")
            zc.enable_zarr_serialization()
            print("✅ Zarr serialization enabled")
        except Exception as e:
            print(f"❌ Failed to enable zarr serialization: {e}")
            raise
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            try:
                import zarrcompatibility as zc
                zc.disable_zarr_serialization()
                print("🔧 Zarr serialization disabled")
            except Exception as e:
                print(f"⚠️ Warning during teardown: {e}")
    
    def test_patch_status_verification(self):
        """NEW: Test that all expected patches are active."""
        import zarrcompatibility as zc
        from zarrcompatibility import zarr_patching
        
        patch_status = zarr_patching.get_patch_status()
        
        # Verify all expected patches are active
        expected_patches = {
            'V3JsonEncoder': True,
            'Attributes.__setitem__': True,
            'Attributes.__getitem__': True,
            'GroupMetadata.from_dict': True,
            'GroupMetadata.to_buffer_dict': True,
            'ArrayV3Metadata.from_dict': True
        }
        
        for patch_name, expected_status in expected_patches.items():
            actual_status = patch_status.get(patch_name, False)
            assert actual_status == expected_status, f"Patch {patch_name}: expected {expected_status}, got {actual_status}"
            print(f"✅ Patch {patch_name}: {actual_status}")
        
        print("✅ All expected patches verified")
    
    def test_memory_store_tuple_preservation(self):
        """Test tuple preservation in memory store (tests Attributes.__getitem__ patch)."""
        if not ZARR_AVAILABLE:
            print("⚠️ Skipping - Zarr not available")
            return
            
        import zarr
        
        # Use memory storage (this should trigger Attributes.__getitem__)
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        # Test various tuples
        test_tuples = {
            "simple": (1, 2, 3),
            "nested": ((1, 2), (3, 4)),
            "mixed": (1, "hello", 3.14),
            "coordinates": (100.5, 200.3, 50.1),
            "empty": (),
            "single": (42,)
        }
        
        # Store tuples (triggers Attributes.__setitem__)
        for key, test_tuple in test_tuples.items():
            group.attrs[key] = test_tuple
            print(f"📝 Stored {key}: {test_tuple}")
        
        # Retrieve tuples (triggers Attributes.__getitem__)
        for key, original_tuple in test_tuples.items():
            retrieved = group.attrs[key]
            print(f"📖 Retrieved {key}: {retrieved} (type: {type(retrieved)})")
            
            assert retrieved == original_tuple, f"Value mismatch for {key}: {retrieved} != {original_tuple}"
            assert isinstance(retrieved, tuple), f"Type mismatch for {key}: {type(retrieved)} != tuple"
        
        print("✅ Memory store tuple preservation test passed")
    
    def test_file_store_tuple_preservation(self):
        """Test tuple preservation in file store (tests GroupMetadata.from_dict patch)."""
        if not ZARR_AVAILABLE:
            print("⚠️ Skipping - Zarr not available")
            return
            
        import zarr
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create zarr group with file storage
            group_path = Path(tmpdir) / "test_group.zarr"
            group = zarr.open_group(str(group_path), mode="w")
            
            # Test tuples
            test_tuples = {
                "version": (3, 0, 0),
                "coordinates": (100.5, 200.3, 50.1),
                "roi_bounds": (10, 20, 90, 180),
                "nested": ((1, 2), (3, 4), (5, 6))
            }
            
            # Store tuples
            for key, test_tuple in test_tuples.items():
                group.attrs[key] = test_tuple
                print(f"📝 Stored to file {key}: {test_tuple}")
            
            group.store.close()
            
            # Reload from file (triggers GroupMetadata.from_dict)
            reloaded_group = zarr.open_group(str(group_path), mode="r")
            
            # Verify tuples are preserved
            for key, original_tuple in test_tuples.items():
                retrieved = reloaded_group.attrs[key]
                print(f"📖 Loaded from file {key}: {retrieved} (type: {type(retrieved)})")
                
                assert retrieved == original_tuple, f"File storage value mismatch for {key}"
                assert isinstance(retrieved, tuple), f"File storage type mismatch for {key}"
            
            print("✅ File store tuple preservation test passed")
    
    def test_complex_types_memory_store(self):
        """Test complex types in memory store."""
        if not ZARR_AVAILABLE:
            print("⚠️ Skipping - Zarr not available")
            return
            
        import zarr
        
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        # Test complex types
        test_data = {
            "datetime_obj": datetime(2025, 1, 19, 12, 0),
            "enum_value": MetricStatus.ACTIVE,
            "uuid_obj": uuid4(),
            "dataclass_obj": ExperimentMetadata("test", (3, 0, 0), datetime.now()),
            "complex_num": 1 + 2j,
            "decimal_num": Decimal("123.456"),
            "bytes_data": b"test data"
        }
        
        # Store all test data
        for key, value in test_data.items():
            group.attrs[key] = value
            print(f"📝 Stored {key}: {value} (type: {type(value)})")
        
        # Retrieve and verify
        for key, original_value in test_data.items():
            stored_value = group.attrs[key]
            print(f"📖 Retrieved {key}: {stored_value} (type: {type(stored_value)})")
            
            assert stored_value == original_value, f"Value mismatch for {key}"
            assert type(stored_value) == type(original_value), f"Type mismatch for {key}"
        
        print("✅ Complex types memory store test passed")
    
    def test_complex_types_file_store(self):
        """Test complex types in file store."""
        if not ZARR_AVAILABLE:
            print("⚠️ Skipping - Zarr not available")
            return
            
        import zarr
        
        with tempfile.TemporaryDirectory() as tmpdir:
            group_path = Path(tmpdir) / "complex_test.zarr"
            group = zarr.open_group(str(group_path), mode="w")
            
            # Test complex types
            test_data = {
                "datetime_obj": datetime(2025, 1, 19, 12, 0),
                "enum_value": MetricStatus.PENDING,
                "uuid_obj": uuid4(),
                "dataclass_obj": ExperimentMetadata("file_test", (1, 2, 3), datetime.now()),
                "complex_num": 3 + 4j,
                "decimal_num": Decimal("987.654"),
                "bytes_data": b"file test data"
            }
            
            # Store all test data
            for key, value in test_data.items():
                group.attrs[key] = value
                print(f"📝 Stored to file {key}: {value}")
            
            group.store.close()
            
            # Reload from file
            reloaded_group = zarr.open_group(str(group_path), mode="r")
            
            # Verify all data
            for key, original_value in test_data.items():
                stored_value = reloaded_group.attrs[key]
                print(f"📖 Loaded from file {key}: {stored_value} (type: {type(stored_value)})")
                
                assert stored_value == original_value, f"File storage value mismatch for {key}"
                assert type(stored_value) == type(original_value), f"File storage type mismatch for {key}"
            
            print("✅ Complex types file store test passed")
    
    def test_nested_structures(self):
        """Test deeply nested structures with mixed types."""
        if not ZARR_AVAILABLE:
            print("⚠️ Skipping - Zarr not available")
            return
            
        import zarr
        
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        # Create complex nested structure
        nested_data = {
            "experiment": {
                "version": (3, 0, 0),
                "created": datetime.now(),
                "status": MetricStatus.ACTIVE,
                "settings": {
                    "image_params": {
                        "dimensions": (1024, 1024, 100),
                        "pixel_size": (0.1, 0.1, 0.2),
                        "roi_list": [
                            (100, 200, 300, 400),
                            (500, 600, 700, 800),
                            (900, 1000, 1100, 1200)
                        ]
                    },
                    "acquisition": {
                        "timestamps": (0.0, 1.0, 2.0, 3.0),
                        "channels": ("DAPI", "GFP", "RFP"),
                        "laser_powers": (10.0, 25.0, 15.0)
                    }
                },
                "metadata": ExperimentMetadata("nested_test", (1, 0, 0), datetime.now())
            }
        }
        
        # Store nested data
        group.attrs["data"] = nested_data
        print("📝 Stored deeply nested structure")
        
        # Reload and verify
        loaded_data = group.attrs["data"]
        
        # Verify nested structure preservation
        exp = loaded_data["experiment"]
        
        # Check basic types
        assert exp["version"] == (3, 0, 0)
        assert isinstance(exp["version"], tuple)
        assert isinstance(exp["created"], datetime)
        assert exp["status"] == MetricStatus.ACTIVE
        assert isinstance(exp["status"], MetricStatus)
        assert isinstance(exp["metadata"],  ExperimentMetadata)
        
        # Check nested tuples
        img_params = exp["settings"]["image_params"]
        assert img_params["dimensions"] == (1024, 1024, 100)
        assert isinstance(img_params["dimensions"], tuple)
        assert img_params["pixel_size"] == (0.1, 0.1, 0.2)
        assert isinstance(img_params["pixel_size"], tuple)
        
        # Check list of tuples
        roi_list = img_params["roi_list"]
        assert len(roi_list) == 3
        for i, roi in enumerate(roi_list):
            expected = [(100, 200, 300, 400), (500, 600, 700, 800), (900, 1000, 1100, 1200)][i]
            assert roi == expected
            assert isinstance(roi, tuple)
        
        # Check acquisition tuples
        acq = exp["settings"]["acquisition"]
        assert acq["timestamps"] == (0.0, 1.0, 2.0, 3.0)
        assert isinstance(acq["timestamps"], tuple)
        assert acq["channels"] == ("DAPI", "GFP", "RFP")
        assert isinstance(acq["channels"], tuple)
        assert acq["laser_powers"] == (10.0, 25.0, 15.0)
        assert isinstance(acq["laser_powers"], tuple)
        
        print("✅ Nested structures test passed")


class TestAdvancedFunctionality:
    """Test advanced functionality and edge cases."""
    
    def setup_method(self):
        """Setup for each test method."""
        if not ZARR_AVAILABLE:
            return
        
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_attributes_patches_directly(self):
        """NEW: Test Attributes.__setitem__ and __getitem__ patches directly."""
        if not ZARR_AVAILABLE:
            return
            
        import zarr
        from zarr.core.attributes import Attributes
        
        # Verify patches are in place
        setitem_method = Attributes.__setitem__
        getitem_method = Attributes.__getitem__
        
        # Check that they're our enhanced versions (not originals)
        assert 'enhanced_attributes_setitem' in str(setitem_method), "Attributes.__setitem__ not patched!"
        assert 'enhanced_attributes_getitem' in str(getitem_method), "Attributes.__getitem__ not patched!"
        
        print("✅ Attributes patches verified")
        
        # Test the patches with a real Attributes object
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        # Test tuple
        test_tuple = (1, 2, 3)
        group.attrs["test"] = test_tuple  # Should trigger enhanced __setitem__
        result = group.attrs["test"]      # Should trigger enhanced __getitem__
        
        assert result == test_tuple
        assert isinstance(result, tuple)
        
        print("✅ Attributes patches functionality verified")
    
    def test_json_format_inspection(self):
        """Test that Enhanced JSON format is correctly stored."""
        if not ZARR_AVAILABLE:
            return
            
        import zarr
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            group_path = Path(tmpdir) / "format_test.zarr"
            group = zarr.open_group(str(group_path), mode="w")
            
            # Store tuple
            group.attrs["version"] = (3, 0, 0)
            group.store.close()
            
            # Read raw JSON file
            zarr_json_path = group_path / "zarr.json"
            with open(zarr_json_path, 'r') as f:
                raw_content = f.read()
            
            print(f"📄 Raw zarr.json content: {raw_content}")
            
            # Parse and verify Enhanced format
            data = json.loads(raw_content)
            version_attr = data['attributes']['version']
            
            assert isinstance(version_attr, dict), "Version should be Enhanced JSON dict!"
            assert version_attr.get('__type__') == 'tuple', "Should have tuple type marker!"
            assert version_attr.get('__data__') == [3, 0, 0], "Should have tuple data!"
            
            print("✅ Enhanced JSON format verification passed")
    
    def test_version_and_compatibility_info(self):
        """Test version information and compatibility functions."""
        import zarrcompatibility as zc
        
        # Test version info
        versions = zc.get_supported_zarr_versions()
        assert isinstance(versions, dict)
        assert "min_version" in versions
        assert "max_tested" in versions
        assert "recommended" in versions
        
        # Test serialization status
        assert zc.is_zarr_serialization_enabled()
        
        # FIXED: test_serialization() is designed for direct serialization, not Zarr context
        # Let's test with actual Zarr usage instead
        import zarr
        
        # Test tuple in actual Zarr context (which is what our system is designed for)
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        test_tuple = (1, 2, 3)
        group.attrs["test"] = test_tuple
        result = group.attrs["test"]
        
        assert result == test_tuple, "Zarr tuple preservation should work!"
        assert isinstance(result, tuple), "Zarr should preserve tuple type!"
        
        print(f"📋 Supported Zarr versions: {versions['min_version']} - {versions['max_tested']}")
        print(f"📋 Recommended: {versions['recommended']}")
        print("✅ Version and compatibility info test passed")
    
    def test_error_conditions(self):
        """Test error conditions and edge cases."""
        if not ZARR_AVAILABLE:
            return
            
        import zarr
        
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        # Test edge cases that should work
        edge_cases = {
            "empty_tuple": (),
            "single_item_tuple": (42,),
            "very_nested": (((1, 2), (3, 4)), ((5, 6), (7, 8))),
            "mixed_types": (1, "hello", 3.14, True, None),
            "none_value": None,
            "empty_dict": {},
            "empty_list": []
        }
        
        for key, value in edge_cases.items():
            group.attrs[key] = value
            retrieved = group.attrs[key]
            
            assert retrieved == value, f"Edge case {key} failed: {retrieved} != {value}"
            assert type(retrieved) == type(value), f"Edge case {key} type mismatch: {type(retrieved)} != {type(value)}"
            
            print(f"✅ Edge case {key}: {value} -> {retrieved}")
        
        print("✅ Error conditions and edge cases test passed")


class TestPerformanceAndCompatibility:
    """Test performance and compatibility aspects."""
    
    def setup_method(self):
        if not ZARR_AVAILABLE:
            return
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
    
    def teardown_method(self):
        if ZARR_AVAILABLE:
            import zarrcompatibility as zc
            zc.disable_zarr_serialization()
    
    def test_large_nested_structures(self):
        """Test with larger nested structures."""
        if not ZARR_AVAILABLE:
            return
            
        import zarr
        
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        # Create larger structure
        large_data = {
            "measurements": [
                {
                    "id": i,
                    "coordinates": (i * 10.0, i * 20.0, i * 30.0),
                    "timestamps": tuple(range(i, i + 5)),
                    "metadata": ExperimentMetadata(f"measurement_{i}", (1, 0, i), datetime.now())
                }
                for i in range(20)  # 20 measurements
            ]
        }
        
        # Store and retrieve
        group.attrs["large_data"] = large_data
        retrieved = group.attrs["large_data"]
        
        # Verify structure
        assert len(retrieved["measurements"]) == 20
        
        for i, measurement in enumerate(retrieved["measurements"]):
            assert measurement["coordinates"] == (i * 10.0, i * 20.0, i * 30.0)
            assert isinstance(measurement["coordinates"], tuple)
            assert measurement["timestamps"] == tuple(range(i, i + 5))
            assert isinstance(measurement["timestamps"], tuple)
            assert isinstance(measurement["metadata"],  ExperimentMetadata)
        
        print("✅ Large nested structures test passed")
    
    def test_multiple_groups_and_arrays(self):
        """Test with multiple groups and arrays."""
        if not ZARR_AVAILABLE:
            return
            
        import zarr
        import numpy as np
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create main group
            main_group = zarr.open_group(f"{tmpdir}/multi_test.zarr", mode="w")
            
            # Add main metadata with tuples
            main_group.attrs.update({
                "version": (3, 0, 0),
                "experiment_id": "MULTI_001",
                "created": datetime.now(),
                "status": MetricStatus.ACTIVE
            })
            
            # Create subgroups with metadata
            for i in range(3):
                subgroup = main_group.create_group(f"dataset_{i}")
                subgroup.attrs.update({
                    "index": i,
                    "dimensions": (100 + i * 10, 200 + i * 20),
                    "roi": (i * 50, i * 60, (i + 1) * 50, (i + 1) * 60),
                    "settings": ExperimentMetadata(f"dataset_{i}", (1, i, 0), datetime.now())
                })
                
                # Create small array with metadata
                arr = subgroup.create_array(
                    "data",
                    shape=(10, 10),
                    dtype="f4",
                    fill_value=0.0
                )
                arr.attrs.update({
                    "pixel_size": (0.1 * (i + 1), 0.1 * (i + 1)),
                    "calibration": (1.0, 0.0, 0.001 * i)
                })
                
                # Fill with test data
                test_data = np.random.random((10, 10)).astype('f4')
                arr[:] = test_data
            
            main_group.store.close()
            
            # Reload and verify all metadata
            reloaded = zarr.open_group(f"{tmpdir}/multi_test.zarr", mode="r")
            
            # Check main metadata
            assert reloaded.attrs["version"] == (3, 0, 0)
            assert isinstance(reloaded.attrs["version"], tuple)
            assert isinstance(reloaded.attrs["created"], datetime)
            assert reloaded.attrs["status"] == MetricStatus.ACTIVE
            
            # Check subgroups
            for i in range(3):
                subgroup = reloaded[f"dataset_{i}"]
                
                assert subgroup.attrs["dimensions"] == (100 + i * 10, 200 + i * 20)
                assert isinstance(subgroup.attrs["dimensions"], tuple)
                assert subgroup.attrs["roi"] == (i * 50, i * 60, (i + 1) * 50, (i + 1) * 60)
                assert isinstance(subgroup.attrs["roi"], tuple)
                assert isinstance(subgroup.attrs["settings"],  ExperimentMetadata)
                
                # Check array metadata
                arr = subgroup["data"]
                assert arr.attrs["pixel_size"] == (0.1 * (i + 1), 0.1 * (i + 1))
                assert isinstance(arr.attrs["pixel_size"], tuple)
                assert arr.attrs["calibration"] == (1.0, 0.0, 0.001 * i)
                assert isinstance(arr.attrs["calibration"], tuple)
            
            print("✅ Multiple groups and arrays test passed")


def run_all_functionality_tests() -> Dict[str, bool]:
    """Run all functionality tests and return results."""
    print("🧪 zarrcompatibility v3.0 - Functionality Tests (Updated)")
    print("=" * 60)
    
    if not ZARR_AVAILABLE:
        print("❌ Zarr not available - skipping all functionality tests")
        return {}
    
    # Test classes
    test_classes = [
        TestBasicFunctionality(),
        TestAdvancedFunctionality(),
        TestPerformanceAndCompatibility(),
    ]
    
    # Collect all test methods
    all_tests = []
    for test_instance in test_classes:
        methods = [getattr(test_instance, method) for method in dir(test_instance) 
                  if method.startswith('test_') and callable(getattr(test_instance, method))]
        all_tests.extend([(test_instance, method) for method in methods])
    
    # Run tests
    results = {}
    passed = 0
    
    for i, (test_instance, test_method) in enumerate(all_tests, 1):
        test_name = f"{test_instance.__class__.__name__}.{test_method.__name__}"
        print(f"\n🔍 Test {i}: {test_name}")
        
        try:
            test_instance.setup_method()
            test_method()
            test_instance.teardown_method()
            
            results[test_name] = True
            print(f"✅ Test {i} passed")
            passed += 1
            
        except Exception as e:
            results[test_name] = False
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                test_instance.teardown_method()
            except:
                pass
    
    print(f"\n📊 Functionality Results: {passed}/{len(all_tests)} tests passed")
    
    # Save detailed results
    results_file = PATHS['testresults_path'] / 'functionality_test_results.txt'
    with open(results_file, 'w') as f:
        f.write(f"zarrcompatibility v3.0 - Functionality Test Results\n")
        f.write(f"=" * 60 + "\n")
        f.write(f"Tests passed: {passed}/{len(all_tests)}\n")
        f.write(f"Success rate: {passed/len(all_tests)*100:.1f}%\n")
        f.write(f"Status: {'PASS' if passed == len(all_tests) else 'FAIL'}\n\n")
        
        f.write("Individual Test Results:\n")
        f.write("-" * 30 + "\n")
        for test_name, success in results.items():
            status = "PASS" if success else "FAIL"
            f.write(f"{status}: {test_name}\n")
    
    print(f"📁 Results saved to: {results_file}")
    
    return results


def main() -> int:
    """Main function for standalone execution."""
    print("🧪 zarrcompatibility v3.0 - Functionality Tests")
    print("=" * 50)
    
    # Check environment
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {Path.cwd()}")
    print()
    
    # Check if we can import our package
    try:
        import zarrcompatibility as zc
        print(f"✅ zarrcompatibility v{zc.__version__} imported")
    except Exception as e:
        print(f"❌ Failed to import zarrcompatibility: {e}")
        return 1
    
    # Check Zarr
    if not ZARR_AVAILABLE:
        print("❌ Zarr not available or incompatible version")
        return 1
    
    # Run all tests
    results = run_all_functionality_tests()
    
    if not results:
        print("❌ No tests were run")
        return 1
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    if success_count == total_count:
        print("\n🎉 All functionality tests passed!")
        print("   ✅ Basic tuple preservation (Memory + File)")
        print("   ✅ Complex type serialization") 
        print("   ✅ Nested structure handling")
        print("   ✅ Attributes patches verification")
        print("   ✅ Performance and compatibility")
        return 0
    else:
        print(f"\n❌ {total_count - success_count} functionality tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
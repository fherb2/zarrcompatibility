#!/usr/bin/env python3
"""
Isolation tests for zarrcompatibility v3.0.

UPDATED VERSION - Fixed for new Zarr-only patching approach.

Author: F. Herbrand  
License: MIT
"""

import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Callable, Tuple

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
print(f"🔧 Project paths:")
print(f"   Project root: {PATHS['project_root']}")
print(f"   Source path: {PATHS['src_path']}")
print(f"   Tests path: {PATHS['tests_path']}")
print(f"   Test results: {PATHS['testresults_path']}")


class TestGlobalJSONIsolation:
    """Test that global JSON module remains completely unaffected."""
    
    def test_global_json_functions_unchanged(self) -> None:
        """Verify global json.dumps and json.loads are not modified."""
        # Store original functions
        original_dumps = json.dumps
        original_loads = json.loads
        original_dumps_id = id(json.dumps)
        original_loads_id = id(json.loads)
        
        # Import and enable zarrcompatibility
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
        
        # Verify functions are still the same objects
        assert json.dumps is original_dumps, "json.dumps object was replaced!"
        assert json.loads is original_loads, "json.loads object was replaced!"
        assert id(json.dumps) == original_dumps_id, "json.dumps identity changed!"
        assert id(json.loads) == original_loads_id, "json.loads identity changed!"
        
        print("✅ Global JSON functions unchanged")
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_global_json_behavior_unchanged(self) -> None:
        """Verify global JSON behavior is exactly the same."""
        import zarrcompatibility as zc
        
        # Test data that would be affected by our enhancements
        test_cases: List[Any] = [
            (1, 2, 3),                    # Tuple -> should become list in global JSON
            {"nested": (4, 5)},           # Nested tuple
            [(6, 7), (8, 9)],            # List of tuples
            {"complex": {"tuple": (10, 11, 12)}},  # Deeply nested
        ]
        
        # Get behavior before enabling
        before_results: List[Tuple[str, Any, type]] = []
        for case in test_cases:
            json_str = json.dumps(case)
            loaded = json.loads(json_str)
            before_results.append((json_str, loaded, type(loaded)))
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        # Get behavior after enabling
        after_results: List[Tuple[str, Any, type]] = []
        for case in test_cases:
            json_str = json.dumps(case)
            loaded = json.loads(json_str)
            after_results.append((json_str, loaded, type(loaded)))
        
        # Verify identical behavior
        for i, (before, after) in enumerate(zip(before_results, after_results)):
            before_json, before_obj, before_type = before
            after_json, after_obj, after_type = after
            
            assert before_json == after_json, f"JSON output changed for case {i}: {test_cases[i]}"
            assert before_obj == after_obj, f"Loaded object changed for case {i}: {test_cases[i]}"
            assert before_type == after_type, f"Loaded type changed for case {i}: {test_cases[i]}"
        
        # Specifically verify tuples become lists (standard JSON behavior)
        tuple_json = json.dumps((1, 2, 3))
        tuple_loaded = json.loads(tuple_json)
        assert tuple_json == "[1, 2, 3]", "Tuple JSON serialization changed!"
        assert tuple_loaded == [1, 2, 3], "Tuple deserialization changed!"
        assert isinstance(tuple_loaded, list), "Tuple should become list in global JSON!"
        
        print("✅ Global JSON behavior unchanged")
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_enhanced_json_not_processed_globally(self) -> None:
        """UPDATED: Test that Enhanced JSON format is NOT processed by global json.loads."""
        import zarrcompatibility as zc
        
        # Enable zarrcompatibility (should NOT affect global JSON)
        zc.enable_zarr_serialization()
        
        try:
            # Enhanced JSON format that our Zarr handlers understand
            enhanced_json = '{"__type__": "tuple", "__data__": [1, 2, 3]}'
            
            # Global json.loads should NOT process this as a tuple
            result = json.loads(enhanced_json)
            
            # Should remain as dict (not converted to tuple)
            assert isinstance(result, dict), "Global JSON incorrectly processed Enhanced format!"
            assert result == {"__type__": "tuple", "__data__": [1, 2, 3]}, "Enhanced JSON not preserved as dict!"
            
            print("✅ Enhanced JSON format ignored by global JSON (correct behavior)")
            
        finally:
            zc.disable_zarr_serialization()


class TestZarrOnlyPatching:
    """Test that only Zarr is patched, not global systems."""
    
    def test_zarr_patches_active(self) -> None:
        """Test that Zarr patches are correctly applied."""
        import zarrcompatibility as zc
        
        # Enable patching
        zc.enable_zarr_serialization()
        
        try:
            # Check patch status
            from zarrcompatibility import zarr_patching
            patch_status = zarr_patching.get_patch_status()
            
            # Verify expected patches are active
            expected_patches = [
                'V3JsonEncoder',
                'Attributes.__setitem__',
                'Attributes.__getitem__',
                'GroupMetadata.from_dict',
                'GroupMetadata.to_buffer_dict'
            ]
            
            for patch_name in expected_patches:
                assert patch_status.get(patch_name, False), f"Patch {patch_name} not active!"
            
            print(f"✅ All expected Zarr patches active: {expected_patches}")
            
        finally:
            zc.disable_zarr_serialization()
    
    def test_zarr_functionality_vs_global_json(self) -> None:
        """Test that Zarr gets enhanced functionality while global JSON remains unchanged."""
        import zarrcompatibility as zc
        import zarr
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        try:
            # Test global JSON behavior (should be unaffected)
            test_tuple = (1, 2, 3)
            global_json = json.dumps(test_tuple)
            global_loaded = json.loads(global_json)
            
            assert global_json == "[1, 2, 3]", "Global JSON dumps changed!"
            assert global_loaded == [1, 2, 3], "Global JSON loads changed!"
            assert isinstance(global_loaded, list), "Global JSON should return list for tuples!"
            
            # Test Zarr behavior (should be enhanced)
            store = zarr.storage.MemoryStore()
            group = zarr.open_group(store=store, mode="w")
            group.attrs["version"] = test_tuple
            
            # Zarr should preserve tuple
            zarr_loaded = group.attrs["version"]
            assert zarr_loaded == (1, 2, 3), "Zarr tuple not preserved!"
            assert isinstance(zarr_loaded, tuple), "Zarr should return tuple!"
            
            print("✅ Global JSON unchanged, Zarr enhanced")
            
        finally:
            zc.disable_zarr_serialization()


class TestLibraryNonInterference:
    """Test that other libraries are completely unaffected."""
    
    def test_requests_simulation(self) -> None:
        """Simulate requests library usage (can't make real HTTP requests in tests)."""
        import zarrcompatibility as zc
        
        # Test data that would be problematic if requests were affected
        test_data = {"coordinates": (10, 20), "values": [1, 2, 3]}
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        try:
            # Simulate what requests would do (serialize with json.dumps)
            json_str = json.dumps(test_data)
            
            # Simulate server response parsing (with json.loads)
            parsed = json.loads(json_str)
            
            # Verify requests would see standard JSON behavior
            assert parsed["coordinates"] == [10, 20], "Requests would see modified JSON behavior!"
            assert isinstance(parsed["coordinates"], list), "Requests would see tuples preserved!"
            
            print("✅ Requests-like usage unaffected")
            
        finally:
            zc.disable_zarr_serialization()
    
    def test_any_library_json_usage(self) -> None:
        """Test that any library using standard JSON remains unaffected."""
        import zarrcompatibility as zc
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        try:
            # Simulate various library usage patterns
            config_data = {
                "version": (1, 0, 0),
                "settings": {
                    "coordinates": (100, 200),
                    "bounds": [(0, 0), (1920, 1080)]
                }
            }
            
            # Libraries would typically do this:
            # 1. Serialize config
            config_json = json.dumps(config_data)
            
            # 2. Save to file / send over network / etc.
            # 3. Load config
            loaded_config = json.loads(config_json)
            
            # Should follow standard JSON rules (tuples -> lists)
            assert loaded_config["version"] == [1, 0, 0], "Config version should be list!"
            assert isinstance(loaded_config["version"], list), "Config version should be list type!"
            assert loaded_config["settings"]["coordinates"] == [100, 200], "Coordinates should be list!"
            assert loaded_config["settings"]["bounds"] == [[0, 0], [1920, 1080]], "Bounds should be list of lists!"
            
            print("✅ Library JSON usage patterns unaffected")
            
        finally:
            zc.disable_zarr_serialization()


class TestImportOrderIndependence:
    """Test that import order doesn't matter."""
    
    def test_import_after_json_usage(self) -> None:
        """Test importing zarrcompatibility after using json."""
        # Use json first
        test_data = (1, 2, 3)
        json_before = json.dumps(test_data)
        
        # Now import and enable zarrcompatibility
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
        
        try:
            # JSON should still behave the same
            json_after = json.dumps(test_data)
            assert json_before == json_after, "JSON behavior changed after import!"
            
            print("✅ Import after JSON usage works")
            
        finally:
            zc.disable_zarr_serialization()
    
    def test_multiple_enable_disable_cycles(self) -> None:
        """Test multiple enable/disable cycles."""
        import zarrcompatibility as zc
        
        # Multiple cycles should be safe
        for cycle in range(3):
            print(f"🔄 Cycle {cycle + 1}")
            
            # Enable
            zc.enable_zarr_serialization()
            
            # Test basic functionality
            test_tuple = (1, 2, 3)
            global_result = json.dumps(test_tuple)
            assert global_result == "[1, 2, 3]", f"Cycle {cycle + 1}: JSON behavior changed!"
            
            # Disable
            zc.disable_zarr_serialization()
            
            # Should still work after disable
            global_result_after = json.dumps(test_tuple)
            assert global_result_after == "[1, 2, 3]", f"Cycle {cycle + 1}: JSON behavior changed after disable!"
        
        print("✅ Multiple enable/disable cycles work")


def run_all_isolation_tests() -> bool:
    """Run all isolation tests."""
    print("🧪 zarrcompatibility v3.0 - Isolation Tests (Updated)")
    print("=" * 60)
    
    test_classes = [
        TestGlobalJSONIsolation(),
        TestZarrOnlyPatching(),
        TestLibraryNonInterference(),
        TestImportOrderIndependence(),
    ]
    
    all_tests = []
    for test_instance in test_classes:
        methods = [getattr(test_instance, method) for method in dir(test_instance) 
                  if method.startswith('test_') and callable(getattr(test_instance, method))]
        all_tests.extend(methods)
    
    passed = 0
    for i, test_func in enumerate(all_tests, 1):
        test_name = f"{test_func.__self__.__class__.__name__}.{test_func.__name__}"
        print(f"\n🔍 Test {i}: {test_name}")
        try:
            test_func()
            print(f"✅ Test {i} passed")
            passed += 1
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Isolation Results: {passed}/{len(all_tests)} tests passed")
    
    # Save results
    results_file = PATHS['testresults_path'] / 'isolation_test_results.txt'
    with open(results_file, 'w') as f:
        f.write(f"zarrcompatibility v3.0 - Isolation Test Results\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Tests passed: {passed}/{len(all_tests)}\n")
        f.write(f"Success rate: {passed/len(all_tests)*100:.1f}%\n")
        f.write(f"Status: {'PASS' if passed == len(all_tests) else 'FAIL'}\n")
    
    print(f"📁 Results saved to: {results_file}")
    
    return passed == len(all_tests)


def main() -> int:
    """Main function for standalone execution."""
    print("🧪 zarrcompatibility v3.0 - Isolation Tests")
    print("=" * 50)
    
    # Check if we can import our package
    try:
        import zarrcompatibility as zc
        print(f"✅ zarrcompatibility v{zc.__version__} imported")
    except Exception as e:
        print(f"❌ Failed to import zarrcompatibility: {e}")
        return 1
    
    # Run all tests
    success = run_all_isolation_tests()
    
    if success:
        print("\n🎉 All isolation tests passed!")
        print("   ✅ Global JSON completely unaffected")
        print("   ✅ Other libraries completely unaffected") 
        print("   ✅ Import order independence confirmed")
        print("   ✅ Zarr-only patching verified")
        print("\n🏆 zarrcompatibility v3.0 delivers on its isolation promise!")
        return 0
    else:
        print("\n❌ Some isolation tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
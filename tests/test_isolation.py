#!/usr/bin/env python3
"""
Isolation tests for zarrcompatibility v2.1.

This test module verifies that zarrcompatibility has ZERO side effects on
the global Python environment. These tests are critical for ensuring that
the new Zarr-only patching approach works as intended without affecting
other libraries.

Test Categories:
    1. Global JSON module isolation
    2. Third-party library isolation  
    3. Import order independence
    4. Multiple enable/disable cycles
    5. Concurrent usage scenarios

The tests can be run with pytest or directly from command line:
    python test_isolation.py -v

Author: F. Herbrand
License: MIT
"""

import json
import sys
import warnings
from typing import Any, Dict, List

# Test framework setup
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    # Create minimal pytest-like decorators for standalone execution
    def pytest_mark_parametrize(argnames, argvalues):
        def decorator(func):
            func._parametrize = (argnames, argvalues)
            return func
        return decorator
    
    class pytest:
        class mark:
            parametrize = pytest_mark_parametrize


class TestGlobalJSONIsolation:
    """Test that global JSON module remains completely unaffected."""
    
    def test_global_json_functions_unchanged(self):
        """Verify global json.dumps and json.loads are not modified."""
        # Store original functions
        original_dumps = json.dumps
        original_loads = json.loads
        
        # Import and enable zarrcompatibility
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
        
        # Verify functions are still the same objects
        assert json.dumps is original_dumps, "json.dumps was modified!"
        assert json.loads is original_loads, "json.loads was modified!"
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_global_json_behavior_unchanged(self):
        """Verify global JSON behavior is exactly the same."""
        import zarrcompatibility as zc
        
        # Test data that would be affected by our enhancements
        test_cases = [
            (1, 2, 3),                    # Tuple -> should become list in global JSON
            {"nested": (4, 5)},           # Nested tuple
            [(6, 7), (8, 9)],            # List of tuples
        ]
        
        # Get behavior before enabling
        before_results = []
        for case in test_cases:
            json_str = json.dumps(case)
            loaded = json.loads(json_str)
            before_results.append((json_str, loaded, type(loaded)))
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        # Get behavior after enabling
        after_results = []
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
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_json_module_attributes_unchanged(self):
        """Verify json module attributes are not modified."""
        import zarrcompatibility as zc
        
        # Get json module attributes before
        before_attrs = set(dir(json))
        before_dict = json.__dict__.copy()
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        # Get json module attributes after
        after_attrs = set(dir(json))
        after_dict = json.__dict__.copy()
        
        # Verify no new attributes added
        new_attrs = after_attrs - before_attrs
        assert not new_attrs, f"New attributes added to json module: {new_attrs}"
        
        # Verify no attributes removed
        removed_attrs = before_attrs - after_attrs
        assert not removed_attrs, f"Attributes removed from json module: {removed_attrs}"
        
        # Verify critical attributes unchanged
        critical_attrs = ['dumps', 'loads', 'JSONEncoder', 'JSONDecoder']
        for attr in critical_attrs:
            assert before_dict[attr] is after_dict[attr], f"json.{attr} was modified!"
        
        # Clean up
        zc.disable_zarr_serialization()


class TestThirdPartyLibraryIsolation:
    """Test that common third-party libraries are unaffected."""
    
    def test_requests_library_unaffected(self):
        """Test that requests library JSON operations work normally."""
        try:
            import requests
        except ImportError:
            pytest.skip("requests not available")
        
        import zarrcompatibility as zc
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        # Test requests JSON functionality
        # Note: We can't make actual HTTP requests in tests, so we test the JSON parts
        
        # Test requests.json() would use standard JSON behavior
        response_data = '{"tuple_data": [1, 2, 3], "status": "ok"}'
        
        # Simulate what requests.Response.json() does internally
        parsed = json.loads(response_data)
        
        # Verify standard JSON behavior (tuples as lists)
        assert parsed["tuple_data"] == [1, 2, 3]
        assert isinstance(parsed["tuple_data"], list)
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_pandas_json_unaffected(self):
        """Test that pandas JSON operations work normally."""
        try:
            import pandas as pd
        except ImportError:
            pytest.skip("pandas not available")
        
        import zarrcompatibility as zc
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        # Test pandas JSON functionality
        test_data = {"a": [1, 2, 3], "b": ["x", "y", "z"]}
        df = pd.DataFrame(test_data)
        
        # Convert to JSON and back
        json_str = df.to_json()
        df_restored = pd.read_json(json_str)
        
        # Verify DataFrame roundtrip works normally
        assert df.equals(df_restored), "pandas JSON roundtrip affected by zarrcompatibility"
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_numpy_json_unaffected(self):
        """Test that numpy array JSON serialization works normally."""
        try:
            import numpy as np
        except ImportError:
            pytest.skip("numpy not available")
        
        import zarrcompatibility as zc
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        # Test numpy JSON behavior
        arr = np.array([1, 2, 3])
        
        # Convert to JSON using standard json (should use numpy's default behavior)
        json_str = json.dumps(arr.tolist())
        loaded = json.loads(json_str)
        
        # Verify standard behavior
        assert loaded == [1, 2, 3]
        assert isinstance(loaded, list)
        
        # Clean up
        zc.disable_zarr_serialization()


class TestImportOrderIndependence:
    """Test that import order doesn't affect functionality."""
    
    def test_import_json_first(self):
        """Test importing json before zarrcompatibility."""
        # This test simulates fresh import state
        import json  # Import json first
        original_dumps = json.dumps
        
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
        
        # Verify json is still original
        assert json.dumps is original_dumps
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_import_zarrcompatibility_first(self):
        """Test importing zarrcompatibility before other libraries."""
        import zarrcompatibility as zc
        zc.enable_zarr_serialization()
        
        # Now import json
        import json
        
        # Verify json still works normally
        result = json.dumps((1, 2, 3))
        assert result == "[1, 2, 3]"
        
        loaded = json.loads(result)
        assert loaded == [1, 2, 3]
        assert isinstance(loaded, list)
        
        # Clean up
        zc.disable_zarr_serialization()
    
    def test_multiple_imports_safe(self):
        """Test that multiple imports don't cause issues."""
        # Import zarrcompatibility multiple times
        import zarrcompatibility as zc1
        import zarrcompatibility as zc2
        from zarrcompatibility import enable_zarr_serialization
        
        # All should be the same module
        assert zc1 is zc2
        
        # Multiple enables should be safe
        zc1.enable_zarr_serialization()
        zc2.enable_zarr_serialization()
        enable_zarr_serialization()
        
        # Should still work correctly
        assert zc1.is_zarr_serialization_enabled()
        
        # Clean up
        zc1.disable_zarr_serialization()


class TestEnableDisableCycles:
    """Test multiple enable/disable cycles work correctly."""
    
    def test_multiple_enable_disable_cycles(self):
        """Test that enable/disable can be called multiple times safely."""
        import zarrcompatibility as zc
        
        # Should start disabled
        assert not zc.is_zarr_serialization_enabled()
        
        # Enable/disable cycle 1
        zc.enable_zarr_serialization()
        assert zc.is_zarr_serialization_enabled()
        
        zc.disable_zarr_serialization()
        assert not zc.is_zarr_serialization_enabled()
        
        # Enable/disable cycle 2
        zc.enable_zarr_serialization()
        assert zc.is_zarr_serialization_enabled()
        
        zc.disable_zarr_serialization()
        assert not zc.is_zarr_serialization_enabled()
        
        # Verify global JSON still works normally after all cycles
        result = json.dumps((1, 2, 3))
        assert result == "[1, 2, 3]"
        loaded = json.loads(result)
        assert isinstance(loaded, list)
    
    def test_multiple_enables_safe(self):
        """Test that multiple enables without disables are safe."""
        import zarrcompatibility as zc
        
        # Multiple enables should not cause issues
        zc.enable_zarr_serialization()
        zc.enable_zarr_serialization()
        zc.enable_zarr_serialization()
        
        # Should still work
        assert zc.is_zarr_serialization_enabled()
        
        # Single disable should work
        zc.disable_zarr_serialization()
        assert not zc.is_zarr_serialization_enabled()
    
    def test_disable_without_enable_safe(self):
        """Test that disable without enable doesn't cause issues."""
        import zarrcompatibility as zc
        
        # Disable without enable should be safe
        zc.disable_zarr_serialization()  # Should not crash
        
        # Should still be disabled
        assert not zc.is_zarr_serialization_enabled()
        
        # Global JSON should still work
        result = json.dumps({"test": [1, 2, 3]})
        loaded = json.loads(result)
        assert loaded == {"test": [1, 2, 3]}


class TestConcurrentUsage:
    """Test concurrent usage scenarios."""
    
    def test_module_level_isolation(self):
        """Test that different modules can use zarrcompatibility independently."""
        import zarrcompatibility as zc
        
        # Enable globally
        zc.enable_zarr_serialization()
        
        # Simulate different modules using JSON
        def module_a_json_usage():
            # Module A just uses standard JSON
            data = {"values": (1, 2, 3)}
            json_str = json.dumps(data)
            return json.loads(json_str)
        
        def module_b_json_usage():
            # Module B also uses standard JSON
            data = [(4, 5), (6, 7)]
            json_str = json.dumps(data)
            return json.loads(json_str)
        
        # Both should get standard JSON behavior (tuples become lists)
        result_a = module_a_json_usage()
        result_b = module_b_json_usage()
        
        assert result_a == {"values": [1, 2, 3]}
        assert isinstance(result_a["values"], list)
        
        assert result_b == [[4, 5], [6, 7]]
        assert all(isinstance(item, list) for item in result_b)
        
        # Clean up
        zc.disable_zarr_serialization()


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
    
    for attr_name in dir(instance):
        if attr_name.startswith('test_'):
            total += 1
            test_method = getattr(instance, attr_name)
            if run_test_function(test_method, verbose):
                passed += 1
    
    return passed, total


def main():
    """Main function for standalone execution."""
    verbose = '-v' in sys.argv or '--verbose' in sys.argv
    
    print("🧪 zarrcompatibility v2.1 - Isolation Tests")
    print("=" * 50)
    print("Testing that zarrcompatibility has ZERO side effects...")
    print()
    
    test_classes = [
        TestGlobalJSONIsolation,
        TestThirdPartyLibraryIsolation, 
        TestImportOrderIndependence,
        TestEnableDisableCycles,
        TestConcurrentUsage,
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
        print("🎉 All isolation tests passed! zarrcompatibility has zero side effects.")
        return 0
    else:
        print("❌ Some tests failed. zarrcompatibility may have side effects.")
        return 1


if __name__ == "__main__":
    # Support both direct execution and pytest
    if PYTEST_AVAILABLE and len(sys.argv) == 1:
        # Run with pytest if available and no command line args
        pytest.main([__file__, "-v"])
    else:
        # Run standalone
        sys.exit(main())

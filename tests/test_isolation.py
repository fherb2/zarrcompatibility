#!/usr/bin/env python3
"""
Isolation tests for zarrcompatibility v2.1.

FIXED VERSION - Corrected path handling and import issues.

Author: F. Herbrand  
License: MIT
"""

import json
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List

# FIXED: Correct path setup based on current working directory
current_dir = Path.cwd()
if current_dir.name == 'tests':
    # Running from tests/ directory
    src_path = current_dir.parent / 'src'
else:
    # Running from project root
    src_path = current_dir / 'src'

# Add src to path
sys.path.insert(0, str(src_path))

print(f"🔧 Debug Info (Isolation Tests):")
print(f"   Current directory: {current_dir}")
print(f"   Source path: {src_path}")
print(f"   Source exists: {src_path.exists()}")

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
        
        print("✅ Global JSON functions unchanged")
        
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
        
        print("✅ Global JSON behavior unchanged")
        
        # Clean up
        zc.disable_zarr_serialization()


def run_basic_isolation_tests():
    """Run basic isolation tests for debugging."""
    print("🧪 Basic Isolation Tests")
    print("-" * 30)
    
    test_instance = TestGlobalJSONIsolation()
    
    tests = [
        test_instance.test_global_json_functions_unchanged,
        test_instance.test_global_json_behavior_unchanged,
    ]
    
    passed = 0
    for i, test_func in enumerate(tests, 1):
        print(f"\n🔍 Test {i}: {test_func.__name__}")
        try:
            test_func()
            print(f"✅ Test {i} passed")
            passed += 1
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Isolation Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)


def main():
    """Main function for standalone execution."""
    print("🧪 zarrcompatibility v2.1 - Isolation Tests")
    print("=" * 50)
    
    # Check if we can import our package
    try:
        import zarrcompatibility as zc
        print(f"✅ zarrcompatibility v{zc.__version__} imported")
    except Exception as e:
        print(f"❌ Failed to import zarrcompatibility: {e}")
        return 1
    
    # Run basic tests
    if run_basic_isolation_tests():
        print("\n🎉 Basic isolation tests passed!")
        return 0
    else:
        print("\n❌ Some isolation tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
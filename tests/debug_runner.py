#!/usr/bin/env python3
"""
Quick debug test runner for zarrcompatibility v2.1.

This runner identifies and fixes common issues before running tests.

Usage:
    python debug_runner.py
"""

import sys
import os
from pathlib import Path


def setup_environment():
    """Setup the environment and check for issues."""
    print("🔧 Setting up test environment...")
    
    # Determine correct paths
    current_dir = Path.cwd()
    if current_dir.name == 'tests':
        src_path = current_dir.parent / 'src'
        project_root = current_dir.parent
    else:
        src_path = current_dir / 'src'
        project_root = current_dir
    
    print(f"📁 Current directory: {current_dir}")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Source path: {src_path}")
    
    # Check paths exist
    if not src_path.exists():
        print(f"❌ Source directory not found: {src_path}")
        return False
    
    if not (src_path / 'zarrcompatibility').exists():
        print(f"❌ zarrcompatibility package not found in: {src_path}")
        return False
    
    # Add to Python path
    sys.path.insert(0, str(src_path))
    print(f"✅ Added to Python path: {src_path}")
    
    return True


def check_dependencies():
    """Check required dependencies."""
    print("\n🔍 Checking dependencies...")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check zarrcompatibility import
    try:
        import zarrcompatibility as zc
        print(f"✅ zarrcompatibility v{zc.__version__}")
    except Exception as e:
        issues.append(f"Cannot import zarrcompatibility: {e}")
    
    # Check Zarr
    try:
        import zarr
        if zarr.__version__.startswith('3'):
            print(f"✅ Zarr v{zarr.__version__} (v3 ✓)")
        else:
            issues.append(f"Zarr v3 required, found v{zarr.__version__}")
    except ImportError:
        issues.append("Zarr not installed (pip install zarr>=3.0.0)")
    
    # Check numpy
    try:
        import numpy
        print(f"✅ NumPy v{numpy.__version__}")
    except ImportError:
        issues.append("NumPy not installed (pip install numpy)")
    
    if issues:
        print(f"\n❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    
    print("✅ All dependencies OK")
    return True


def run_basic_functionality_test():
    """Run a basic functionality test."""
    print("\n🧪 Running basic functionality test...")
    
    try:
        import zarrcompatibility as zc
        import zarr
        
        # Test basic enable/disable
        print("🔧 Testing enable/disable...")
        zc.enable_zarr_serialization()
        assert zc.is_zarr_serialization_enabled()
        
        zc.disable_zarr_serialization()
        assert not zc.is_zarr_serialization_enabled()
        
        print("✅ Enable/disable works")
        
        # Test basic tuple preservation
        print("🔧 Testing tuple preservation...")
        zc.enable_zarr_serialization()
        
        # Memory store test
        store = zarr.storage.MemoryStore()
        group = zarr.open_group(store=store, mode="w")
        
        test_tuple = (1, 2, 3)
        group.attrs["version"] = test_tuple
        
        # Reload
        reloaded_group = zarr.open_group(store=store, mode="r")
        result = reloaded_group.attrs["version"]
        
        assert result == test_tuple
        assert isinstance(result, tuple)
        
        print("✅ Tuple preservation works")
        
        zc.disable_zarr_serialization()
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_isolation_test():
    """Run basic isolation test."""
    print("\n🧪 Running isolation test...")
    
    try:
        import json
        import zarrcompatibility as zc
        
        # Store original JSON functions
        original_dumps = json.dumps
        original_loads = json.loads
        
        # Test that tuples become lists in global JSON (before enabling)
        before_result = json.dumps((1, 2, 3))
        assert before_result == "[1, 2, 3]"
        
        # Enable zarrcompatibility
        zc.enable_zarr_serialization()
        
        # Test that global JSON is still unchanged
        assert json.dumps is original_dumps
        assert json.loads is original_loads
        
        # Test that tuples still become lists in global JSON (after enabling)
        after_result = json.dumps((1, 2, 3))
        assert after_result == "[1, 2, 3]"
        assert before_result == after_result
        
        print("✅ Isolation test passed - global JSON unaffected")
        
        zc.disable_zarr_serialization()
        return True
        
    except Exception as e:
        print(f"❌ Isolation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main debug runner."""
    print("🧪 zarrcompatibility v2.1 - Debug Runner")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        return 1
    
    # Run basic tests
    tests = [
        ("Basic Functionality", run_basic_functionality_test),
        ("Isolation", run_isolation_test),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        if test_func():
            passed += 1
        else:
            print(f"\n⚠️ {test_name} test failed - check output above")
    
    print(f"\n📊 Debug Results: {passed}/{len(tests)} core tests passed")
    
    if passed == len(tests):
        print("\n🎉 Core functionality working! Ready for full test suite.")
        print("\nNext steps:")
        print("   python tests/test_isolation.py -v")
        print("   python tests/test_functionality.py -v")
        return 0
    else:
        print("\n❌ Core issues found - fix these before running full tests")
        return 1


if __name__ == "__main__":
    sys.exit(main())
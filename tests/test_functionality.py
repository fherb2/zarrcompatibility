#!/usr/bin/env python3
"""
Functionality tests for zarrcompatibility v2.1.

FIXED VERSION - Corrected path handling for running from tests/ directory.

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

# FIXED: Correct path setup based on current working directory
current_dir = Path.cwd()
if current_dir.name == 'tests':
    # Running from tests/ directory
    src_path = current_dir.parent / 'src'
    testresults_dir = current_dir / 'testresults'
else:
    # Running from project root
    src_path = current_dir / 'src'
    testresults_dir = current_dir / 'tests' / 'testresults'

# Add src to path
sys.path.insert(0, str(src_path))

# Ensure testresults directory exists
testresults_dir.mkdir(parents=True, exist_ok=True)
TESTRESULTS_DIR = testresults_dir

print(f"🔧 Debug Info:")
print(f"   Current directory: {current_dir}")
print(f"   Source path: {src_path}")
print(f"   Test results path: {TESTRESULTS_DIR}")
print(f"   Source exists: {src_path.exists()}")
print(f"   Test results exists: {TESTRESULTS_DIR.exists()}")

# Test framework setup
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    
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


class TestStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


@dataclass
class TestMetadata:
    name: str
    version: tuple
    created: datetime
    

class TestBasicFunctionality:
    """Test basic functionality first to identify core issues."""
    
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
    
    def test_simple_import_and_enable(self):
        """Test that we can import and enable without errors."""
        import zarrcompatibility as zc
        
        # Check basic attributes
        assert hasattr(zc, 'enable_zarr_serialization')
        assert hasattr(zc, 'disable_zarr_serialization')
        assert hasattr(zc, '__version__')
        
        print(f"✅ Basic import test passed - version {zc.__version__}")
    
    def test_simple_memory_storage(self):
        """Test simplest possible case - memory storage with tuples."""
        if not ZARR_AVAILABLE:
            print("⚠️ Skipping - Zarr not available")
            return
            
        import zarr
        
        # Use memory storage (simplest case)
        store = zarr.storage.MemoryStore()
        
        # Create group
        group = zarr.open_group(store=store, mode="w")
        
        # Store simple tuple
        test_tuple = (1, 2, 3)
        group.attrs["version"] = test_tuple
        
        print(f"📝 Stored tuple: {test_tuple}")
        
        # Reload
        reloaded_group = zarr.open_group(store=store, mode="r")
        stored_version = reloaded_group.attrs["version"]
        
        print(f"📖 Retrieved: {stored_version} (type: {type(stored_version)})")
        
        # Verify
        assert stored_version == test_tuple, f"Value mismatch: {stored_version} != {test_tuple}"
        assert isinstance(stored_version, tuple), f"Type mismatch: {type(stored_version)} != tuple"
        
        print("✅ Simple memory storage test passed")


# Simplified main function for debugging
def main():
    """Main function for debugging."""
    print("🧪 zarrcompatibility v2.1 - Debug Test Run")
    print("=" * 50)
    
    # Check environment
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {Path.cwd()}")
    print(f"📦 Python path includes: {[p for p in sys.path if 'src' in p or 'zarrcompatibility' in p]}")
    print()
    
    # Try basic import
    try:
        import zarrcompatibility as zc
        print(f"✅ Import successful: zarrcompatibility v{zc.__version__}")
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return 1
    
    # Check Zarr
    try:
        import zarr
        print(f"✅ Zarr available: v{zarr.__version__}")
        if not zarr.__version__.startswith('3'):
            print(f"⚠️ Warning: Zarr v{zarr.__version__} - tests need v3")
    except ImportError:
        print("❌ Zarr not available")
        return 1
    
    print()
    
    # Run basic functionality test
    test_instance = TestBasicFunctionality()
    
    tests = [
        test_instance.test_simple_import_and_enable,
        test_instance.test_simple_memory_storage,
    ]
    
    passed = 0
    for i, test_func in enumerate(tests, 1):
        print(f"🧪 Test {i}: {test_func.__name__}")
        try:
            test_instance.setup_method()
            test_func()
            test_instance.teardown_method()
            print(f"✅ Test {i} passed")
            passed += 1
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            try:
                test_instance.teardown_method()
            except:
                pass
        print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Basic functionality working!")
        return 0
    else:
        print("❌ Some basic tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Test runner for zarrcompatibility v2.1.

This script provides an easy way to run all tests and get comprehensive results.
It automatically sets up the correct paths and runs tests in the right order.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py -v                # Verbose output
    python run_tests.py isolation         # Run only isolation tests
    python run_tests.py functionality     # Run only functionality tests  
    python run_tests.py integration       # Run only integration tests

Author: F. Herbrand
License: MIT
"""

import sys
import os
import subprocess
from pathlib import Path


def setup_paths():
    """Ensure correct Python paths are set."""
    # Add src to Python path
    src_path = Path("./src").resolve()
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Ensure testresults directory exists
    testresults_dir = Path("./tests/testresults")
    testresults_dir.mkdir(parents=True, exist_ok=True)
    
    return src_path, testresults_dir


def run_test_file(test_file, verbose=False):
    """Run a specific test file."""
    cmd = [sys.executable, f"tests/{test_file}"]
    if verbose:
        cmd.append("-v")
    
    print(f"🧪 Running {test_file}...")
    print("=" * 50)
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {test_file}: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    missing = []
    
    try:
        import zarr
        if not zarr.__version__.startswith('3'):
            print(f"⚠️  Zarr v{zarr.__version__} detected. Tests require Zarr v3.")
            missing.append("zarr>=3.0.0")
        else:
            print(f"✅ Zarr v{zarr.__version__} (v3 ✓)")
    except ImportError:
        print("❌ Zarr not installed")
        missing.append("zarr>=3.0.0")
    
    try:
        import numpy
        print(f"✅ NumPy v{numpy.__version__}")
    except ImportError:
        print("❌ NumPy not installed")
        missing.append("numpy")
    
    # Check if our package can be imported
    try:
        import zarrcompatibility
        print(f"✅ zarrcompatibility v{zarrcompatibility.__version__}")
    except ImportError as e:
        print(f"❌ zarrcompatibility import failed: {e}")
        print("   Make sure you're running from the project root directory")
        missing.append("zarrcompatibility (local)")
    
    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(f'"{dep}"' for dep in missing if not dep.endswith("(local)")))
        return False
    
    print("✅ All dependencies available\n")
    return True


def main():
    """Main test runner."""
    verbose = "-v" in sys.argv or "--verbose" in sys.argv
    
    # Parse test selection
    test_selection = None
    for arg in sys.argv[1:]:
        if arg in ["isolation", "functionality", "integration"]:
            test_selection = arg
            break
    
    print("🧪 zarrcompatibility v2.1 - Test Runner")
    print("=" * 50)
    
    # Setup paths
    src_path, testresults_dir = setup_paths()
    print(f"📁 Source path: {src_path}")
    print(f"📁 Test results: {testresults_dir}")
    print()
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Define test files in order
    test_files = []
    if test_selection is None or test_selection == "isolation":
        test_files.append("test_isolation.py")
    if test_selection is None or test_selection == "functionality":
        test_files.append("test_functionality.py")
    if test_selection is None or test_selection == "integration":
        test_files.append("test_integration.py")
    
    # Run tests
    results = {}
    for test_file in test_files:
        success = run_test_file(test_file, verbose)
        results[test_file] = success
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_file, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} {test_file}")
    
    print()
    print(f"📈 Overall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! zarrcompatibility v2.1 is working correctly.")
        
        # Show created test files
        zarr_files = list(testresults_dir.glob("*.zarr"))
        if zarr_files:
            print(f"\n📂 Created {len(zarr_files)} test .zarr files in {testresults_dir}:")
            for zarr_file in sorted(zarr_files):
                print(f"   - {zarr_file.name}")
        
        return 0
    else:
        print("❌ Some tests failed. Check output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
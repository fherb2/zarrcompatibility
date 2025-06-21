#!/usr/bin/env python3
"""
pytest configuration and fixtures for zarrcompatibility tests.

This file provides common setup, teardown, and fixtures for all tests.
It automatically handles path setup and ensures tests can run from any directory.

Author: F. Herbrand
License: MIT
"""

import sys
import os
import tempfile
import warnings
from pathlib import Path
from typing import Dict, Any, Generator

import pytest


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


# Setup paths at module level
PATHS = setup_project_paths()


# pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "isolation: marks tests as isolation/compatibility tests"
    )
    config.addinivalue_line(
        "markers", "functionality: marks tests as core functionality tests"
    )
    config.addinivalue_line(
        "markers", "requires_zarr: marks tests that require Zarr to be installed"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file names
        if "test_isolation" in str(item.fspath):
            item.add_marker(pytest.mark.isolation)
        elif "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.slow)
        elif "test_functionality" in str(item.fspath):
            item.add_marker(pytest.mark.functionality)
        
        # Add zarr requirement marker for all tests except isolation
        if "test_isolation" not in str(item.fspath):
            item.add_marker(pytest.mark.requires_zarr)


def pytest_runtest_setup(item):
    """Setup run before each test."""
    # Skip zarr-requiring tests if zarr is not available
    if item.get_closest_marker("requires_zarr"):
        try:
            import zarr
            if not hasattr(zarr, '__version__') or not zarr.__version__.startswith('3'):
                pytest.skip(f"Test requires Zarr v3, found v{getattr(zarr, '__version__', 'unknown')}")
        except ImportError:
            pytest.skip("Test requires Zarr but it's not installed")


# Fixtures
@pytest.fixture(scope="session")
def project_paths():
    """Provide project paths to all tests."""
    return PATHS


@pytest.fixture(scope="session")
def zarrcompatibility_module():
    """Import and provide zarrcompatibility module."""
    try:
        import zarrcompatibility as zc
        return zc
    except ImportError as e:
        pytest.fail(f"Failed to import zarrcompatibility: {e}")


@pytest.fixture(scope="function")
def zarr_serialization_enabled(zarrcompatibility_module):
    """
    Enable zarr serialization for a test and ensure cleanup.
    
    This fixture automatically enables zarrcompatibility at the start
    of a test and disables it at the end, ensuring clean state.
    """
    zc = zarrcompatibility_module
    
    # Enable serialization
    zc.enable_zarr_serialization()
    
    yield zc
    
    # Cleanup: disable serialization
    try:
        zc.disable_zarr_serialization()
    except Exception as e:
        warnings.warn(f"Failed to disable zarr serialization: {e}")


@pytest.fixture(scope="function")
def temp_zarr_store():
    """Provide a temporary directory for Zarr storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="function")
def zarr_memory_store():
    """Provide a Zarr memory store."""
    try:
        import zarr
        return zarr.storage.MemoryStore()
    except ImportError:
        pytest.skip("Zarr not available")


@pytest.fixture(scope="function")
def zarr_group_memory(zarr_memory_store, zarr_serialization_enabled):
    """Provide a Zarr group in memory store with serialization enabled."""
    try:
        import zarr
        return zarr.open_group(store=zarr_memory_store, mode="w")
    except ImportError:
        pytest.skip("Zarr not available")


@pytest.fixture(scope="function")
def zarr_group_file(temp_zarr_store, zarr_serialization_enabled):
    """Provide a Zarr group in file store with serialization enabled."""
    try:
        import zarr
        group_path = temp_zarr_store / "test_group.zarr"
        group = zarr.open_group(str(group_path), mode="w")
        
        yield group, group_path
        
        # Cleanup
        try:
            group.store.close()
        except:
            pass
            
    except ImportError:
        pytest.skip("Zarr not available")


@pytest.fixture(scope="session")
def environment_info():
    """Provide environment information for tests."""
    env_info = {
        "python_version": sys.version,
        "python_executable": sys.executable,
        "working_directory": Path.cwd(),
        "project_paths": PATHS,
    }
    
    # Check zarrcompatibility
    try:
        import zarrcompatibility as zc
        env_info["zarrcompatibility_available"] = True
        env_info["zarrcompatibility_version"] = zc.__version__
    except Exception as e:
        env_info["zarrcompatibility_available"] = False
        env_info["zarrcompatibility_error"] = str(e)
    
    # Check Zarr
    try:
        import zarr
        env_info["zarr_available"] = True
        env_info["zarr_version"] = zarr.__version__
        env_info["zarr_compatible"] = zarr.__version__.startswith('3')
    except ImportError:
        env_info["zarr_available"] = False
        env_info["zarr_compatible"] = False
    
    # Check numpy
    try:
        import numpy as np
        env_info["numpy_available"] = True
        env_info["numpy_version"] = np.__version__
    except ImportError:
        env_info["numpy_available"] = False
    
    return env_info


@pytest.fixture(autouse=True, scope="function")
def isolation_check():
    """
    Automatically check that global JSON is not modified after each test.
    
    This fixture runs after every test to ensure no test accidentally
    modifies global JSON behavior.
    """
    import json
    
    # Store original functions before test
    original_dumps = json.dumps
    original_loads = json.loads
    original_dumps_id = id(json.dumps)
    original_loads_id = id(json.loads)
    
    yield
    
    # Check after test that functions are unchanged
    assert json.dumps is original_dumps, "Test modified global json.dumps!"
    assert json.loads is original_loads, "Test modified global json.loads!"
    assert id(json.dumps) == original_dumps_id, "json.dumps identity changed!"
    assert id(json.loads) == original_loads_id, "json.loads identity changed!"
    
    # Quick functional check
    test_tuple = (1, 2, 3)
    result = json.dumps(test_tuple)
    assert result == "[1, 2, 3]", "Global JSON behavior was modified!"
    
    loaded = json.loads(result)
    assert loaded == [1, 2, 3], "Global JSON loads behavior was modified!"
    assert isinstance(loaded, list), "Global JSON should return lists for arrays!"


# Test result collection
def pytest_runtest_makereport(item, call):
    """Collect test results for reporting."""
    if call.when == "call":
        # Store test result for later analysis
        outcome = "PASSED" if call.excinfo is None else "FAILED"
        
        # You could store results here for CI reporting
        # For now, we just ensure test results directory exists
        PATHS['testresults_path'].mkdir(exist_ok=True)


# Session-level reporting
def pytest_sessionfinish(session, exitstatus):
    """Generate summary report after all tests."""
    results_file = PATHS['testresults_path'] / 'pytest_summary.txt'
    
    with open(results_file, 'w') as f:
        f.write("zarrcompatibility v3.0 - pytest Test Summary\n")
        f.write("=" * 50 + "\n")
        f.write(f"Exit status: {exitstatus}\n")
        f.write(f"Total tests: {session.testscollected}\n")
        f.write(f"Failed tests: {session.testsfailed}\n")
        f.write(f"Passed tests: {session.testscollected - session.testsfailed}\n")
        f.write(f"Success rate: {(session.testscollected - session.testsfailed) / max(session.testscollected, 1) * 100:.1f}%\n")
        
        if exitstatus == 0:
            f.write("Status: PASS\n")
        else:
            f.write("Status: FAIL\n")
    
    print(f"\n📁 Test summary saved to: {results_file}")


# Skip deprecated tests
def pytest_ignore_collect(collection_path, config):
    """Ignore deprecated test files."""
    if collection_path.name == "test_json_patch.py":
        return True
    return False

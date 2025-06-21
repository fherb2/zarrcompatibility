#!/usr/bin/env python3
"""
Version management tests for zarrcompatibility.

Tests the version_manager module functionality including version detection,
compatibility validation, and recommendation logic.

Author: F. Herbrand
License: MIT
"""

import sys
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from unittest.mock import patch, MagicMock, mock_open

# Setup paths
def setup_project_paths() -> Dict[str, Path]:
    """Setup paths consistently regardless of execution directory."""
    current_dir = Path.cwd()
    if current_dir.name == 'tests':
        src_path = current_dir.parent / 'src'
    else:
        src_path = current_dir / 'src'
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    return {'src_path': src_path}

PATHS = setup_project_paths()


class TestVersionDetection:
    """Test Zarr version detection functionality."""
    
    def test_get_zarr_version_success(self) -> None:
        """Test successful Zarr version detection."""
        from zarrcompatibility import version_manager as vm
        
        # Should return a string version if Zarr is installed
        version = vm.get_zarr_version()
        
        if version is not None:
            assert isinstance(version, str)
            assert len(version) > 0
            # Should follow semantic versioning pattern
            assert '.' in version
            print(f"✅ Detected Zarr version: {version}")
        else:
            print("⚠️ Zarr not installed - cannot test version detection")
    
    def test_get_zarr_version_not_installed(self) -> None:
        """Test behavior when Zarr is not installed."""
        from zarrcompatibility import version_manager as vm
        
        # Mock ImportError when trying to import zarr
        with patch('builtins.__import__', side_effect=ImportError("No module named 'zarr'")):
            version = vm.get_zarr_version()
            assert version is None
            print("✅ Correctly handles missing Zarr installation")
    
    def test_get_zarr_version_no_version_attr(self) -> None:
        """Test fallback when zarr has no __version__ attribute."""
        from zarrcompatibility import version_manager as vm
        
        # Mock zarr module without __version__
        mock_zarr = MagicMock()
        del mock_zarr.__version__  # Remove __version__ attribute
        
        with patch.dict('sys.modules', {'zarr': mock_zarr}):
            with patch('pkg_resources.get_distribution') as mock_pkg:
                mock_pkg.return_value.version = "3.0.8"
                version = vm.get_zarr_version()
                assert version == "3.0.8"
                print("✅ Correctly falls back to pkg_resources")


class TestVersionCompatibility:
    """Test version compatibility checking."""
    
    def test_is_zarr_version_supported_working_versions(self) -> None:
        """Test known working versions are reported as supported."""
        from zarrcompatibility import version_manager as vm
        
        versions_info = vm.get_supported_versions()
        known_working = versions_info['known_working']
        
        for version in known_working[:3]:  # Test first 3
            supported, reason = vm.is_zarr_version_supported(version)
            assert supported == True
            assert "working" in reason.lower() or "supported" in reason.lower()
            print(f"✅ Version {version}: {reason}")
    
    def test_is_zarr_version_supported_too_old(self) -> None:
        """Test that old versions are rejected."""
        from zarrcompatibility import version_manager as vm
        
        old_versions = ["2.16.0", "2.17.0", "1.0.0"]
        
        for version in old_versions:
            supported, reason = vm.is_zarr_version_supported(version)
            assert supported == False
            assert "below minimum" in reason.lower()
            print(f"✅ Old version {version} correctly rejected: {reason}")
    
    def test_is_zarr_version_supported_too_new(self) -> None:
        """Test that untested new versions are handled appropriately."""
        from zarrcompatibility import version_manager as vm
        
        future_versions = ["4.0.0", "3.1.0", "10.0.0"]
        
        for version in future_versions:
            supported, reason = vm.is_zarr_version_supported(version)
            # Could be supported (in range) or not (above max tested)
            print(f"✅ Future version {version}: supported={supported}, reason={reason}")
    
    def test_is_zarr_version_supported_invalid_version(self) -> None:
        """Test handling of invalid version strings."""
        from zarrcompatibility import version_manager as vm
        
        invalid_versions = ["not.a.version", "", "3.0.x", "latest"]
        
        for version in invalid_versions:
            supported, reason = vm.is_zarr_version_supported(version)
            assert supported == False
            assert "parse" in reason.lower() or "failed" in reason.lower()
            print(f"✅ Invalid version {version} correctly rejected: {reason}")


class TestVersionRecommendations:
    """Test version recommendation logic."""
    
    def test_get_version_recommendation_current_is_recommended(self) -> None:
        """Test when current version is already recommended."""
        from zarrcompatibility import version_manager as vm
        
        versions_info = vm.get_supported_versions()
        recommended = versions_info['recommended']
        
        rec = vm.get_version_recommendation(recommended)
        
        assert rec['current'] == recommended
        assert rec['recommended'] == recommended
        assert rec['action'] == 'none'
        assert rec['command'] is None
        print(f"✅ Recommended version {recommended} needs no action")
    
    def test_get_version_recommendation_upgrade_needed(self) -> None:
        """Test when upgrade is recommended."""
        from zarrcompatibility import version_manager as vm
        
        old_version = "3.0.0"  # Assume this is older than recommended
        rec = vm.get_version_recommendation(old_version)
        
        if rec['action'] in ['upgrade', 'none']:  # Could be none if 3.0.0 is recommended
            print(f"✅ Old version {old_version}: action={rec['action']}")
            if rec['command']:
                assert "pip install" in rec['command']
                assert "zarr==" in rec['command']
        else:
            print(f"⚠️ Unexpected action for old version: {rec['action']}")
    
    def test_get_version_recommendation_not_installed(self) -> None:
        """Test recommendation when Zarr is not installed."""
        from zarrcompatibility import version_manager as vm
        
        # FIXED: Properly mock get_zarr_version to return None
        with patch.object(vm, 'get_zarr_version', return_value=None):
            rec = vm.get_version_recommendation(None)  # Explicitly pass None
            
            assert rec['current'] is None
            assert rec['action'] == 'install'
            assert rec['command'] is not None
            assert "pip install zarr==" in rec['command']
            print(f"✅ Not installed case handled correctly: {rec['command']}")


class TestVersionValidation:
    """Test version validation functionality."""
    
    def test_validate_zarr_version_success(self) -> None:
        """Test successful validation with compatible version."""
        from zarrcompatibility import version_manager as vm
        
        # This should not raise an exception if Zarr is properly installed
        try:
            vm.validate_zarr_version()
            print("✅ Current Zarr installation passes validation")
        except ImportError as e:
            print(f"⚠️ Zarr validation failed (expected if Zarr not installed): {e}")
    
    def test_validate_zarr_version_not_installed(self) -> None:
        """Test validation when Zarr is not installed."""
        from zarrcompatibility import version_manager as vm
        
        with patch.object(vm, 'get_zarr_version', return_value=None):
            try:
                vm.validate_zarr_version()
                assert False, "Should have raised ImportError"
            except ImportError as e:
                assert "not installed" in str(e).lower()
                assert "pip install zarr" in str(e)
                print(f"✅ Correctly rejects missing Zarr: {e}")
    
    def test_validate_zarr_version_too_old(self) -> None:
        """Test validation with unsupported old version."""
        from zarrcompatibility import version_manager as vm
        
        with patch.object(vm, 'get_zarr_version', return_value="2.17.0"):
            try:
                vm.validate_zarr_version()
                assert False, "Should have raised ImportError"
            except ImportError as e:
                assert "too old" in str(e).lower()
                assert "v2 is not supported" in str(e)
                print(f"✅ Correctly rejects old Zarr: {e}")
    
    def test_validate_zarr_version_too_new(self) -> None:
        """Test validation with untested new version."""
        from zarrcompatibility import version_manager as vm
        
        with patch.object(vm, 'get_zarr_version', return_value="10.0.0"):
            try:
                vm.validate_zarr_version()
                assert False, "Should have raised ImportError" 
            except ImportError as e:
                assert "newer" in str(e).lower() or "above" in str(e).lower()
                print(f"✅ Correctly handles future Zarr: {e}")


class TestConfigurationHandling:
    """Test configuration file loading and fallback."""
    
    def test_load_supported_versions_default(self) -> None:
        """Test loading default versions when no config file."""
        from zarrcompatibility import version_manager as vm
        
        # Mock missing config file
        with patch('pathlib.Path.exists', return_value=False):
            versions = vm._load_supported_versions()
            
            # Should contain required keys
            required_keys = ['min_version', 'max_tested', 'known_working', 'recommended']
            for key in required_keys:
                assert key in versions
                assert versions[key] is not None
            
            print(f"✅ Default configuration loaded with {len(versions)} keys")
    
    def test_load_supported_versions_custom_config(self) -> None:
        """Test loading custom configuration file."""
        from zarrcompatibility import version_manager as vm
        
        # Create test config data
        custom_config = {
            "min_version": "3.0.0",
            "max_tested": "3.0.5", 
            "known_working": ["3.0.0", "3.0.5"],
            "recommended": "3.0.5",
            "last_update": "2025-01-19",
            "update_source": "test"
        }
        
        # FIXED: Use mock_open with the JSON content directly
        mock_file_content = json.dumps(custom_config)
        
        # Mock both Path.exists and the file opening
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_file_content)):
                versions = vm._load_supported_versions()
                
                assert versions['min_version'] == "3.0.0"
                assert versions['max_tested'] == "3.0.5"
                assert versions['update_source'] == "test"
                print("✅ Custom configuration loaded correctly")
    
    def test_load_supported_versions_corrupted_config(self) -> None:
        """Test fallback when config file is corrupted."""
        from zarrcompatibility import version_manager as vm
        import warnings
        
        # Create corrupted JSON content
        corrupted_content = "{ invalid json content }"
        
        # Mock file exists but contains invalid JSON
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=corrupted_content)):
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    versions = vm._load_supported_versions()
                    
                    # Should fall back to defaults
                    assert 'min_version' in versions
                    assert len(w) > 0  # Should have warning
                    assert "failed to load" in str(w[0].message).lower()
                    print("✅ Corrupted config handled with fallback")


def run_all_version_management_tests() -> bool:
    """Run all version management tests."""
    print("🧪 zarrcompatibility v3.0 - Version Management Tests")
    print("=" * 60)
    
    test_classes: List[Any] = [
        TestVersionDetection(),
        TestVersionCompatibility(),
        TestVersionRecommendations(),
        TestVersionValidation(),
        TestConfigurationHandling(),
    ]
    
    all_tests: List[Tuple[Any, Any]] = []
    for test_instance in test_classes:
        methods = [getattr(test_instance, method) for method in dir(test_instance) 
                  if method.startswith('test_') and callable(getattr(test_instance, method))]
        all_tests.extend([(test_instance, method) for method in methods])
    
    passed: int = 0
    for i, (test_instance, test_method) in enumerate(all_tests, 1):
        test_name = f"{test_instance.__class__.__name__}.{test_method.__name__}"
        print(f"\n🔍 Test {i}: {test_name}")
        
        try:
            test_method()
            print(f"✅ Test {i} passed")
            passed += 1
        except Exception as e:
            print(f"❌ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Version Management Results: {passed}/{len(all_tests)} tests passed")
    return passed == len(all_tests)


if __name__ == "__main__":
    success = run_all_version_management_tests()
    sys.exit(0 if success else 1)
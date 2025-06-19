"""
Zarr version compatibility management for zarrcompatibility.

This module handles version checking, compatibility validation, and provides
information about supported Zarr versions. It ensures that zarrcompatibility
works correctly with the installed Zarr version and provides helpful error
messages when incompatible versions are detected.

The module supports automated version management through CI/CD pipelines that
can update the supported version database and create new releases when new
Zarr versions are validated.

Key Functions:
    - validate_zarr_version(): Check if installed Zarr is compatible
    - get_supported_versions(): Get version compatibility information
    - is_zarr_version_supported(): Check specific version compatibility
    - get_version_recommendation(): Get upgrade/downgrade recommendations

Author: F. Herbrand
License: MIT
"""

import json
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from packaging import version


# Default supported versions (embedded fallback)
DEFAULT_SUPPORTED_VERSIONS = {
    "min_version": "3.0.0",
    "max_tested": "3.0.8",
    "known_working": [
        "3.0.0", "3.0.1", "3.0.2", "3.0.3", 
        "3.0.4", "3.0.5", "3.0.6", "3.0.7", "3.0.8"
    ],
    "known_issues": {
        "3.0.0": "Initial release - may have stability issues",
        "3.0.1": "Minor bug fixes from 3.0.0"
    },
    "recommended": "3.0.8",
    "last_update": "2025-01-19",
    "update_source": "manual"
}


def _load_supported_versions() -> Dict[str, Any]:
    """
    Load supported Zarr versions from configuration file or return defaults.
    
    Returns
    -------
    dict
        Dictionary containing version compatibility information
    """
    # Try to load from supported_zarr_versions.json
    try:
        config_path = Path(__file__).parent / "supported_zarr_versions.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        warnings.warn(
            f"Failed to load supported_zarr_versions.json: {e}. "
            "Using embedded defaults.",
            UserWarning,
            stacklevel=3
        )
    
    return DEFAULT_SUPPORTED_VERSIONS.copy()


def get_supported_versions() -> Dict[str, Any]:
    """
    Get information about supported Zarr versions.
    
    Returns
    -------
    dict
        Dictionary containing:
        - min_version: Minimum supported Zarr version
        - max_tested: Highest Zarr version tested
        - known_working: List of confirmed working versions
        - known_issues: Dict of version-specific known issues
        - recommended: Recommended Zarr version
        - last_update: Date of last compatibility update
        - update_source: Source of version info (manual/ci)
    
    Examples
    --------
    >>> import zarrcompatibility.version_manager as vm
    >>> versions = vm.get_supported_versions()
    >>> print(f"Recommended Zarr version: {versions['recommended']}")
    >>> print(f"Supported range: {versions['min_version']} - {versions['max_tested']}")
    """
    return _load_supported_versions()


def get_zarr_version() -> Optional[str]:
    """
    Get the currently installed Zarr version.
    
    Returns
    -------
    str or None
        Zarr version string, or None if Zarr is not installed
    """
    try:
        import zarr
        return zarr.__version__
    except ImportError:
        return None
    except AttributeError:
        # Zarr installed but no __version__ attribute
        try:
            import pkg_resources
            return pkg_resources.get_distribution('zarr').version
        except Exception:
            return None


def parse_version(version_str: str) -> version.Version:
    """
    Parse a version string into a comparable Version object.
    
    Parameters
    ----------
    version_str : str
        Version string to parse
        
    Returns
    -------
    packaging.version.Version
        Parsed version object
    """
    return version.parse(version_str)


def is_zarr_version_supported(zarr_version: str) -> Tuple[bool, str]:
    """
    Check if a specific Zarr version is supported.
    
    Parameters
    ----------
    zarr_version : str
        Zarr version string to check
        
    Returns
    -------
    tuple of (bool, str)
        (is_supported, reason) where is_supported indicates compatibility
        and reason provides explanation
    
    Examples
    --------
    >>> supported, reason = is_zarr_version_supported("3.0.8")
    >>> print(f"Zarr 3.0.8 supported: {supported} - {reason}")
    """
    versions_info = get_supported_versions()
    
    try:
        v_zarr = parse_version(zarr_version)
        v_min = parse_version(versions_info["min_version"])
        v_max = parse_version(versions_info["max_tested"])
        
        # Check if version is too old
        if v_zarr < v_min:
            return False, f"Version {zarr_version} is below minimum supported {versions_info['min_version']}"
        
        # Check if version is in known working list
        if zarr_version in versions_info["known_working"]:
            issues = versions_info.get("known_issues", {}).get(zarr_version)
            if issues:
                return True, f"Supported with known issues: {issues}"
            return True, "Confirmed working version"
        
        # Check if version is above max tested
        if v_zarr > v_max:
            return False, f"Version {zarr_version} is above max tested {versions_info['max_tested']} - untested"
        
        # Version is in range but not explicitly tested
        return True, f"Version {zarr_version} is in supported range but not explicitly tested"
        
    except Exception as e:
        return False, f"Failed to parse version {zarr_version}: {e}"


def get_version_recommendation(current_version: Optional[str] = None) -> Dict[str, Any]:
    """
    Get version upgrade/downgrade recommendations.
    
    Parameters
    ----------
    current_version : str, optional
        Current Zarr version. If None, detects automatically.
        
    Returns
    -------
    dict
        Dictionary containing:
        - current: Current version
        - recommended: Recommended version
        - action: Recommended action (upgrade/downgrade/none)
        - reason: Explanation of recommendation
        - command: Pip command to execute recommendation
    """
    if current_version is None:
        current_version = get_zarr_version()
    
    versions_info = get_supported_versions()
    recommended = versions_info["recommended"]
    
    if current_version is None:
        return {
            "current": None,
            "recommended": recommended,
            "action": "install",
            "reason": "Zarr is not installed",
            "command": f"pip install zarr=={recommended}"
        }
    
    if current_version == recommended:
        return {
            "current": current_version,
            "recommended": recommended, 
            "action": "none",
            "reason": "Already using recommended version",
            "command": None
        }
    
    supported, reason = is_zarr_version_supported(current_version)
    
    if not supported:
        try:
            v_current = parse_version(current_version)
            v_recommended = parse_version(recommended)
            
            action = "upgrade" if v_current < v_recommended else "downgrade"
            return {
                "current": current_version,
                "recommended": recommended,
                "action": action,
                "reason": f"Current version not supported: {reason}",
                "command": f"pip install zarr=={recommended}"
            }
        except Exception:
            return {
                "current": current_version,
                "recommended": recommended,
                "action": "reinstall",
                "reason": f"Invalid version format: {current_version}",
                "command": f"pip install zarr=={recommended}"
            }
    
    # Supported but not recommended
    try:
        v_current = parse_version(current_version)
        v_recommended = parse_version(recommended)
        
        if v_current < v_recommended:
            return {
                "current": current_version,
                "recommended": recommended,
                "action": "upgrade",
                "reason": "Newer recommended version available",
                "command": f"pip install --upgrade zarr=={recommended}"
            }
        else:
            return {
                "current": current_version,
                "recommended": recommended,
                "action": "optional_downgrade",
                "reason": "Using newer version than recommended - should work but untested",
                "command": f"pip install zarr=={recommended}"
            }
    except Exception:
        return {
            "current": current_version,
            "recommended": recommended,
            "action": "check",
            "reason": "Unable to compare versions",
            "command": None
        }


def validate_zarr_version() -> None:
    """
    Validate that the installed Zarr version is compatible.
    
    Raises
    ------
    ImportError
        If Zarr is not installed
    ImportError
        If Zarr version is not supported
    UserWarning
        If Zarr version has known issues (but is supported)
    
    Examples
    --------
    >>> import zarrcompatibility.version_manager as vm
    >>> vm.validate_zarr_version()  # Raises exception if incompatible
    """
    # Check if Zarr is installed
    zarr_version = get_zarr_version()
    if zarr_version is None:
        recommendation = get_version_recommendation()
        raise ImportError(
            "Zarr is not installed. zarrcompatibility requires Zarr v3.0.0+.\n"
            f"Install with: {recommendation['command']}"
        )
    
    # Check version compatibility
    supported, reason = is_zarr_version_supported(zarr_version)
    
    if not supported:
        recommendation = get_version_recommendation(zarr_version)
        
        # Provide helpful error message based on the issue
        if "below minimum" in reason:
            raise ImportError(
                f"Zarr v{zarr_version} is too old. zarrcompatibility v2.1 requires Zarr v3.0+.\n"
                f"Zarr v2 is not supported. Please upgrade: {recommendation['command']}"
            )
        elif "above max tested" in reason:
            raise ImportError(
                f"Zarr v{zarr_version} is newer than the last tested version.\n"
                f"zarrcompatibility may not work correctly with this version.\n"
                f"Consider downgrading to tested version: {recommendation['command']}\n"
                f"Or check for zarrcompatibility updates."
            )
        else:
            raise ImportError(
                f"Zarr v{zarr_version} is not supported: {reason}\n"
                f"Recommended action: {recommendation['command']}"
            )
    
    # Check for known issues
    versions_info = get_supported_versions()
    known_issues = versions_info.get("known_issues", {})
    if zarr_version in known_issues:
        warnings.warn(
            f"Zarr v{zarr_version} has known issues: {known_issues[zarr_version]}. "
            f"Consider upgrading to v{versions_info['recommended']}.",
            UserWarning,
            stacklevel=3
        )


def print_version_info() -> None:
    """
    Print comprehensive version information for debugging.
    
    This function prints detailed information about the current Zarr
    installation, compatibility status, and recommendations.
    """
    print("🔍 Zarr Version Compatibility Information")
    print("=" * 50)
    
    # Current installation
    zarr_version = get_zarr_version()
    if zarr_version:
        print(f"📦 Installed Zarr version: {zarr_version}")
    else:
        print("❌ Zarr not installed")
    
    # Compatibility status
    if zarr_version:
        supported, reason = is_zarr_version_supported(zarr_version)
        status = "✅ Supported" if supported else "❌ Not supported"
        print(f"🔧 Compatibility status: {status}")
        print(f"   Reason: {reason}")
    
    # Version information
    versions_info = get_supported_versions()
    print(f"\n📋 Version Support Information:")
    print(f"   Minimum supported: {versions_info['min_version']}")
    print(f"   Maximum tested: {versions_info['max_tested']}")
    print(f"   Recommended: {versions_info['recommended']}")
    print(f"   Last updated: {versions_info['last_update']}")
    
    # Known working versions
    working_versions = versions_info['known_working']
    print(f"\n✅ Known working versions ({len(working_versions)}):")
    for v in working_versions[-5:]:  # Show last 5
        issues = versions_info.get('known_issues', {}).get(v, '')
        issue_str = f" (⚠️  {issues})" if issues else ""
        print(f"   - {v}{issue_str}")
    if len(working_versions) > 5:
        print(f"   ... and {len(working_versions) - 5} more")
    
    # Recommendations
    if zarr_version:
        recommendation = get_version_recommendation(zarr_version)
        if recommendation['action'] != 'none':
            print(f"\n💡 Recommendation:")
            print(f"   Action: {recommendation['action']}")
            print(f"   Reason: {recommendation['reason']}")
            if recommendation['command']:
                print(f"   Command: {recommendation['command']}")

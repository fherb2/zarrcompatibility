"""
Zarr-focused JSON serialization enhancement for Python scientific computing.

This module provides enhanced JSON serialization capabilities specifically for Zarr
metadata storage, solving the tuple-to-list conversion problem and adding support
for additional Python types, while maintaining complete isolation from the global
JSON module.

🎯 **Key Features:**
    - Tuple preservation in Zarr metadata (tuples stay tuples!)
    - Support for datetime, enum, UUID, dataclass, complex, decimal types
    - Zero side effects on global JSON or other libraries  
    - Import order independence
    - Professional-grade production safety
    - Zarr v3 optimized and tested

🚀 **Quick Start:**
    >>> import zarrcompatibility as zc
    >>> import zarr
    >>> import tempfile
    >>> 
    >>> # One-time setup
    >>> zc.enable_zarr_serialization()
    >>> 
    >>> # Tuples now preserved in Zarr!
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
    ...     group.attrs["version"] = (3, 0, 0)  # Stays as tuple!
    ...     group.store.close()
    ...     
    ...     reloaded = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
    ...     assert reloaded.attrs["version"] == (3, 0, 0)
    ...     assert isinstance(reloaded.attrs["version"], tuple)  # ✅

🔒 **Safety Guarantees:**
    - Global json.dumps/loads remain completely unchanged
    - Other libraries (requests, pandas, numpy) unaffected
    - Import order doesn't matter
    - No unexpected side effects in your application

🏗️ **Architecture:**
    This module works by patching only Zarr's internal JSON serialization
    methods, creating a clean separation between Zarr operations and the
    rest of your Python environment.

📦 **Supported Types in Zarr Metadata:**
    - tuple: (1, 2, 3) → preserved as tuple
    - datetime: datetime.now() → ISO string, restored as datetime
    - Enum: MyEnum.VALUE → enum value, restored as enum  
    - UUID: uuid4() → string, restored as UUID
    - dataclass: @dataclass objects → dict, restored as dataclass
    - complex: 1+2j → {"real": 1, "imag": 2}, restored as complex
    - bytes: b"data" → base64 string, restored as bytes
    - Decimal: Decimal("1.23") → string, restored as Decimal

⚙️ **Requirements:**
    - Python 3.8+
    - Zarr 3.0.0+ (v2 not supported)
    - See supported_zarr_versions.json for tested versions

📋 **Version:** 3.0.0
📧 **Author:** F. Herbrand  
📄 **License:** MIT
"""

import warnings
from typing import Any, Dict, Optional

# Import sub-modules
from . import version_manager
from . import serializers
from . import zarr_patching
from . import type_handlers

# Module version
__version__ = "3.0.0"
__author__ = "F. Herbrand"
__license__ = "MIT"

# Global state tracking
_zarr_patching_enabled = False


def enable_zarr_serialization() -> None:
    """
    Enable enhanced JSON serialization for Zarr metadata only.
    
    This function patches Zarr's internal JSON serialization methods to support
    additional Python types while leaving the global json module unchanged.
    This approach has no side effects on other libraries.
    
    The following types become serializable in Zarr metadata:
        - Tuples (preserved as tuples, not converted to lists)
        - Datetime objects (as ISO strings)
        - Enums (as their values)
        - UUIDs (as strings)
        - Dataclasses (as dictionaries)
        - Complex numbers (as real/imaginary dicts)
        - Binary data (as base64 strings)
        - Decimal numbers (as strings)
    
    Raises
    ------
    ImportError
        If Zarr is not installed or incompatible version
    RuntimeError
        If patching fails due to Zarr API changes
        
    Examples
    --------
    Basic usage with tuple preservation:
    
    >>> import zarrcompatibility as zc
    >>> import zarr
    >>> import tempfile
    >>> 
    >>> zc.enable_zarr_serialization()
    >>> 
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
    ...     group.attrs["version"] = (3, 0, 0)
    ...     group.store.close()
    ...     
    ...     reloaded = zarr.open_group(f"{tmpdir}/test.zarr", mode="r")
    ...     assert reloaded.attrs["version"] == (3, 0, 0)
    ...     assert isinstance(reloaded.attrs["version"], tuple)
    
    Using with complex types:
    
    >>> from datetime import datetime
    >>> from enum import Enum
    >>> 
    >>> class Status(Enum):
    ...     ACTIVE = "active"
    ...     INACTIVE = "inactive"
    >>> 
    >>> with tempfile.TemporaryDirectory() as tmpdir:
    ...     group = zarr.open_group(f"{tmpdir}/test.zarr", mode="w")
    ...     group.attrs["created"] = datetime.now()
    ...     group.attrs["status"] = Status.ACTIVE
    ...     group.attrs["coordinates"] = (10.5, 20.3)
    ...     # All types are properly serialized and preserved
    
    Notes
    -----
    This function should be called once at the beginning of your program,
    before any Zarr operations. It's safe to call multiple times.
    
    This approach ensures that:
    - Standard json.dumps/loads remain unchanged
    - Other libraries (requests, pandas, etc.) are unaffected
    - No import order dependencies
    - No unexpected side effects
    """
    global _zarr_patching_enabled
    
    # Check if already enabled
    if _zarr_patching_enabled:
        warnings.warn(
            "Zarr serialization already enabled. Multiple calls to "
            "enable_zarr_serialization() are safe but unnecessary.",
            UserWarning,
            stacklevel=2
        )
        return
    
    try:
        # Step 1: Validate Zarr version compatibility
        version_manager.validate_zarr_version()
        
        # Step 2: Apply Zarr-specific patches
        zarr_patching.patch_v3_json_encoder()
        zarr_patching.patch_zarr_v3_json_loading()
        
        # Step 3: Mark as enabled
        _zarr_patching_enabled = True
        
        print("✅ Zarr serialization enabled successfully!")
        print("   - Tuple preservation active in Zarr metadata")
        print("   - Additional types supported (datetime, enum, UUID, etc.)")
        print("   - Global JSON module remains unchanged")
        
    except ImportError as e:
        raise ImportError(
            f"Failed to enable Zarr serialization: {e}. "
            "Please ensure Zarr v3.0+ is installed: pip install zarr>=3.0.0"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Failed to patch Zarr serialization methods: {e}. "
            "This may indicate an incompatible Zarr version. "
            "Please check supported_zarr_versions.json for compatibility."
        ) from e


def disable_zarr_serialization() -> None:
    """
    Disable Zarr serialization enhancements and restore original behavior.
    
    This function restores Zarr's original JSON serialization methods,
    removing all enhancements provided by this module. After calling this
    function, tuples will again be converted to lists in Zarr metadata.
    
    Notes
    -----
    This function is primarily useful for testing and debugging. In normal
    usage, there's typically no need to disable the enhancements.
    """
    global _zarr_patching_enabled
    
    if not _zarr_patching_enabled:
        warnings.warn(
            "Zarr serialization not currently enabled. Nothing to disable.",
            UserWarning,
            stacklevel=2
        )
        return
    
    try:
        zarr_patching.restore_original_zarr_functions()
        _zarr_patching_enabled = False
        
        print("✅ Zarr serialization disabled. Original behavior restored.")
        
    except Exception as e:
        warnings.warn(
            f"Failed to completely restore original Zarr functions: {e}. "
            "You may need to restart Python to ensure clean state.",
            UserWarning,
            stacklevel=2
        )


def is_zarr_serialization_enabled() -> bool:
    """
    Check if Zarr serialization enhancements are currently active.
    
    Returns
    -------
    bool
        True if zarr serialization is enabled, False otherwise
    """
    return _zarr_patching_enabled


def get_supported_zarr_versions() -> Dict[str, Any]:
    """
    Get information about supported Zarr versions.
    
    Returns
    -------
    dict
        Dictionary containing version compatibility information including
        min_version, max_tested, known_working versions, and last_update
    """
    return version_manager.get_supported_versions()


def test_serialization(obj: Any, verbose: bool = True) -> bool:
    """
    Test if an object can be successfully serialized and deserialized.
    
    This function tests the complete round-trip serialization process:
    object → JSON → object, verifying that the result matches the original.
    
    Parameters
    ----------
    obj : any
        Object to test serialization for
    verbose : bool, default True
        If True, print detailed test results
        
    Returns
    -------
    bool
        True if serialization test passes, False otherwise
    
    Examples
    --------
    >>> import zarrcompatibility as zc
    >>> zc.enable_zarr_serialization()
    >>> 
    >>> # Test tuple serialization
    >>> result = zc.test_serialization((1, 2, 3))
    Serialization test passed for tuple
       Original: (1, 2, 3)
       Serialized: {'__type__': 'tuple', '__data__': [1, 2, 3]}
       Deserialized: (1, 2, 3)
    >>> assert result == True
    """
    if not _zarr_patching_enabled:
        if verbose:
            print("❌ Zarr serialization not enabled. Call enable_zarr_serialization() first.")
        return False
        
    return serializers.test_object_serialization(obj, verbose=verbose)


# Export main API
__all__ = [
    "enable_zarr_serialization",
    "disable_zarr_serialization", 
    "is_zarr_serialization_enabled",
    "get_supported_zarr_versions",
    "test_serialization",
    "__version__",
    "__author__",
    "__license__",
]


# Module-level setup validation
def _validate_module_import():
    """Validate module can be imported safely."""
    try:
        # Check Python version
        import sys
        if sys.version_info < (3, 8):
            warnings.warn(
                f"zarrcompatibility v{__version__} requires Python 3.8+. "
                f"Found Python {sys.version_info.major}.{sys.version_info.minor}. "
                "Some features may not work correctly.",
                UserWarning,
                stacklevel=2
            )
        
        # Check if Zarr is available (but don't require it at import time)
        try:
            import zarr
            version_manager.validate_zarr_version()
        except ImportError:
            # Zarr not installed - that's okay, we'll check when enabling
            pass
        except Exception as e:
            # Zarr version incompatible - warn but don't fail import
            warnings.warn(
                f"Zarr version compatibility issue: {e}. "
                "Call get_supported_zarr_versions() for more information.",
                UserWarning,
                stacklevel=2
            )
            
    except Exception as e:
        warnings.warn(
            f"Module validation failed: {e}. Some features may not work correctly.",
            UserWarning,
            stacklevel=2
        )

# Run validation on module import
_validate_module_import()

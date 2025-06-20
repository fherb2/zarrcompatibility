"""
zarrcompatibility - Zarr-focused JSON serialization enhancement.

This package provides enhanced JSON serialization capabilities specifically for Zarr
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
    >>> zc.enable_zarr_serialization()
    >>> # Now tuples are preserved in Zarr metadata!

⚙️ **Requirements:**
    - Python 3.8+
    - Zarr 3.0.0+ (v2 not supported)

📋 **Version:** 3.0.0
📧 **Author:** F. Herbrand  
📄 **License:** MIT
"""

# Import main API functions
from .main import (
    enable_zarr_serialization,
    disable_zarr_serialization,
    is_zarr_serialization_enabled,
    get_supported_zarr_versions,
    test_serialization,
)

# Import version info
from .main import __version__, __author__, __license__

# Export public API
__all__ = [
    # Main API
    "enable_zarr_serialization",
    "disable_zarr_serialization", 
    "is_zarr_serialization_enabled",
    "get_supported_zarr_versions",
    "test_serialization",
    
    # Package info
    "__version__",
    "__author__",
    "__license__",
]

"""
zarrcompatibility - Zarr-focused JSON serialization enhancement.

This package provides enhanced JSON serialization capabilities specifically for Zarr
metadata storage, solving the tuple-to-list conversion problem and adding support
for additional Python types, while maintaining complete isolation from the global
JSON module.

Author: F. Herbrand
License: MIT
Version: 2.1.0
"""

# Import main API functions
from .main import (
    enable_zarr_serialization,
    disable_zarr_serialization,
    is_zarr_serialization_enabled,
    get_supported_zarr_versions,
    test_serialization,
    # Backward compatibility (deprecated)
    enable_universal_serialization,
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
    
    # Backward compatibility (deprecated)
    "enable_universal_serialization",
    
    # Package info
    "__version__",
    "__author__",
    "__license__",
]
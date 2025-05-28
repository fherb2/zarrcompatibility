"""
ZarrCompatibility Package

Universal JSON serialization for Python objects with Zarr compatibility.
"""

from .serialization import (
    # Core functions
    enable_universal_serialization,
    disable_universal_serialization,
    serialize_object,
    deserialize_object,
    
    # Mixin classes
    JSONSerializable,
    ZarrCompatible,
    
    # Utilities
    make_serializable,
    is_json_serializable,
    prepare_for_zarr,
    test_serialization,
    
    # JSON Encoder
    UniversalJSONEncoder,
)

# Define what gets imported with "from zarrcompatibility import *"
__all__ = [
    # Main functions
    'enable_universal_serialization',
    'disable_universal_serialization',
    'serialize_object',
    'deserialize_object',
    
    # Mixin classes
    'JSONSerializable',
    'ZarrCompatible',
    
    # Utilities
    'make_serializable',
    'is_json_serializable',
    'prepare_for_zarr',
    'test_serialization',
    
    # JSON Encoder
    'UniversalJSONEncoder',
]
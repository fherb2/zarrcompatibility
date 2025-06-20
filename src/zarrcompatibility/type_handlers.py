"""
Type serialization and deserialization handlers for zarrcompatibility.

FIXED VERSION - Added Zarr internal object detection to prevent over-serialization.

This version adds a critical fix: we now detect and skip Zarr-internal objects
like DataType enums, which should remain untouched by our enhanced serialization.

Author: F. Herbrand
License: MIT
"""

import base64
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
from uuid import UUID


# Type marker for tuple preservation
TUPLE_TYPE_MARKER = "__type__"
TUPLE_DATA_MARKER = "__data__"
TUPLE_TYPE_VALUE = "tuple"


def is_zarr_internal_object(obj: Any) -> bool:
    """
    Check if an object is a Zarr-internal type that should NOT be enhanced.
    
    This function is VERY PRECISE to avoid blocking user enums and types.
    Only objects that are genuinely part of Zarr's internal machinery are blocked.
    
    CRITICAL: User enums (even if named "DataType") must NOT be blocked!
    
    Parameters
    ----------
    obj : any
        Object to check
        
    Returns
    -------
    bool
        True if this is a Zarr-internal object that should not be enhanced
    """
    # Get the object's class module
    obj_class = type(obj)
    obj_module = getattr(obj_class, '__module__', '')
    obj_class_name = obj_class.__name__
    
    # PRECISE CHECK: Only block objects that are SPECIFICALLY from Zarr's internal modules
    # and have the exact problematic combinations
    
    # Block zarr.core.metadata.v3.DataType specifically (the original culprit)
    if obj_module == 'zarr.core.metadata.v3' and obj_class_name == 'DataType':
        return True
    
    # Block other specific Zarr internal metadata objects
    zarr_internal_combinations = [
        ('zarr.core.metadata.v3', 'ArrayV3Metadata'),
        ('zarr.core.group', 'GroupMetadata'),
        ('zarr.core.buffer', 'Buffer'),
        ('zarr.core.store', 'Store'),
        ('zarr.core.chunk_grids', 'ChunkGrid'),
        ('zarr.core.chunk_key_encodings', 'ChunkKeyEncoding'),
        ('zarr.core.codecs', 'Codec'),
        ('zarr.core.metadata', 'ArrayMetadata'),
        ('zarr.core.chunk_grids', 'ChunkManifest'),
        ('zarr.core.indexing', 'Selection'),
    ]
    
    for module_pattern, class_pattern in zarr_internal_combinations:
        if obj_module == module_pattern and obj_class_name == class_pattern:
            return True
    
    # Block NumPy dtypes and related objects (they have their own serialization)
    if obj_module and obj_module.startswith('numpy') and obj_class_name in ['dtype', 'ndarray']:
        return True
    
    # DO NOT block anything else - especially not user enums, user dataclasses, etc.
    # User objects should always be enhanced, regardless of their names
    
    return False


class TypeHandler:
    """Base class for type serialization handlers."""
    
    def can_handle(self, obj: Any) -> bool:
        """Check if this handler can process the given object."""
        raise NotImplementedError("Subclasses must implement can_handle()")
    
    def serialize(self, obj: Any) -> Any:
        """Convert object to JSON-compatible representation."""
        raise NotImplementedError("Subclasses must implement serialize()")
    
    def can_deserialize(self, data: Any) -> bool:
        """Check if this handler can deserialize the given data."""
        raise NotImplementedError("Subclasses must implement can_deserialize()")
    
    def deserialize(self, data: Any) -> Any:
        """Convert JSON-compatible data back to original object."""
        raise NotImplementedError("Subclasses must implement deserialize()")


class TupleHandler(TypeHandler):
    """Handler for tuple preservation - the main feature of zarrcompatibility."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, tuple)
    
    def serialize(self, obj: tuple) -> Dict[str, Any]:
        """Convert tuple to type-preserved dict with recursive serialization."""
        # Recursively serialize tuple elements
        serialized_data = [serialize_object(item) for item in obj]
        return {
            TUPLE_TYPE_MARKER: TUPLE_TYPE_VALUE,
            TUPLE_DATA_MARKER: serialized_data
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get(TUPLE_TYPE_MARKER) == TUPLE_TYPE_VALUE and
            TUPLE_DATA_MARKER in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> tuple:
        """Restore tuple from type-preserved dict with recursive deserialization."""
        # Recursively deserialize tuple elements
        deserialized_data = [deserialize_object(item) for item in data[TUPLE_DATA_MARKER]]
        return tuple(deserialized_data)


class DateTimeHandler(TypeHandler):
    """Handler for datetime objects using ISO format."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, (datetime, date, time))
    
    def serialize(self, obj: Union[datetime, date, time]) -> Dict[str, Any]:
        """Convert datetime to ISO string with type info."""
        return {
            "__type__": "datetime",
            "__subtype__": type(obj).__name__,
            "__data__": obj.isoformat()
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "datetime" and
            "__subtype__" in data and
            "__data__" in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> Union[datetime, date, time]:
        """Restore datetime from ISO string."""
        subtype = data["__subtype__"]
        iso_string = data["__data__"]
        
        if subtype == "datetime":
            return datetime.fromisoformat(iso_string)
        elif subtype == "date":
            return date.fromisoformat(iso_string)
        elif subtype == "time":
            return time.fromisoformat(iso_string)
        else:
            raise ValueError(f"Unknown datetime subtype: {subtype}")


class EnumHandler(TypeHandler):
    """Handler for Enum objects - but only user enums, not Zarr internal ones."""
    
    def can_handle(self, obj: Any) -> bool:
        # Only handle user enums, not Zarr internal ones
        return isinstance(obj, Enum) and not is_zarr_internal_object(obj)
    
    def serialize(self, obj: Enum) -> Dict[str, Any]:
        """Convert enum to value with type info."""
        return {
            "__type__": "enum",
            "__class__": f"{obj.__class__.__module__}.{obj.__class__.__qualname__}",
            "__data__": obj.value
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "enum" and
            "__class__" in data and
            "__data__" in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> Enum:
        """Restore enum from value and class info."""
        # Import the enum class
        module_name, class_name = data["__class__"].rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        enum_class = getattr(module, class_name)
        
        # Create enum instance from value
        return enum_class(data["__data__"])


class UUIDHandler(TypeHandler):
    """Handler for UUID objects."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, UUID)
    
    def serialize(self, obj: UUID) -> Dict[str, Any]:
        """Convert UUID to string with type info."""
        return {
            "__type__": "uuid",
            "__data__": str(obj)
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "uuid" and
            "__data__" in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> UUID:
        """Restore UUID from string."""
        return UUID(data["__data__"])


class DataclassHandler(TypeHandler):
    """Handler for dataclass objects."""
    
    def can_handle(self, obj: Any) -> bool:
        return is_dataclass(obj) and not isinstance(obj, type)
    
    def serialize(self, obj: Any) -> Dict[str, Any]:
        """Convert dataclass to dict with type info and recursive serialization."""
        raw_data = asdict(obj)
        serialized_data = serialize_object(raw_data)
        
        return {
            "__type__": "dataclass",
            "__class__": f"{obj.__class__.__module__}.{obj.__class__.__qualname__}",
            "__data__": serialized_data
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "dataclass" and
            "__class__" in data and
            "__data__" in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> Any:
        """Restore dataclass from dict and class info with recursive deserialization."""
        # Import the dataclass
        module_name, class_name = data["__class__"].rsplit(".", 1)
        module = __import__(module_name, fromlist=[class_name])
        dataclass_type = getattr(module, class_name)
        
        # Recursively deserialize the data first
        deserialized_data = deserialize_object(data["__data__"])
        
        # Create instance from dict
        return dataclass_type(**deserialized_data)


class ComplexHandler(TypeHandler):
    """Handler for complex numbers."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, complex)
    
    def serialize(self, obj: complex) -> Dict[str, Any]:
        """Convert complex to real/imaginary dict."""
        return {
            "__type__": "complex",
            "__data__": {"real": obj.real, "imag": obj.imag}
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "complex" and
            isinstance(data.get("__data__"), dict) and
            "real" in data["__data__"] and
            "imag" in data["__data__"]
        )
    
    def deserialize(self, data: Dict[str, Any]) -> complex:
        """Restore complex from real/imaginary dict."""
        d = data["__data__"]
        return complex(d["real"], d["imag"])


class BytesHandler(TypeHandler):
    """Handler for bytes objects using base64 encoding."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, bytes)
    
    def serialize(self, obj: bytes) -> Dict[str, Any]:
        """Convert bytes to base64 string with type info."""
        return {
            "__type__": "bytes",
            "__data__": base64.b64encode(obj).decode('ascii')
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "bytes" and
            "__data__" in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> bytes:
        """Restore bytes from base64 string."""
        return base64.b64decode(data["__data__"])


class DecimalHandler(TypeHandler):
    """Handler for Decimal objects."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, Decimal)
    
    def serialize(self, obj: Decimal) -> Dict[str, Any]:
        """Convert Decimal to string with type info."""
        return {
            "__type__": "decimal",
            "__data__": str(obj)
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "decimal" and
            "__data__" in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> Decimal:
        """Restore Decimal from string."""
        return Decimal(data["__data__"])


# Registry of type handlers
_TYPE_HANDLERS: List[TypeHandler] = [
    TupleHandler(),
    DateTimeHandler(),
    EnumHandler(),
    UUIDHandler(),
    DataclassHandler(),
    ComplexHandler(),
    BytesHandler(),
    DecimalHandler(),
]


def register_type_handler(handler: TypeHandler, priority: int = 0) -> None:
    """Register a custom type handler."""
    if priority > 0:
        _TYPE_HANDLERS.insert(0, handler)
    else:
        _TYPE_HANDLERS.append(handler)


def serialize_object(obj: Any) -> Any:
    """
    Serialize an object to JSON-compatible form using registered handlers.
    
    This function tries to find an appropriate type handler for the object.
    If no handler is found, it falls back to basic JSON types or collections.
    
    CRITICAL FIX: Now checks for Zarr-internal objects first and skips them.
    """
    # Handle basic JSON types first
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    # CRITICAL FIX: Skip Zarr-internal objects that should NOT be enhanced
    # These are Zarr's internal types that must remain untouched
    if is_zarr_internal_object(obj):
        return obj
    
    # Try registered type handlers first (BEFORE collections)
    for handler in _TYPE_HANDLERS:
        if handler.can_handle(obj):
            return handler.serialize(obj)
    
    # Handle collections recursively AFTER type handlers
    if isinstance(obj, dict):
        return {key: serialize_object(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_object(item) for item in obj]
    elif isinstance(obj, tuple):
        # This should have been handled by TupleHandler above
        # If we reach here, something is wrong with the handler registration
        raise RuntimeError(f"Tuple {obj} was not handled by TupleHandler - handler registration issue!")
    elif isinstance(obj, set):
        return {"__type__": "set", "__data__": [serialize_object(item) for item in obj]}
    
    # Fallback for unknown types
    return str(obj)


def deserialize_object(data: Any) -> Any:
    """
    Deserialize JSON-compatible data back to Python objects using registered handlers.
    
    This function tries to find an appropriate type handler that can deserialize
    the data. If no handler is found, it processes collections recursively.
    """
    # Handle basic JSON types
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    
    # Try registered type handlers first (BEFORE collections)
    if isinstance(data, dict):
        for handler in _TYPE_HANDLERS:
            if handler.can_deserialize(data):
                return handler.deserialize(data)
        
        # Handle set type
        if data.get("__type__") == "set" and "__data__" in data:
            return set(deserialize_object(item) for item in data["__data__"])
        
        # Regular dict - deserialize values recursively
        return {key: deserialize_object(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [deserialize_object(item) for item in data]
    
    # Return as-is if no handler found
    return data


def get_supported_types() -> List[str]:
    """Get list of supported types for serialization."""
    return [
        "tuple", "datetime", "date", "time", "enum", "uuid", 
        "dataclass", "complex", "bytes", "decimal", "set"
    ]


def test_type_roundtrip(obj: Any, verbose: bool = False) -> bool:
    """Test if an object can roundtrip through serialization successfully."""
    try:
        # Serialize
        serialized = serialize_object(obj)
        
        # Deserialize
        deserialized = deserialize_object(serialized)
        
        # Compare
        success = obj == deserialized and type(obj) == type(deserialized)
        
        if verbose:
            print(f"Type roundtrip test: {type(obj).__name__}")
            print(f"  Original: {obj!r}")
            print(f"  Serialized: {serialized!r}")
            print(f"  Deserialized: {deserialized!r}")
            print(f"  Success: {success}")
            if not success:
                print(f"    Type match: {type(obj) == type(deserialized)}")
                print(f"    Value match: {obj == deserialized}")
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"Type roundtrip test failed for {type(obj).__name__}: {e}")
        return False


def print_type_handler_status() -> None:
    """Print status information about all registered type handlers."""
    print("🔧 Type Handler Status Report")
    print("=" * 40)
    
    print(f"📊 Total handlers registered: {len(_TYPE_HANDLERS)}")
    print()
    
    print("📋 Registered Type Handlers:")
    for i, handler in enumerate(_TYPE_HANDLERS, 1):
        handler_name = handler.__class__.__name__
        print(f"   {i}. {handler_name}")
    
    print()
    print("✅ Supported Types:")
    for type_name in get_supported_types():
        print(f"   - {type_name}")
    
    print()
    print("💡 To test a specific type:")
    print("   from zarrcompatibility.type_handlers import test_type_roundtrip")
    print("   test_type_roundtrip(your_object, verbose=True)")


def debug_serialization(obj: Any) -> Tuple[Optional[Any], Optional[Any]]:
    """Debug function to trace serialization process."""
    print(f"\n🔍 DEBUG: Serializing {type(obj).__name__}: {obj!r}")
    
    # Check if it's a Zarr internal object
    if is_zarr_internal_object(obj):
        print(f"   🚫 ZARR INTERNAL OBJECT - skipping enhancement")
        print(f"   Module: {type(obj).__module__}")
        print(f"   Class: {type(obj).__name__}")
        return obj, obj
    
    # Check which handler will be used
    handler_found: Optional[TypeHandler] = None
    for i, handler in enumerate(_TYPE_HANDLERS):
        if handler.can_handle(obj):
            handler_found = handler
            print(f"   Handler: {handler.__class__.__name__} (index {i})")
            break
    
    if not handler_found:
        print(f"   Handler: None - will use fallback logic")
    
    # Test serialization
    try:
        serialized = serialize_object(obj)
        print(f"   Serialized: {serialized!r}")
        
        # Test deserialization
        deserialized = deserialize_object(serialized)
        print(f"   Deserialized: {deserialized!r}")
        print(f"   Type match: {type(obj) == type(deserialized)}")
        print(f"   Value match: {obj == deserialized}")
        
        return serialized, deserialized
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_zarr_internal_detection() -> None:
    """Test the Zarr internal object detection functionality."""
    print("🧪 Testing Zarr Internal Object Detection")
    print("=" * 50)
    
    test_cases = []
    
    # Try to import and test Zarr types
    try:
        from zarr.core.metadata.v3 import DataType
        test_cases.append(("DataType.float32", DataType.float32))
    except ImportError:
        print("   ⚠️  Could not import zarr.core.metadata.v3.DataType")
    
    # Test user types (should NOT be detected as Zarr internal)
    from enum import Enum
    from datetime import datetime
    
    class UserEnum(Enum):
        TEST = "test"
    
    test_cases.extend([
        ("UserEnum.TEST", UserEnum.TEST),
        ("datetime.now()", datetime.now()),
        ("tuple", (1, 2, 3)),
        ("string", "hello"),
        ("int", 42),
    ])
    
    for name, obj in test_cases:
        is_internal = is_zarr_internal_object(obj)
        obj_module = getattr(type(obj), '__module__', 'unknown')
        obj_class = type(obj).__name__
        
        status = "🚫 INTERNAL" if is_internal else "✅ USER TYPE"
        print(f"   {status}: {name}")
        print(f"      Module: {obj_module}")
        print(f"      Class: {obj_class}")
        print(f"      Value: {obj!r}")
        print()
    
    print("✅ Zarr internal object detection test completed")


if __name__ == "__main__":
    # Run tests when module is executed directly
    test_zarr_internal_detection()
    print()
    print_type_handler_status()
"""
Type serialization and deserialization handlers for zarrcompatibility.

This module provides specialized handlers for converting Python objects to
JSON-compatible representations and back. Each type handler is responsible
for safely converting objects to/from JSON while preserving their semantic
meaning and type information.

The module includes handlers for:
    - Tuples (main feature - preserved as tuples)
    - Datetime objects (ISO format strings)
    - Enums (value extraction and restoration)
    - UUIDs (string representation)
    - Dataclasses (field dictionaries)
    - Complex numbers (real/imaginary dicts)
    - Binary data (base64 encoding)
    - Decimal numbers (string representation)

Key Functions:
    - serialize_object(): Convert any object to JSON-compatible form
    - deserialize_object(): Restore objects from JSON-compatible form
    - register_type_handler(): Add custom type handlers
    - get_supported_types(): List all supported types

Design Principles:
    - Type preservation: Objects roundtrip to their original type
    - Safety: Invalid data doesn't crash the deserializer
    - Extensibility: Easy to add new type handlers
    - Performance: Minimal overhead for supported types

Author: F. Herbrand
License: MIT
"""

import base64
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union
from uuid import UUID


# Type marker for tuple preservation
TUPLE_TYPE_MARKER = "__type__"
TUPLE_DATA_MARKER = "__data__"
TUPLE_TYPE_VALUE = "tuple"


class TypeHandler:
    """
    Base class for type serialization handlers.
    
    Each type handler is responsible for detecting, serializing, and
    deserializing a specific Python type. Handlers are registered
    with the serialization system and applied in order.
    """
    
    def can_handle(self, obj: Any) -> bool:
        """
        Check if this handler can process the given object.
        
        Parameters
        ----------
        obj : any
            Object to check
            
        Returns
        -------
        bool
            True if this handler can process the object
        """
        raise NotImplementedError("Subclasses must implement can_handle()")
    
    def serialize(self, obj: Any) -> Any:
        """
        Convert object to JSON-compatible representation.
        
        Parameters
        ----------
        obj : any
            Object to serialize
            
        Returns
        -------
        any
            JSON-compatible representation
        """
        raise NotImplementedError("Subclasses must implement serialize()")
    
    def can_deserialize(self, data: Any) -> bool:
        """
        Check if this handler can deserialize the given data.
        
        Parameters
        ----------
        data : any
            JSON data to check
            
        Returns
        -------
        bool
            True if this handler can deserialize the data
        """
        raise NotImplementedError("Subclasses must implement can_deserialize()")
    
    def deserialize(self, data: Any) -> Any:
        """
        Convert JSON-compatible data back to original object.
        
        Parameters
        ----------
        data : any
            JSON-compatible data
            
        Returns
        -------
        any
            Restored Python object
        """
        raise NotImplementedError("Subclasses must implement deserialize()")


class TupleHandler(TypeHandler):
    """Handler for tuple preservation - the main feature of zarrcompatibility."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, tuple)
    
    def serialize(self, obj: tuple) -> Dict[str, Any]:
        """Convert tuple to type-preserved dict."""
        return {
            TUPLE_TYPE_MARKER: TUPLE_TYPE_VALUE,
            TUPLE_DATA_MARKER: list(obj)
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get(TUPLE_TYPE_MARKER) == TUPLE_TYPE_VALUE and
            TUPLE_DATA_MARKER in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> tuple:
        """Restore tuple from type-preserved dict."""
        return tuple(data[TUPLE_DATA_MARKER])


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
    """Handler for Enum objects."""
    
    def can_handle(self, obj: Any) -> bool:
        return isinstance(obj, Enum)
    
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
        try:
            # Import the enum class
            module_name, class_name = data["__class__"].rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            enum_class = getattr(module, class_name)
            
            # Create enum instance from value
            return enum_class(data["__data__"])
        except Exception as e:
            # Fallback: return just the value if enum class can't be imported
            return data["__data__"]


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
        """Convert dataclass to dict with type info."""
        return {
            "__type__": "dataclass",
            "__class__": f"{obj.__class__.__module__}.{obj.__class__.__qualname__}",
            "__data__": asdict(obj)
        }
    
    def can_deserialize(self, data: Any) -> bool:
        return (
            isinstance(data, dict) and 
            data.get("__type__") == "dataclass" and
            "__class__" in data and
            "__data__" in data
        )
    
    def deserialize(self, data: Dict[str, Any]) -> Any:
        """Restore dataclass from dict and class info."""
        try:
            # Import the dataclass
            module_name, class_name = data["__class__"].rsplit(".", 1)
            module = __import__(module_name, fromlist=[class_name])
            dataclass_type = getattr(module, class_name)
            
            # Create instance from dict
            return dataclass_type(**data["__data__"])
        except Exception:
            # Fallback: return just the data dict
            return data["__data__"]


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
    """
    Register a custom type handler.
    
    Parameters
    ----------
    handler : TypeHandler
        The type handler to register
    priority : int, default 0
        Priority for handler (higher = checked first)
    """
    if priority > 0:
        _TYPE_HANDLERS.insert(0, handler)
    else:
        _TYPE_HANDLERS.append(handler)


def serialize_object(obj: Any) -> Any:
    """
    Serialize an object to JSON-compatible form using registered handlers.
    
    This function tries to find an appropriate type handler for the object.
    If no handler is found, it falls back to basic JSON types or returns
    the object unchanged for JSON-compatible types.
    
    Parameters
    ----------
    obj : any
        Object to serialize
        
    Returns
    -------
    any
        JSON-compatible representation of the object
    """
    # Handle basic JSON types first
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Try registered type handlers
    for handler in _TYPE_HANDLERS:
        if handler.can_handle(obj):
            try:
                return handler.serialize(obj)
            except Exception:
                # If handler fails, continue to next one
                continue
    
    # Handle collections recursively
    if isinstance(obj, dict):
        return {key: serialize_object(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        # Note: tuples should be handled by TupleHandler above
        return [serialize_object(item) for item in obj]
    elif isinstance(obj, set):
        return {"__type__": "set", "__data__": [serialize_object(item) for item in obj]}
    
    # Fallback: try to convert to string
    try:
        return str(obj)
    except Exception:
        return f"<Unserializable: {type(obj).__name__}>"


def deserialize_object(data: Any) -> Any:
    """
    Deserialize JSON-compatible data back to Python objects using registered handlers.
    
    This function tries to find an appropriate type handler that can deserialize
    the data. If no handler is found, it returns the data as-is or processes
    it recursively if it's a collection.
    
    Parameters
    ----------
    data : any
        JSON-compatible data to deserialize
        
    Returns
    -------
    any
        Restored Python object
    """
    # Handle basic JSON types
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    
    # Try registered type handlers
    if isinstance(data, dict):
        for handler in _TYPE_HANDLERS:
            if handler.can_deserialize(data):
                try:
                    return handler.deserialize(data)
                except Exception:
                    # If handler fails, continue to next one
                    continue
        
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
    """
    Get list of supported types for serialization.
    
    Returns
    -------
    list of str
        List of type names that can be serialized
    """
    return [
        "tuple", "datetime", "date", "time", "enum", "uuid", 
        "dataclass", "complex", "bytes", "decimal", "set"
    ]


def test_type_roundtrip(obj: Any, verbose: bool = False) -> bool:
    """
    Test if an object can roundtrip through serialization successfully.
    
    Parameters
    ----------
    obj : any
        Object to test
    verbose : bool, default False
        If True, print detailed test information
        
    Returns
    -------
    bool
        True if roundtrip successful, False otherwise
    """
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
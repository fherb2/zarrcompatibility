"""
Universal JSON Serialization Module for Zarr Compatibility

This module provides universal JSON serialization capabilities for any Python class,
making them compatible with Zarr and other systems that require JSON serialization.

## Key Features:

* Works with ANY Python class (dataclasses, regular classes, enums)
* Automatic serialization/deserialization with tuple preservation
* Zarr-compatible out of the box
* No class modification required (optional enhancements available)
* Single import and setup

## Usage:

    import zarrcompatibility as zc
    
    # One-time setup (call once at program start)
    zc.enable_universal_serialization()
    
    # Now ALL your classes work with json.dumps() and Zarr!
    json.dumps(your_object)  # Just works!

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


# =============================================================================
# Core Serialization Functions
# =============================================================================

def serialize_object(obj: Any) -> Any:
    """
    Universal object serializer that handles any Python object.
    
    This function tries multiple strategies to serialize an object:
    1. Basic JSON types (pass through)
    2. Objects with __json__() method
    3. Objects with to_dict() method  
    4. Dataclasses (via dataclasses.asdict)
    5. Enums (via .value)
    6. Callable objects without __dict__ (converted to string)
    7. Built-in types (datetime, UUID, Decimal, etc.)
    8. Objects with __dict__ attribute
    9. Iterables (lists, tuples, sets)
    10. Mappings (dictionaries)
    11. Fallback to string representation
    
    Args:
        obj: Any Python object to serialize
        
    Returns:
        JSON-serializable representation of the object
    """
    # 1. Basic JSON types - pass through unchanged
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    # 2. Objects with explicit __json__ method (highest priority)
    if hasattr(obj, '__json__') and callable(getattr(obj, '__json__')):
        try:
            result = obj.__json__()
            # Recursively serialize the result in case it contains complex objects
            return serialize_object(result) if not isinstance(result, (str, int, float, bool, type(None))) else result
        except Exception:
            pass  # Fall through to next strategy
    
    # 3. Objects with to_dict method
    if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        try:
            result = obj.to_dict()
            return serialize_object(result)
        except Exception:
            pass
    
    # 4. Dataclasses - use dataclasses.asdict
    if is_dataclass(obj):
        try:
            result = asdict(obj)
            return serialize_object(result)
        except Exception:
            pass
    
    # 5. Enums - use .value
    if isinstance(obj, Enum):
        return serialize_object(obj.value)
    
    # 6. Check for callable objects before checking __dict__
    if callable(obj) and not hasattr(obj, '__dict__'):
        # Lambda functions and other callables without __dict__
        try:
            return str(obj)
        except Exception:
            pass
    
    # 7. Built-in types that need special handling
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, time):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, bytes):
        # Convert bytes to base64 string
        return base64.b64encode(obj).decode('ascii')
    elif isinstance(obj, complex):
        return {'real': obj.real, 'imag': obj.imag, '_type': 'complex'}
    
    # 8. Objects with __dict__ (most regular Python classes)
    if hasattr(obj, '__dict__'):
        try:
            # Create dict from object attributes, excluding private/callable attributes
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_') and not callable(value):
                    result[key] = serialize_object(value)
            # If result is empty and object has callable attributes, it might be a function
            if not result and callable(obj):
                return str(obj)
            return result
        except Exception:
            pass
    
    # 9. Iterables (lists, tuples, sets)
    if hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, dict)):
        try:
            if isinstance(obj, (list, tuple)):
                return [serialize_object(item) for item in obj]
            elif isinstance(obj, set):
                return list(serialize_object(item) for item in obj)
            else:
                # Other iterables
                return [serialize_object(item) for item in obj]
        except Exception:
            pass
    
    # 10. Mappings (dictionaries and dict-like objects)
    if hasattr(obj, 'items'):
        try:
            return {str(key): serialize_object(value) for key, value in obj.items()}
        except Exception:
            pass
    
    # 11. Fallback - convert to string
    try:
        return str(obj)
    except Exception:
        return f"<Unserializable: {type(obj).__name__}>"


def deserialize_object(data: Any, target_class: Optional[Type] = None) -> Any:
    """
    Universal object deserializer.
    
    Attempts to reconstruct objects from their JSON representation.
    Works best when target_class is provided, but can handle basic cases automatically.
    Supports dataclasses and classes with appropriate constructors.
    
    Args:
        data: JSON data (typically dict) to deserialize
        target_class: Optional target class to deserialize into
        
    Returns:
        Reconstructed object or the original data if no deserialization is possible
    """
    # Basic types - return as is
    if data is None or isinstance(data, (str, int, float, bool)):
        return data
    
    # Lists - recursively deserialize items
    if isinstance(data, list):
        return [deserialize_object(item, target_class) for item in data]
    
    # Dictionaries
    if isinstance(data, dict):
        # Special handling for complex numbers
        if data.get('_type') == 'complex':
            return complex(data['real'], data['imag'])
        
        # If target class is provided, try to construct it
        if target_class:
            try:
                # Try direct construction from dict
                if hasattr(target_class, 'from_json') and callable(getattr(target_class, 'from_json')):
                    return target_class.from_json(data)
                elif hasattr(target_class, 'from_dict') and callable(getattr(target_class, 'from_dict')):
                    return target_class.from_dict(data)
                elif is_dataclass(target_class):
                    # For dataclasses, try direct construction
                    return target_class(**data)
                else:
                    # Try constructor with kwargs
                    return target_class(**data)
            except Exception:
                # If construction fails, return the dict
                pass
        
        # Recursively deserialize dict values
        return {key: deserialize_object(value) for key, value in data.items()}
    
    return data


# =============================================================================
# JSON Encoder Patching
# =============================================================================

class UniversalJSONEncoder(json.JSONEncoder):
    """Universal JSON encoder that handles tuples and other Python objects."""
    
    def encode(self, obj: Any) -> str:
        """Override encode to handle nested tuples and complex objects."""
        converted_obj = self._convert_tuples_recursive(obj)
        return super().encode(converted_obj)
    
    def _convert_tuples_recursive(self, obj: Any) -> Any:
        """Recursively convert tuples to type-preserved dictionaries."""
        if isinstance(obj, tuple):
            return {"__type__": "tuple", "__data__": list(obj)}
        elif isinstance(obj, dict):
            return {key: self._convert_tuples_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_tuples_recursive(item) for item in obj]
        else:
            # For other complex objects, use existing serialization logic
            return serialize_object(obj)
    
    def default(self, obj: Any) -> Any:
        """Fallback for objects that couldn't be handled by encode."""
        return serialize_object(obj)

def universal_object_hook(data: Any) -> Any:
    """Object hook that restores tuples and other Python objects."""
    if isinstance(data, dict):
        # Restore tuples
        if data.get("__type__") == "tuple" and "__data__" in data:
            return tuple(data["__data__"])
        
        # Process nested structures
        return {key: universal_object_hook(value) for key, value in data.items()}
    
    elif isinstance(data, list):
        return [universal_object_hook(item) for item in data]
    
    return data


# Global reference to original JSON functions for restoration
_original_json_default: Optional[Callable] = None


def enable_universal_serialization() -> None:
    """Enable universal JSON serialization with automatic tuple preservation."""
    
    # Store originals for potential restoration
    if not hasattr(json, '_original_dumps'):
        json._original_dumps = json.dumps
        json._original_loads = json.loads
    
    def enhanced_dumps(obj: Any, cls: Optional[Type[json.JSONEncoder]] = None, **kwargs: Any) -> str:
        if cls is None:
            cls = UniversalJSONEncoder
        return json._original_dumps(obj, cls=cls, **kwargs)
    
    def enhanced_loads(s: str, object_hook: Optional[Callable[[Dict[str, Any]], Any]] = None, **kwargs: Any) -> Any:
        if object_hook is None:
            object_hook = universal_object_hook
        return json._original_loads(s, object_hook=object_hook, **kwargs)
    
    # Patch JSON module
    json.dumps = enhanced_dumps
    json.loads = enhanced_loads
    
    # PATCH ZARR'S METADATA SERIALIZATION for tuple preservation
    try:
        import zarr.core.metadata.v3
        
        # Patch ArrayV3Metadata.to_buffer_dict
        original_to_buffer_dict = zarr.core.metadata.v3.ArrayV3Metadata.to_buffer_dict
        
        def enhanced_to_buffer_dict(self, prototype):
            # Get the original dict
            d = self.to_dict()
            
            # Convert tuples recursively before JSON encoding
            def convert_tuples(obj):
                if isinstance(obj, tuple):
                    return {"__type__": "tuple", "__data__": list(obj)}
                elif isinstance(obj, dict):
                    return {k: convert_tuples(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_tuples(item) for item in obj]
                else:
                    return obj
            
            d_converted = convert_tuples(d)
            
            # Apply special floats replacement and encode
            from zarr.core.metadata.v3 import _replace_special_floats, ZARR_JSON, V3JsonEncoder
            d_final = _replace_special_floats(d_converted)
            
            return {ZARR_JSON: prototype.buffer.from_bytes(json.dumps(d_final, cls=V3JsonEncoder).encode())}
        
        zarr.core.metadata.v3.ArrayV3Metadata.to_buffer_dict = enhanced_to_buffer_dict
        
        # Also patch GroupMetadata if it exists (for groups)
        if hasattr(zarr.core.metadata.v3, 'GroupV3Metadata'):
            zarr.core.metadata.v3.GroupV3Metadata.to_buffer_dict = enhanced_to_buffer_dict
        
    except ImportError:
        # Zarr not available or different version
        pass

    # PATCH ZARR'S METADATA SERIALIZATION for tuple preservation
    try:
        import zarr.core.metadata.v3
        
        # ... (bestehender ArrayV3Metadata Patch) ...
        
        # HIER HINZUFÜGEN:
        # Also patch GroupMetadata for groups
        import zarr.core.group
        if hasattr(zarr.core.group, 'GroupMetadata'):
            zarr.core.group.GroupMetadata.to_buffer_dict = enhanced_to_buffer_dict
        
    except ImportError:
        # Zarr not available or different version
        pass

def disable_universal_serialization() -> None:
    """
    Disable universal JSON serialization and restore original behavior.
    
    This restores the original json.dumps and json.loads functions.
    """
    if hasattr(json, '_original_dumps'):
        json.dumps = json._original_dumps
        json.loads = json._original_loads
        delattr(json, '_original_dumps')
        delattr(json, '_original_loads')
        print("Universal JSON serialization disabled, original behavior restored.")
    else:
        print("Warning: Universal serialization was not enabled.")


# =============================================================================
# Mixin Classes for Enhanced Functionality
# =============================================================================

class JSONSerializable:
    """
    Mixin class that adds JSON serialization methods to any class.
    
    This mixin provides robust serialization methods that preserve native
    Python types (lists, dicts) and handle complex nested structures.
    
    Usage:
        class MyClass(JSONSerializable):
            def __init__(self, value):
                self.value = value
        
        obj = MyClass(42)
        json_str = obj.to_json()
        obj_copy = MyClass.from_json(json_str)
    
    Methods:
        __json__(): Returns dict representation for JSON serialization
        to_dict(): Converts object to dictionary, preserving native types
        to_json(): Converts object to JSON string
        from_dict(): Class method to create instance from dictionary
        from_json(): Class method to create instance from JSON string
    """
    
    def __json__(self) -> Dict[str, Any]:
        """Return JSON-serializable representation."""
        return self.to_dict()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert object to dictionary.
        
        Preserves native Python types (lists, dicts, etc.) without 
        over-serialization to strings. Only serializes complex objects
        that are not JSON-compatible.
        
        Returns:
            Dict representation of the object
        """
        if hasattr(self, '__dict__'):
            result = {}
            for key, value in self.__dict__.items():
                if not key.startswith('_') and not callable(value):
                    # Only serialize complex objects, keep simple types as-is
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        result[key] = value
                    else:
                        result[key] = serialize_object(value)
            return result
        return {}
    
    def to_json(self, **kwargs: Any) -> str:
        """
        Convert object to JSON string.
        
        Uses the object's dict representation to avoid double-serialization
        issues that can occur when complex objects are serialized multiple times.
        
        Args:
            **kwargs: Additional arguments passed to json.dumps()
            
        Returns:
            JSON string representation of the object
        """
        dict_repr = self.to_dict()
        return json.dumps(dict_repr, **kwargs)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        """
        Create instance from dictionary.
        
        Attempts direct construction first, then falls back to
        deserialization methods. Handles various edge cases
        robustly.
        
        Args:
            data: Dictionary containing object data
            
        Returns:
            Instance of this class
        """
        if not isinstance(data, dict):
            return data
            
        try:
            # Try direct construction first
            return cls(**data)
        except Exception:
            # If that fails, try deserialize_object
            result = deserialize_object(data, cls)
            if isinstance(result, cls):
                return result
            elif isinstance(result, dict):
                try:
                    return cls(**result)
                except Exception:
                    return result
            else:
                return result
    
    @classmethod
    def from_json(cls, json_str: str) -> Any:
        """Create instance from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class ZarrCompatible(JSONSerializable):
    """
    Enhanced mixin specifically designed for Zarr compatibility.
    
    Provides additional methods for working with Zarr metadata and attributes.
    Includes intelligent parameter filtering to handle cases where stored
    data contains more fields than the constructor expects.
    
    Example:
        class ExperimentInfo(ZarrCompatible):
            def __init__(self, name, version):
                self.name = name
                self.version = version
                self.created_at = datetime.now()  # Auto-added field
        
        info = ExperimentInfo("test", "1.0")
        info.save_to_zarr_group(zarr_group)
        loaded = ExperimentInfo.load_from_zarr_group(zarr_group)
    """
    
    def to_zarr_attrs(self) -> Dict[str, Any]:
        """
        Convert object to Zarr-compatible attributes dictionary.
        
        Returns:
            Dictionary suitable for storing in Zarr .zattrs
        """
        return self.to_dict()
    
    @classmethod
    def from_zarr_attrs(cls, attrs: Dict[str, Any]) -> Any:
        """
        Create instance from Zarr attributes dictionary.
        
        Args:
            attrs: Dictionary loaded from Zarr .zattrs
            
        Returns:
            Instance of this class
        """
        return cls.from_dict(attrs)
    
    def save_to_zarr_group(self, zarr_group: Any, attr_name: str = 'metadata') -> None:
        """
        Save this object to a Zarr group as attributes.
        
        Args:
            zarr_group: Zarr group object
            attr_name: Name of the attribute to store this object under
        """
        attrs_dict = self.to_zarr_attrs()
        zarr_group.attrs[attr_name] = attrs_dict
    
    @classmethod
    def load_from_zarr_group(cls, zarr_group: Any, attr_name: str = 'metadata') -> Any:
        """
        Load this object from a Zarr group's attributes.
        
        Intelligently handles parameter filtering - only passes constructor
        parameters that the class actually accepts, ignoring additional
        fields that may have been stored (like auto-generated timestamps).
        
        Args:
            zarr_group: Zarr group object
            attr_name: Name of the attribute to load this object from
            
        Returns:
            Instance of this class
        """
        import inspect
        
        attrs = zarr_group.attrs[attr_name]
        
        # Handle different cases of what might be stored
        if isinstance(attrs, cls):
            # Already the right type
            return attrs
        elif isinstance(attrs, dict):
            # Dictionary - construct object directly
            try:
                # Get constructor parameters
                sig = inspect.signature(cls.__init__)
                valid_params = list(sig.parameters.keys())
                valid_params.remove('self')  # Remove 'self' parameter
                
                # Filter dict to only include valid constructor parameters
                filtered_attrs = {k: v for k, v in attrs.items() if k in valid_params}
                
                # Try direct construction with filtered dict
                return cls(**filtered_attrs)
            except Exception:
                try:
                    return cls.from_zarr_attrs(attrs)
                except Exception:
                    return attrs
        else:
            # Try to convert whatever we have to dict first
            if hasattr(attrs, '__dict__'):
                attrs_dict = {key: value for key, value in attrs.__dict__.items() 
                             if not key.startswith('_') and not callable(value)}
                try:
                    return cls(**attrs_dict)
                except Exception:
                    return cls.from_zarr_attrs(attrs_dict)
            else:
                return attrs


# =============================================================================
# Utility Functions
# =============================================================================

def make_serializable(cls: Type) -> Type:
    """
    Class decorator that adds JSON serialization methods to any class.
    
    This is an alternative to using the JSONSerializable mixin.
    Adds the same robust serialization methods with proper parameter
    filtering and native type preservation.
    
    Usage:
        @make_serializable
        class MyClass:
            def __init__(self, value):
                self.value = value
        
        obj = MyClass(42)
        json.dumps(obj)  # Works with global serialization enabled
        obj.to_json()    # Also works directly
    
    Args:
        cls: Class to make serializable
        
    Returns:
        Enhanced class with serialization methods
    """
    # Add __json__ method
    cls.__json__ = lambda self: serialize_object(self)
    
    # Add to_dict method
    def to_dict_method(self) -> Dict[str, Any]:
        if hasattr(self, '__dict__'):
            result = {}
            for key, value in self.__dict__.items():
                if not key.startswith('_') and not callable(value):
                    # Only serialize complex objects, keep simple types as-is
                    if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                        result[key] = value
                    else:
                        result[key] = serialize_object(value)
            return result
        return {}
    cls.to_dict = to_dict_method
    
    # Add to_json method - use dict representation to avoid double serialization
    def to_json_method(self, **kwargs: Any) -> str:
        dict_repr = self.to_dict()
        return json.dumps(dict_repr, **kwargs)
    cls.to_json = to_json_method
    
    # Add from_dict class method
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Any:
        if not isinstance(data, dict):
            return data
            
        try:
            # Try direct construction first
            return cls(**data)
        except Exception:
            # If that fails, try deserialize_object
            result = deserialize_object(data, cls)
            if isinstance(result, cls):
                return result
            elif isinstance(result, dict):
                try:
                    return cls(**result)
                except Exception:
                    return result
            else:
                return result
    cls.from_dict = from_dict
    
    # Add from_json class method
    @classmethod
    def from_json(cls, json_str: str) -> Any:
        data = json.loads(json_str)
        return cls.from_dict(data)
    cls.from_json = from_json
    
    return cls


def is_json_serializable(obj: Any) -> bool:
    """
    Check if an object can be JSON serialized.
    
    Args:
        obj: Object to check
        
    Returns:
        True if object can be serialized, False otherwise
    """
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False


def prepare_for_zarr(obj: Any) -> Any:
    """
    Prepare any object for Zarr storage by ensuring it's JSON serializable.
    
    This function explicitly converts objects to their JSON-serializable form
    without relying on global patching.
    
    Args:
        obj: Object to prepare for Zarr
        
    Returns:
        JSON-serializable version of the object
    """
    return serialize_object(obj)


def test_serialization(obj: Any, verbose: bool = True) -> bool:
    """
    Test if an object can be successfully serialized and deserialized.
    
    Args:
        obj: Object to test
        verbose: Whether to print detailed results
        
    Returns:
        True if serialization/deserialization works, False otherwise
    """
    try:
        # Serialize
        serialized = serialize_object(obj)
        
        # Convert to JSON and back
        json_str = json.dumps(serialized)
        json_data = json.loads(json_str)
        
        # Try to deserialize
        deserialized = deserialize_object(json_data, type(obj))
        
        if verbose:
            print(f"Serialization test passed for {type(obj).__name__}")
            print(f"   Original: {obj}")
            print(f"   Serialized: {serialized}")
            print(f"   Deserialized: {deserialized}")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"Serialization test failed for {type(obj).__name__}: {e}")
        return False


# =============================================================================
# Module Information
# =============================================================================

__version__ = "1.0.0"
__author__ = "Universal JSON Serialization Module"
__description__ = "Universal JSON serialization for Python objects with Zarr compatibility"


if __name__ == "__main__":
    # Demo/test code when module is run directly
    print("Universal JSON Serialization Module Demo")
    print("=" * 50)
    
    # Enable universal serialization
    enable_universal_serialization()
    
    # Test with various object types
    from dataclasses import dataclass
    
    # Test enum
    class Status(Enum):
        READY = "ready"
        PROCESSING = "processing"
    
    # Test regular class
    class RegularClass:
        def __init__(self, name: str, value: int) -> None:
            self.name = name
            self.value = value
    
    # Test dataclass
    @dataclass
    class DataClass:
        name: str
        count: int
    
    # Test with mixin
    class MixinClass(JSONSerializable):
        def __init__(self, data: Dict[str, Any]) -> None:
            self.data = data
    
    # Run tests
    test_objects: List[Any] = [
        Status.READY,
        RegularClass("test", 42),
        DataClass("example", 100),
        MixinClass({"nested": "data"}),
        datetime.now(),
        [1, 2, {"key": "value"}],
        (1, 0),  # Test tuple preservation
    ]
    
    for obj in test_objects:
        test_serialization(obj)
        print()
    
    print("All tests completed!")
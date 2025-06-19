"""
JSON serialization functions for zarrcompatibility.

This module provides enhanced JSON serialization functions that work with
the type handlers to convert Python objects to JSON and back. The functions
are designed to be drop-in replacements for Zarr's internal JSON functions.

The module provides both the core serialization logic and testing utilities
for validating that objects can be properly serialized and deserialized.

Key Functions:
    - enhanced_json_dumps(): Enhanced JSON serialization with type preservation
    - enhanced_json_loads(): Enhanced JSON deserialization with type restoration  
    - test_object_serialization(): Test serialization of specific objects
    - create_zarr_json_encoder(): Create custom JSON encoder for Zarr

Author: F. Herbrand
License: MIT
"""

import json
import warnings
from typing import Any, Dict, Optional, Type

from . import type_handlers


class ZarrCompatibilityJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles zarrcompatibility types.
    
    This encoder automatically converts supported Python types to their
    JSON-compatible representations using the registered type handlers.
    It serves as a bridge between the type handler system and Python's
    built-in JSON encoder.
    """
    
    def default(self, obj: Any) -> Any:
        """
        Convert objects to JSON-serializable form.
        
        This method is called by json.dumps() for objects that are not
        natively JSON-serializable.
        
        Parameters
        ----------
        obj : any
            Object to serialize
            
        Returns
        -------
        any
            JSON-serializable representation
        """
        # Use type handlers to serialize
        serialized = type_handlers.serialize_object(obj)
        
        # If serialization didn't change the object, call parent
        if serialized is obj:
            return super().default(obj)
        
        return serialized


def enhanced_json_dumps(obj: Any, **kwargs) -> str:
    """
    Enhanced JSON dumps with type preservation for zarrcompatibility.
    
    This function is a drop-in replacement for json.dumps() that adds
    support for additional Python types including tuples, datetime objects,
    enums, UUIDs, dataclasses, and more.
    
    Parameters
    ----------
    obj : any
        Object to serialize to JSON
    **kwargs
        Additional keyword arguments passed to json.dumps()
        
    Returns
    -------
    str
        JSON string representation
        
    Examples
    --------
    >>> from zarrcompatibility.serializers import enhanced_json_dumps
    >>> enhanced_json_dumps((1, 2, 3))
    '{"__type__": "tuple", "__data__": [1, 2, 3]}'
    
    >>> from datetime import datetime
    >>> enhanced_json_dumps(datetime(2025, 1, 19, 12, 0))
    '{"__type__": "datetime", "__subtype__": "datetime", "__data__": "2025-01-19T12:00:00"}'
    """
    # Use our custom encoder by default
    if 'cls' not in kwargs:
        kwargs['cls'] = ZarrCompatibilityJSONEncoder
    
    return json.dumps(obj, **kwargs)


def enhanced_json_loads(s: str, **kwargs) -> Any:
    """
    Enhanced JSON loads with type restoration for zarrcompatibility.
    
    This function is a drop-in replacement for json.loads() that restores
    Python objects from their JSON representations created by enhanced_json_dumps().
    
    Parameters
    ----------
    s : str
        JSON string to deserialize
    **kwargs
        Additional keyword arguments passed to json.loads()
        
    Returns
    -------
    any
        Restored Python object
        
    Examples
    --------
    >>> from zarrcompatibility.serializers import enhanced_json_loads
    >>> enhanced_json_loads('{"__type__": "tuple", "__data__": [1, 2, 3]}')
    (1, 2, 3)
    
    >>> enhanced_json_loads('{"__type__": "datetime", "__subtype__": "datetime", "__data__": "2025-01-19T12:00:00"}')
    datetime.datetime(2025, 1, 19, 12, 0)
    """
    # Load JSON normally first
    data = json.loads(s, **kwargs)
    
    # Then deserialize using type handlers
    return type_handlers.deserialize_object(data)


def convert_for_zarr_json(obj: Any) -> Any:
    """
    Convert an object to a form suitable for Zarr JSON serialization.
    
    This function performs the type conversion step without actually
    serializing to JSON. It's useful for preparing objects for Zarr's
    internal JSON processing.
    
    Parameters
    ----------
    obj : any
        Object to convert
        
    Returns
    -------
    any
        Object converted to JSON-compatible form
    """
    return type_handlers.serialize_object(obj)


def restore_from_zarr_json(data: Any) -> Any:
    """
    Restore objects from Zarr JSON-compatible form.
    
    This function performs the type restoration step on data that has
    already been loaded from JSON. It's the counterpart to convert_for_zarr_json().
    
    Parameters
    ----------
    data : any
        JSON-compatible data to restore
        
    Returns
    -------
    any
        Restored Python object
    """
    return type_handlers.deserialize_object(data)


def test_object_serialization(obj: Any, verbose: bool = True) -> bool:
    """
    Test if an object can be successfully serialized and deserialized.
    
    This function performs a complete round-trip test: object → JSON → object,
    verifying that the result matches the original in both value and type.
    
    Parameters
    ----------
    obj : any
        Object to test
    verbose : bool, default True
        If True, print detailed test results
        
    Returns
    -------
    bool
        True if serialization test passes, False otherwise
        
    Examples
    --------
    >>> from zarrcompatibility.serializers import test_object_serialization
    >>> test_object_serialization((1, 2, 3))
    Serialization test passed for tuple
       Original: (1, 2, 3)
       JSON: {"__type__": "tuple", "__data__": [1, 2, 3]}
       Restored: (1, 2, 3)
       Type preserved: True
    True
    """
    try:
        # Serialize to JSON
        json_str = enhanced_json_dumps(obj)
        
        # Deserialize from JSON
        restored = enhanced_json_loads(json_str)
        
        # Check if restoration was successful
        value_match = obj == restored
        type_match = type(obj) == type(restored)
        success = value_match and type_match
        
        if verbose:
            obj_type = type(obj).__name__
            if success:
                print(f"✅ Serialization test passed for {obj_type}")
            else:
                print(f"❌ Serialization test failed for {obj_type}")
            
            print(f"   Original: {obj!r}")
            print(f"   JSON: {json_str}")
            print(f"   Restored: {restored!r}")
            print(f"   Type preserved: {type_match}")
            
            if not success:
                print(f"   Value match: {value_match}")
                if not type_match:
                    print(f"   Expected type: {type(obj)}")
                    print(f"   Actual type: {type(restored)}")
        
        return success
        
    except Exception as e:
        if verbose:
            obj_type = type(obj).__name__
            print(f"❌ Serialization test failed for {obj_type}: {e}")
        return False


def test_json_compatibility() -> Dict[str, bool]:
    """
    Test serialization compatibility with various Python types.
    
    This function runs comprehensive tests on all supported types to
    verify that the serialization system is working correctly.
    
    Returns
    -------
    dict
        Dictionary mapping type names to test results (True/False)
    """
    from datetime import datetime, date, time
    from enum import Enum
    from uuid import uuid4
    from dataclasses import dataclass
    from decimal import Decimal
    
    # Test enum
    class TestEnum(Enum):
        OPTION_A = "a"
        OPTION_B = "b"
    
    # Test dataclass  
    @dataclass
    class TestDataclass:
        name: str
        value: int
    
    # Test objects
    test_cases = {
        "tuple": (1, 2, 3),
        "nested_tuple": (1, (2, 3), 4),
        "datetime": datetime(2025, 1, 19, 12, 0, 0),
        "date": date(2025, 1, 19),
        "time": time(12, 0, 0),
        "enum": TestEnum.OPTION_A,
        "uuid": uuid4(),
        "dataclass": TestDataclass("test", 42),
        "complex": 1 + 2j,
        "bytes": b"test data",
        "decimal": Decimal("123.456"),
        "set": {1, 2, 3},
        "nested_dict": {"tuple": (1, 2), "datetime": datetime.now()},
        "list_with_tuples": [(1, 2), (3, 4)],
    }
    
    results = {}
    for name, obj in test_cases.items():
        results[name] = test_object_serialization(obj, verbose=False)
    
    return results


def print_compatibility_report() -> None:
    """
    Print a comprehensive compatibility report for all supported types.
    
    This function runs tests on all supported types and prints a formatted
    report showing which types work correctly and which have issues.
    """
    print("🧪 zarrcompatibility Serialization Compatibility Report")
    print("=" * 60)
    
    results = test_json_compatibility()
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"📊 Overall: {passed}/{total} types working correctly")
    print()
    
    # Group results
    working = []
    failing = []
    
    for type_name, success in results.items():
        if success:
            working.append(type_name)
        else:
            failing.append(type_name)
    
    if working:
        print("✅ Working Types:")
        for type_name in sorted(working):
            print(f"   - {type_name}")
        print()
    
    if failing:
        print("❌ Failing Types:")
        for type_name in sorted(failing):
            print(f"   - {type_name}")
        print()
        print("⚠️  Some types are not working correctly. This may indicate")
        print("   a configuration issue or missing dependencies.")
    else:
        print("🎉 All supported types are working correctly!")
    
    print()
    print("💡 To test a specific object:")
    print("   from zarrcompatibility.serializers import test_object_serialization")
    print("   test_object_serialization(your_object)")


if __name__ == "__main__":
    # Run compatibility tests when module is executed directly
    print_compatibility_report()

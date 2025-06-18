# zarrcompatibility Tuple Serialization Issue

## Problem Summary

The zarrcompatibility library successfully serializes Python tuples to JSON (as arrays), but does not provide automatic deserialization back to tuples. This creates data type inconsistencies when storing and retrieving tuple metadata in Zarr arrays, particularly affecting version numbers and other tuple-based configuration data.

## Current Behavior

### What Works
```python
import zarrcompatibility as zc
import json

zc.enable_universal_serialization()

# Serialization works fine
version_tuple = (1, 0)
serialized = json.dumps(version_tuple)  # Results in: "[1, 0]"
```

### What Doesn't Work
```python
# Deserialization loses type information
deserialized = json.loads(serialized)  # Results in: [1, 0] (list, not tuple)

# This causes comparison failures
assert version_tuple == deserialized  # FAILS! (1, 0) != [1, 0]
```

## Real-World Impact

### Use Case: Audio Database Version Management
In the zarrwlr (Zarr Wildlife Recording) project, we store version tuples in Zarr group attributes:

```python
from zarrwlr.config import Config
import zarr

# Configuration defines version as tuple
Config.original_audio_group_version = (1, 0)  # tuple

# Zarr group creation
audio_group = zarr.open_group("audio.zarr", mode="w")
audio_group.attrs["version"] = Config.original_audio_group_version

# Later validation fails due to type mismatch
stored_version = audio_group.attrs["version"]  # [1, 0] (list)
if stored_version == Config.original_audio_group_version:  # FAILS!
    print("Version matches")
```

### Current Workaround Required
```python
# Manual type conversion needed everywhere
stored_version = audio_group.attrs["version"]
if isinstance(stored_version, list):
    stored_version = tuple(stored_version)

if stored_version == Config.original_audio_group_version:
    print("Version matches")  # Now works
```

## Technical Root Cause

1. **JSON Limitation**: JSON specification only supports arrays `[1, 0]`, not tuples
2. **Asymmetric Conversion**: zarrcompatibility converts `tuple → array` but not `array → tuple`
3. **Type Metadata Loss**: No information preserved about original tuple type during serialization

## Proposed Solutions

### Solution 1: Type-Aware Serialization (Recommended)

Add metadata to distinguish tuples from lists during serialization:

```python
# Enhanced serialization with type hints
def enhanced_serialize_tuple(obj):
    if isinstance(obj, tuple):
        return {
            "__type__": "tuple",
            "__data__": list(obj)
        }
    return obj

# Enhanced deserialization with type restoration
def enhanced_deserialize_tuple(data):
    if isinstance(data, dict) and data.get("__type__") == "tuple":
        return tuple(data["__data__"])
    return data
```

**Expected Result:**
```python
version_tuple = (1, 0)
serialized = json.dumps(version_tuple)  
# Results in: '{"__type__": "tuple", "__data__": [1, 0]}'

deserialized = json.loads(serialized)
# Results in: (1, 0) - tuple restored!
```

### Solution 2: Smart Collection Detection

Implement heuristic-based tuple detection for specific patterns:

```python
def smart_tuple_detection(data):
    """Detect likely tuples based on usage patterns"""
    if isinstance(data, list):
        # Version numbers: [major, minor] or [major, minor, patch]
        if len(data) in [2, 3] and all(isinstance(x, int) for x in data):
            return tuple(data)
        
        # Coordinate pairs: [x, y] or [x, y, z]
        if len(data) in [2, 3] and all(isinstance(x, (int, float)) for x in data):
            return tuple(data)
    
    return data
```

### Solution 3: Configuration-Based Type Hints

Allow users to register tuple patterns:

```python
zc.register_tuple_pattern("version", pattern=r"version|ver")
zc.register_tuple_pattern("coordinates", pattern=r"pos|coord|point")

# Automatic detection for registered patterns
audio_group.attrs["version"] = (1, 0)      # Detected as tuple
audio_group.attrs["position"] = (10, 20)   # Detected as tuple
audio_group.attrs["data"] = [1, 2, 3]      # Remains list
```

## Implementation Requirements

### Core Features Needed

1. **Backward Compatibility**: Existing code must continue working
2. **Opt-in Behavior**: Enhanced tuple handling should be optional
3. **Performance**: Minimal overhead for non-tuple data
4. **Configurability**: Users can control tuple detection behavior

### API Design Proposal

```python
# New configuration options
zc.enable_universal_serialization(
    preserve_tuples=True,           # Enable tuple preservation
    tuple_detection="smart",        # "smart", "explicit", "off"
    tuple_patterns=["version", "pos"] # Pattern-based detection
)

# Alternative explicit API
zc.enable_tuple_preservation()
zc.register_tuple_patterns(["version", "coordinate", "point"])

# Per-object control
@zc.preserve_tuples
class ConfigClass:
    version = (1, 0)
    coordinates = (10, 20, 30)
```

## Test Cases

### Test 1: Basic Tuple Round-Trip
```python
def test_tuple_roundtrip():
    zc.enable_universal_serialization(preserve_tuples=True)
    
    original = (1, 0)
    serialized = json.dumps(original)
    deserialized = json.loads(serialized)
    
    assert isinstance(deserialized, tuple)
    assert deserialized == original
```

### Test 2: Mixed Collections
```python
def test_mixed_collections():
    zc.enable_universal_serialization(preserve_tuples=True)
    
    data = {
        "version": (1, 0),           # Should become tuple
        "items": [1, 2, 3],          # Should remain list
        "coordinates": (10.5, 20.3), # Should become tuple
        "nested": [(1, 2), [3, 4]]   # Mixed preservation
    }
    
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)
    
    assert isinstance(deserialized["version"], tuple)
    assert isinstance(deserialized["items"], list)
    assert isinstance(deserialized["coordinates"], tuple)
    assert isinstance(deserialized["nested"][0], tuple)
    assert isinstance(deserialized["nested"][1], list)
```

### Test 3: Zarr Integration
```python
def test_zarr_integration():
    zc.enable_universal_serialization(preserve_tuples=True)
    
    # Create Zarr group with tuple metadata
    group = zarr.open_group("test.zarr", mode="w")
    group.attrs["version"] = (1, 0)
    group.attrs["shape"] = (100, 200)
    group.attrs["tags"] = ["data", "experiment"]  # Should remain list
    
    # Reload and verify types
    reloaded = zarr.open_group("test.zarr", mode="r")
    
    assert isinstance(reloaded.attrs["version"], tuple)
    assert isinstance(reloaded.attrs["shape"], tuple)
    assert isinstance(reloaded.attrs["tags"], list)
```

### Test 4: Performance Benchmark
```python
def test_performance_impact():
    """Ensure tuple preservation doesn't significantly impact performance"""
    
    # Measure with tuple preservation off
    start = time.time()
    for _ in range(10000):
        json.dumps({"data": [1, 2, 3, 4, 5]})
    baseline_time = time.time() - start
    
    # Measure with tuple preservation on
    zc.enable_universal_serialization(preserve_tuples=True)
    start = time.time()
    for _ in range(10000):
        json.dumps({"data": [1, 2, 3, 4, 5]})
    enhanced_time = time.time() - start
    
    # Should not be more than 20% slower
    assert enhanced_time < baseline_time * 1.2
```

### Test 5: Backward Compatibility
```python
def test_backward_compatibility():
    """Ensure existing serialized data still works"""
    
    # Old format (without tuple preservation)
    old_serialized = '{"version": [1, 0], "data": [1, 2, 3]}'
    
    # Should work with new system
    zc.enable_universal_serialization(preserve_tuples=True)
    deserialized = json.loads(old_serialized)
    
    # Might be lists (backward compatibility) or tuples (smart detection)
    assert "version" in deserialized
    assert "data" in deserialized
```

## Configuration Examples

### Conservative Approach (Recommended for v1)
```python
# Only preserve tuples for known patterns
zc.enable_universal_serialization()
zc.register_tuple_patterns([
    "version", "ver", "shape", "dimensions", 
    "coordinates", "coord", "pos", "point"
])
```

### Aggressive Approach (For Advanced Users)
```python
# Preserve all probable tuples
zc.enable_universal_serialization(
    preserve_tuples=True,
    tuple_detection="smart",
    smart_heuristics=True
)
```

### Explicit Approach (Maximum Control)
```python
# Only preserve explicitly marked tuples
zc.enable_universal_serialization(preserve_tuples="explicit")

# Manual marking
data = {
    "version": zc.Tuple(1, 0),        # Explicit tuple
    "coords": zc.Tuple(10.5, 20.3),   # Explicit tuple
    "items": [1, 2, 3]                # Regular list
}
```

## Integration with zarrwlr

Once implemented, zarrwlr can:

1. **Remove Workarounds**: Delete manual tuple conversion code
2. **Enable Tuple Preservation**: Add to initialization
3. **Configure Patterns**: Register audio-specific tuple patterns

```python
# zarrwlr initialization
import zarrcompatibility as zc

zc.enable_universal_serialization(preserve_tuples=True)
zc.register_tuple_patterns([
    "version", "original_audio_group_version", 
    "original_audio_data_array_version"
])
```

## Priority and Impact

- **Priority**: Medium-High (affects data integrity and user experience)
- **Complexity**: Medium (requires careful design for backward compatibility)
- **Impact**: High (improves data type consistency across scientific applications)
- **User Benefit**: Eliminates manual type conversion workarounds

## Success Metrics

1. **Functional**: All test cases pass, including edge cases
2. **Performance**: <20% overhead for tuple-enabled serialization
3. **Compatibility**: Existing zarrcompatibility users unaffected
4. **Adoption**: zarrwlr can remove all tuple conversion workarounds

This issue represents a fundamental improvement to the zarrcompatibility library that will benefit the broader scientific Python community using Zarr for metadata storage.
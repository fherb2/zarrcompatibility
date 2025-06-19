# zarrcompatibility

**Universal JSON Serialization for Python Objects with Zarr Compatibility**

## Overview

`zarrcompatibility` is a Python library that makes **any Python object** compatible with JSON serialization and Zarr storage. It solves the common problem of storing complex metadata alongside scientific data in Zarr arrays, with **automatic tuple preservation** to maintain data type integrity.

**[Full documentation](https://fherb2.github.io/zarrcompatibility/)**

### The Problem

Zarr stores metadata as JSON, but Python's standard JSON serializer can't handle many common objects, and **converts tuples to lists**, breaking type consistency:

```python
import json
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    name: str
    timestamp: datetime
    version: tuple  # This becomes a list in JSON!
    params: dict

config = ExperimentConfig("exp_001", datetime.now(), (1, 0), {"lr": 0.001})

# This fails!
json.dumps(config)  # TypeError: Object of type ExperimentConfig is not JSON serializable

# Even basic tuples lose their type
version = (1, 0)
json_str = json.dumps(version)  # "[1, 0]" 
restored = json.loads(json_str)  # [1, 0] - now a list, not tuple!
assert version == restored  # FAILS! (1, 0) != [1, 0]
```

### Motivation

I first encountered this problem when I wanted to save the meta information from the original audio files in Zarr as attributes in addition to the audio PCM data arrays for my project [ZarrWildlifeRecording Library for Python](https://github.com/fherb2/zarr_wildlife_recording_py). Zarr saves attributes in files in JSON coding. Different structures and enums required individual special solutions in the application. The tuple-to-list conversion was particularly problematic for version numbers and coordinates that needed to remain as tuples for direct comparison. With zarrcompatibility v2.0+, however, the conversion to JSON now takes place in the background with full type preservation and does not need to be handled separately in the application.

### The Solution

With `zarrcompatibility`, everything just works with **automatic tuple preservation**:

```python
import zarrcompatibility as zc

# One-time setup with automatic tuple preservation
zc.enable_universal_serialization()

# Now everything works, including tuples!
json.dumps(config)  # Works perfectly!

# Tuples are preserved through JSON round-trips
version = (1, 0)
json_str = json.dumps(version)  # '{"__type__": "tuple", "__data__": [1, 0]}'
restored = json.loads(json_str)  # (1, 0) - still a tuple!
assert version == restored  # SUCCESS! (1, 0) == (1, 0)

# Store in Zarr metadata with tuple preservation
import zarr
z = zarr.zeros((100, 100))
z.attrs['experiment'] = config  # Just works!
z.attrs['version'] = (1, 0)     # Remains a tuple
```

## Key Features

- **Universal Compatibility**: Works with ANY Python object (dataclasses, regular classes, enums, built-ins)
- **Automatic Tuple Preservation**: Tuples remain tuples through JSON serialization (New in v2.0!)
- **Zero Code Changes**: No need to modify your existing classes
- **Zarr Ready**: Designed specifically for Zarr v2 and v3 metadata storage
- **Smart Serialization**: Handles datetime, UUID, Decimal, Enum, complex numbers, and more
- **Flexible Usage**: Global patching or explicit serialization
- **Type Preservation**: Maintains data integrity through serialization
- **Extensible**: Easy to customize for special cases

## Installation

See the latest release: https://github.com/fherb2/zarrcompatibility/releases

```bash
# Latest version (recommended)
pip install https://github.com/fherb2/zarrcompatibility/releases/download/v2.0.1/zarrcompatibility-2.0.1-py3-none-any.whl

# Poetry install
poetry add https://github.com/fherb2/zarrcompatibility/releases/download/v2.0.1/zarrcompatibility-2.0.1-py3-none-any.whl

# Development installation
git clone https://github.com/fherb2/zarrcompatibility.git
cd zarrcompatibility
pip install -e .[dev,test,zarr]
```

## Quick Start

### Method 1: Global Enable (Recommended)

```python
import zarrcompatibility as zc
import json
from datetime import datetime
from dataclasses import dataclass

# Enable universal serialization with automatic tuple preservation
zc.enable_universal_serialization()

# Now json.dumps works with everything!
@dataclass
class SensorData:
    sensor_id: str
    timestamp: datetime
    version: tuple
    readings: list
    metadata: dict

data = SensorData(
    sensor_id="temp_01",
    timestamp=datetime.now(),
    version=(1, 0),  # This will remain a tuple!
    readings=[23.5, 24.1, 23.8],
    metadata={"location": "lab_a", "calibrated": True}
)

# Just works!
json_str = json.dumps(data)
print(json_str)  # Perfect JSON output with tuple preservation

# Round-trip test
restored_data = json.loads(json_str)
print(f"Version type: {type(restored_data['version'])}")  # <class 'tuple'>
```

### Method 2: Explicit Serialization

```python
import zarrcompatibility as zc

# Explicit conversion (no global changes)
serialized = zc.serialize_object(data)
json_str = json.dumps(serialized)
```

### Method 3: Using Mixins

```python
class ExperimentMetadata(zc.ZarrCompatible):
    def __init__(self, name, parameters):
        self.name = name
        self.parameters = parameters
        self.version = (1, 0)  # Tuple preserved automatically
        self.created_at = datetime.now()

metadata = ExperimentMetadata("exp_001", {"epochs": 100})

# Rich API for Zarr integration
zarr_attrs = metadata.to_zarr_attrs()
json_str = metadata.to_json()

# Direct Zarr integration
import zarr
group = zarr.open_group("experiment.zarr", mode="w")
metadata.save_to_zarr_group(group, "metadata")
```

## Supported Types

`zarrcompatibility` automatically handles:

| Type Category | Examples | Serialization |
|---------------|----------|---------------|
| **Basic Types** | `str`, `int`, `float`, `bool`, `None` | Pass-through |
| **Collections** | `list`, `tuple`, `set`, `dict` | Recursive serialization with tuple preservation |
| **Date/Time** | `datetime`, `date`, `time` | ISO format strings |
| **Numbers** | `Decimal`, `complex` | String/dict representation |
| **Identifiers** | `UUID` | String representation |
| **Enums** | `Enum` subclasses | Value extraction |
| **Dataclasses** | `@dataclass` | Field dictionary |
| **Regular Classes** | Any custom class | Attribute dictionary |
| **Binary Data** | `bytes` | Base64 encoding |

## Automatic Tuple Preservation (New in v2.0!)

The breakthrough feature of zarrcompatibility v2.0+ is **automatic tuple preservation** through JSON serialization, solving a major pain point in scientific computing:

```python
import zarrcompatibility as zc
import zarr
import tempfile

# Enable universal serialization with automatic tuple preservation
zc.enable_universal_serialization()

# Problem: Before zarrcompatibility, this was broken
with tempfile.TemporaryDirectory() as tmpdir:
    group = zarr.open_group(f"{tmpdir}/data.zarr", mode="w")
    
    # Store tuples in Zarr metadata
    group.attrs["version"] = (1, 0)           # Stored as tuple, not list!
    group.attrs["coordinates"] = (10.5, 20.3) # Stored as tuple, not list!
    group.attrs["shape"] = (100, 200)         # Stored as tuple, not list!
    group.attrs["tags"] = ["data", "test"]    # Lists remain lists
    
    # Save and reload
    group.store.close()
    reloaded = zarr.open_group(f"{tmpdir}/data.zarr", mode="r")
    
    # Tuples are preserved!
    version = reloaded.attrs["version"]        # (1, 0) - still a tuple!
    coordinates = reloaded.attrs["coordinates"] # (10.5, 20.3) - still a tuple!
    shape = reloaded.attrs["shape"]            # (100, 200) - still a tuple!
    tags = reloaded.attrs["tags"]              # ["data", "test"] - still a list!
    
    # Direct comparisons now work without manual conversion!
    assert version == (1, 0)                  # ✅ Works!
    assert coordinates == (10.5, 20.3)        # ✅ Works!
    assert shape == (100, 200)                # ✅ Works!
    
    print("✅ All tuple types preserved through Zarr storage!")
```

### Before vs After zarrcompatibility v2.0

**Before (manual workarounds required):**
```python
# The old way - manual type conversion everywhere
stored_version = audio_group.attrs["version"]  # [1, 0] (list)
if isinstance(stored_version, list):
    stored_version = tuple(stored_version)      # Manual conversion
if stored_version == Config.original_audio_group_version:
    print("Version matches")
```

**After (automatic preservation):**
```python
# The new way - just works!
stored_version = audio_group.attrs["version"]  # (1, 0) (tuple)
if stored_version == Config.original_audio_group_version:
    print("Version matches")                   # Direct comparison works!
```

## Scientific Computing Examples

### Storing ML Model Metadata with Tuple Preservation

```python
import zarrcompatibility as zc
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import zarr
import numpy as np

zc.enable_universal_serialization()

class ModelStatus(Enum):
    TRAINING = "training"
    CONVERGED = "converged"
    FAILED = "failed"

@dataclass
class ModelMetadata:
    model_name: str
    architecture: str
    version: tuple  # Will be preserved as tuple!
    input_shape: tuple  # Will be preserved as tuple!
    hyperparameters: dict
    training_start: datetime
    status: ModelStatus
    metrics: dict

# Create model metadata
metadata = ModelMetadata(
    model_name="resnet50_experiment",
    architecture="ResNet-50",
    version=(2, 1),  # Tuple preserved
    input_shape=(224, 224, 3),  # Tuple preserved
    hyperparameters={
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100
    },
    training_start=datetime.now(),
    status=ModelStatus.TRAINING,
    metrics={"accuracy": 0.95, "loss": 0.05}
)

# Save model weights and metadata together
weights = np.random.random((1000, 1000))  # Your actual model weights
z = zarr.array(weights, store="model.zarr")
z.attrs['model_metadata'] = metadata  # Just works with tuple preservation!

# Later: load everything back - tuples are preserved!
loaded_array = zarr.open("model.zarr")
loaded_metadata = loaded_array.attrs['model_metadata']

# Tuples are automatically preserved
print(f"Version: {loaded_metadata['version']} (type: {type(loaded_metadata['version'])})")
print(f"Input shape: {loaded_metadata['input_shape']} (type: {type(loaded_metadata['input_shape'])})")
# Output: Version: (2, 1) (type: <class 'tuple'>)
#         Input shape: (224, 224, 3) (type: <class 'tuple'>)
```

### Experiment Tracking with Coordinates

```python
class ExperimentTracker(zc.ZarrCompatible):
    def __init__(self, experiment_name):
        self.experiment_name = experiment_name
        self.start_time = datetime.now()
        self.version = (1, 0)  # Preserved as tuple
        self.coordinates = {}  # Will store tuples
        self.parameters = {}
        self.results = {}
    
    def add_coordinate(self, name, position):
        self.coordinates[name] = position  # Tuples preserved
    
    def add_parameter(self, name, value):
        self.parameters[name] = value
    
    def add_result(self, name, value):
        self.results[name] = value

# Track an experiment with coordinates
tracker = ExperimentTracker("protein_folding_001")
tracker.add_coordinate("start_position", (10.5, 20.3, 15.8))
tracker.add_coordinate("end_position", (12.1, 18.9, 16.2))
tracker.add_parameter("temperature", 298.15)
tracker.add_result("final_energy", -1234.56)

# Save with data
simulation_data = np.random.random((1000, 3))
z = zarr.array(simulation_data, store="simulation.zarr")
tracker.save_to_zarr_group(z, "experiment_info")

# Later: coordinates are still tuples!
reloaded = zarr.open("simulation.zarr")
info = reloaded.attrs["experiment_info"]
start_pos = info["coordinates"]["start_position"]  # Still (10.5, 20.3, 15.8) tuple!
```

## Advanced Usage

### Custom Serialization

```python
class CustomClass:
    def __init__(self, data):
        self.data = data
        self.coordinates = (1.0, 2.0)  # Will be preserved as tuple
        self._secret = "don't serialize this"
    
    def __json__(self):
        """Custom serialization method"""
        return {
            "data": self.data,
            "coordinates": self.coordinates,  # Tuple preserved in custom serialization
            "serialized_at": datetime.now().isoformat(),
            "version": "1.0"
        }

obj = CustomClass({"important": "data"})
serialized = zc.serialize_object(obj)
# Uses custom __json__ method with tuple preservation
```

### Testing Serialization

```python
# Test if your objects serialize properly with tuple preservation
complex_obj = {
    "version": (2, 1, 0),
    "coordinates": [(1.0, 2.0), (3.0, 4.0)],  # List of tuples
    "metadata": {"shape": (100, 200)}
}

result = zc.test_serialization(complex_obj, verbose=True)
print(f"Serialization {'passed' if result else 'failed'}")

# Check JSON compatibility
if zc.is_json_serializable(complex_obj):
    print("Ready for Zarr storage with tuple preservation!")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests including tuple preservation tests
pytest

# Run with coverage
pytest --cov=zarrcompatibility

# Run only Zarr integration tests
pytest -m zarr

# Run tuple preservation tests specifically
pytest tests/test_tuple_preservation.py

# Run with verbose output
pytest -v
```

## API Reference

### Core Functions

- `enable_universal_serialization()` - Enable global JSON patching with tuple preservation
- `disable_universal_serialization()` - Restore original JSON behavior
- `serialize_object(obj)` - Convert any object to JSON-compatible form
- `deserialize_object(data, target_class=None)` - Reconstruct objects from JSON
- `prepare_for_zarr(obj)` - Explicit Zarr preparation

### Mixin Classes

- `JSONSerializable` - Adds serialization methods to any class
- `ZarrCompatible` - Enhanced mixin with Zarr-specific methods

### Utilities

- `@make_serializable` - Decorator to add serialization to existing classes
- `is_json_serializable(obj)` - Test JSON compatibility
- `test_serialization(obj)` - Comprehensive serialization testing with tuple preservation

## Development Setup

```bash
git clone https://github.com/fherb2/zarrcompatibility.git
cd zarrcompatibility
pip install -e .[dev,test,zarr]
pre-commit install
```

### Running Tests

```bash
pytest                           # Run all tests
pytest -m "not slow"            # Skip slow tests  
pytest tests/test_zarr.py        # Run specific test file
pytest tests/test_tuple_preservation.py  # Run tuple preservation tests
```

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built for the scientific Python community
- Inspired by the need for better metadata handling in Zarr
- Special thanks to the Zarr development team for Zarr v3 compatibility
- Thanks to all contributors and testers

## Changelog

### Version 2.0.1 (Current)
- **🚀 Major Feature: Automatic Tuple Preservation**
  - Tuples now remain tuples through JSON serialization round-trips
  - Works seamlessly with Zarr v2 and v3 metadata storage
  - Eliminates manual type conversion workarounds
  - Direct tuple comparisons now work without isinstance() checks
- Fixed tuple preservation in Zarr metadata serialization
- Enhanced compatibility with Zarr v3 JSON encoding
- Comprehensive test suite for tuple preservation scenarios
- Updated documentation with tuple preservation examples

### Version 2.0.0 
- Initial implementation of tuple preservation feature
- Zarr v3 compatibility improvements
- Enhanced JSON encoder with recursive tuple detection

### Version 1.0.3
- Bug fixes and stability improvements
- Enhanced error handling
- Documentation updates

### Version 1.0.0
- Initial release
- Universal JSON serialization
- Zarr compatibility
- Comprehensive test suite
- Full documentation

## Migration from v1.x to v2.x

**Good news: No breaking changes!** zarrcompatibility v2.x is fully backward compatible with v1.x:

```python
# Your existing v1.x code works unchanged
import zarrcompatibility as zc
zc.enable_universal_serialization()

# But now you get automatic tuple preservation for free!
version = (1, 0)
json_str = json.dumps(version)  # Now preserves tuple type
restored = json.loads(json_str)  # (1, 0) - still a tuple!
```

**Recommended migration steps:**
1. Update to v2.0.1+
2. Remove any manual tuple-to-list conversion workarounds
3. Enjoy direct tuple comparisons in your Zarr metadata!

For questions, issues, or contributions, please visit: https://github.com/fherb2/zarrcompatibility
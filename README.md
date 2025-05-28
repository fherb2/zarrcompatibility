# zarrcompatibility

**Universal JSON Serialization for Python Objects with Zarr Compatibility**

## Overview

`zarrcompatibility` is a Python library that makes **any Python object** compatible with JSON serialization and Zarr storage. It solves the common problem of storing complex metadata alongside scientific data in Zarr arrays.

**[Full documentation](https://fherb2.github.io/zarrcompatibility/)**

### The Problem

Zarr stores metadata as JSON, but Python's standard JSON serializer can't handle many common objects:

```python
import json
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ExperimentConfig:
    name: str
    timestamp: datetime
    params: dict

config = ExperimentConfig("exp_001", datetime.now(), {"lr": 0.001})

# This fails!
json.dumps(config)  # TypeError: Object of type ExperimentConfig is not JSON serializable
```

I first encountered this problem when I wanted to save the meta information from the original audio files in Zarr as attributes in addition to the audio PCM data arrays for my project [ZarrWildlifeRecording Library for Python](https://github.com/fherb2/zarr_wildlife_recording_py). Zarr saves attributes in files in JSON coding. Different structures and enums required individual special solutions in the application. With zarrcompatibility, however, the conversion to JSON now takes place in the background and does not need to be handled separately in the application.

### The Solution

With `zarrcompatibility`, everything just works:

```python
import zarrcompatibility as zc

# One-time setup
zc.enable_universal_serialization()

# Now everything works!
json.dumps(config)  # Works perfectly!

# Store in Zarr metadata
import zarr
z = zarr.zeros((100, 100))
z.attrs['experiment'] = config  # Just works!
```

## Key Features

- **Universal Compatibility**: Works with ANY Python object (dataclasses, regular classes, enums, built-ins)
- **Zero Code Changes**: No need to modify your existing classes
- **Zarr Ready**: Designed specifically for Zarr metadata storage
- **Smart Serialization**: Handles datetime, UUID, Decimal, Enum, complex numbers, and more
- **Flexible Usage**: Global patching or explicit serialization
- **Type Preservation**: Maintains data integrity through serialization
- **Extensible**: Easy to customize for special cases

## Installation

See for the last release: https://github.com/fherb2/zarrcompatibility/releases

and write by changing the release: 

```bash
# Basic installation
pip install https://github.com/fherb2/zarrcompatibility/releases/download/v1.0.3/zarrcompatibility-1.0.3-py3-none-any.whl

# Poetry install
poetry add https://github.com/fherb2/zarrcompatibility/releases/download/v1.0.3/zarrcompatibility-1.0.3-py3-none-any.whl

```

## Quick Start

### Method 1: Global Enable (Recommended)

```python
import zarrcompatibility as zc
import json
from datetime import datetime
from dataclasses import dataclass

# Enable universal serialization once
zc.enable_universal_serialization()

# Now json.dumps works with everything!
@dataclass
class SensorData:
    sensor_id: str
    timestamp: datetime
    readings: list
    metadata: dict

data = SensorData(
    sensor_id="temp_01",
    timestamp=datetime.now(),
    readings=[23.5, 24.1, 23.8],
    metadata={"location": "lab_a", "calibrated": True}
)

# Just works!
json_str = json.dumps(data)
print(json_str)  # Perfect JSON output
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
| **Collections** | `list`, `tuple`, `set`, `dict` | Recursive serialization |
| **Date/Time** | `datetime`, `date`, `time` | ISO format strings |
| **Numbers** | `Decimal`, `complex` | String/dict representation |
| **Identifiers** | `UUID` | String representation |
| **Enums** | `Enum` subclasses | Value extraction |
| **Dataclasses** | `@dataclass` | Field dictionary |
| **Regular Classes** | Any custom class | Attribute dictionary |
| **Binary Data** | `bytes` | Base64 encoding |

## Scientific Computing Examples

### Storing ML Model Metadata

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
    hyperparameters: dict
    training_start: datetime
    status: ModelStatus
    metrics: dict

# Create model metadata
metadata = ModelMetadata(
    model_name="resnet50_experiment",
    architecture="ResNet-50",
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
z.attrs['model_metadata'] = metadata  # Just works!

# Later: load everything back
loaded_array = zarr.open("model.zarr")
loaded_metadata = loaded_array.attrs['model_metadata']

# Note: The loaded metadata might be stored as the original object or as a dict
# Handle both cases:
if hasattr(loaded_metadata, 'model_name'):
    # Stored as object
    print(f"Model: {loaded_metadata.model_name}")
    print(f"Status: {loaded_metadata.status}")
else:
    # Stored as dict
    print(f"Model: {loaded_metadata['model_name']}")
    print(f"Status: {loaded_metadata['status']}")
```

### Experiment Tracking

```python
class ExperimentTracker(zc.ZarrCompatible):
    def __init__(self, experiment_name):
        self.experiment_name = experiment_name
        self.start_time = datetime.now()
        self.parameters = {}
        self.results = {}
        self.notes = []
    
    def add_parameter(self, name, value):
        self.parameters[name] = value
    
    def add_result(self, name, value):
        self.results[name] = value
    
    def add_note(self, note):
        self.notes.append({
            "timestamp": datetime.now(),
            "note": note
        })

# Track an experiment
tracker = ExperimentTracker("protein_folding_001")
tracker.add_parameter("temperature", 298.15)
tracker.add_parameter("ph", 7.4)
tracker.add_result("final_energy", -1234.56)
tracker.add_note("Simulation completed successfully")

# Save with data
simulation_data = np.random.random((1000, 3))  # Your simulation results
z = zarr.array(simulation_data, store="simulation.zarr")
tracker.save_to_zarr_group(z, "experiment_info")
```

## Advanced Usage

### Custom Serialization

```python
class CustomClass:
    def __init__(self, data):
        self.data = data
        self._secret = "don't serialize this"
    
    def __json__(self):
        """Custom serialization method"""
        return {
            "data": self.data,
            "serialized_at": datetime.now().isoformat(),
            "version": "1.0"
        }

obj = CustomClass({"important": "data"})
serialized = zc.serialize_object(obj)
# Uses custom __json__ method
```

### Decorator Approach

```python
@zc.make_serializable
class DataProcessor:
    def __init__(self, algorithm, parameters):
        self.algorithm = algorithm
        self.parameters = parameters
        self.processed_count = 0

processor = DataProcessor("gaussian_blur", {"sigma": 1.5})
json_str = processor.to_json()  # Added by decorator
```

### Testing Serialization

```python
# Test if your objects serialize properly
result = zc.test_serialization(your_complex_object, verbose=True)
print(f"Serialization {'passed' if result else 'failed'}")

# Check JSON compatibility
if zc.is_json_serializable(your_object):
    print("Ready for Zarr storage!")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=zarrcompatibility

# Run only Zarr integration tests
pytest -m zarr

# Run with verbose output
pytest -v
```

## API Reference

### Core Functions

- `enable_universal_serialization()` - Enable global JSON patching
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
- `test_serialization(obj)` - Comprehensive serialization testing

### Development Setup

```bash
git clone https://github.com/yourusername/zarrcompatibility.git
cd zarrcompatibility
pip install -e .[dev,test,zarr]
pre-commit install
```

### Running Tests

```bash
pytest                    # Run all tests
pytest -m "not slow"     # Skip slow tests
pytest tests/test_zarr.py # Run specific test file
```

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built for the scientific Python community
- Inspired by the need for better metadata handling in Zarr
- Thanks to all contributors and testers

## Changelog

### Version 1.0.0
- Initial release
- Universal JSON serialization
- Zarr compatibility
- Comprehensive test suite
- Full documentation


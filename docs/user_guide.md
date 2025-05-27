# Universal Zarr Serialization User Guide

## Overview

The `zarrcompatibility` library provides universal JSON serialization capabilities that make any Python object compatible with Zarr storage. This solves the common problem of storing complex metadata alongside scientific data, as Zarr stores metadata as JSON but Python's standard JSON serializer cannot handle many common object types.

## Key Features

- **Universal Compatibility**: Serializes ANY Python object type (dataclasses, regular classes, enums, built-ins)
- **Zero Code Changes**: No modifications needed to existing classes
- **Zarr Ready**: Specifically designed for Zarr metadata storage
- **Smart Serialization**: Handles datetime, UUID, Decimal, Enum, complex numbers, and more
- **Flexible Usage**: Global patching or explicit serialization modes
- **Type Preservation**: Maintains data integrity through serialization
- **Extensible**: Easy to customize for special cases

## Installation

**Important**: Before installation, check the latest release number at: https://github.com/fherb2/zarrcompatibility/releases

Replace the version number in the commands below with the current release version:

```bash
# Basic installation
pip install https://github.com/fherb2/zarrcompatibility/releases/download/v1.0.3/zarrcompatibility-1.0.3-py3-none-any.whl

# Poetry installation
poetry add https://github.com/fherb2/zarrcompatibility/releases/download/v1.0.3/zarrcompatibility-1.0.3-py3-none-any.whl
```

For the latest release, update the URL format by changing the version numbers:
```bash
# Example with version v1.0.4 (replace with actual latest version)
pip install https://github.com/fherb2/zarrcompatibility/releases/download/v1.0.4/zarrcompatibility-1.0.4-py3-none-any.whl
```

### Development Installation

For development or if you want to contribute:

```bash
# Clone the repository first
git clone https://github.com/fherb2/zarrcompatibility.git
cd zarrcompatibility

# Development installation with all extras
pip install -e .[dev,test,zarr]
```

## Quick Start

The simplest way to get started is by enabling universal serialization globally:

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

## Usage Patterns

### 1. Global Serialization (Recommended)

Enable universal serialization once at the start of your application:

```python
import zarrcompatibility as zc

# One-time setup
zc.enable_universal_serialization()

# Now all JSON operations work with any Python object
import json
from datetime import datetime

config = {
    "experiment_name": "test_001",
    "timestamp": datetime.now(),
    "parameters": {"lr": 0.001, "epochs": 100}
}

json_str = json.dumps(config)  # Works perfectly!
```

### 2. Explicit Serialization

For more control, use explicit conversion without modifying global behavior:

```python
import zarrcompatibility as zc

# Explicit conversion (no global changes)
serialized = zc.serialize_object(data)
json_str = json.dumps(serialized)

# Or one-step conversion
json_str = zc.to_json(data)
```

### 3. Custom Serializable Classes

Create classes with enhanced Zarr integration:

```python
from zarrcompatibility import ZarrCompatible
from datetime import datetime

class ExperimentMetadata(ZarrCompatible):
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

## Supported Data Types

The library automatically handles a wide range of Python types:

| Type Category | Examples | Serialization Method |
|---------------|----------|---------------------|
| Basic Types | `str`, `int`, `float`, `bool`, `None` | Pass-through |
| Collections | `list`, `tuple`, `set`, `dict` | Recursive serialization |
| Date/Time | `datetime`, `date`, `time` | ISO format strings |
| Numbers | `Decimal`, `complex` | String/dict representation |
| Identifiers | `UUID` | String representation |
| Enums | `Enum` subclasses | Value extraction |
| Dataclasses | `@dataclass` | Field dictionary |
| Regular Classes | Any custom class | Attribute dictionary |
| Binary Data | `bytes` | Base64 encoding |

## Real-World Examples

### Machine Learning Model Metadata

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

# Handle both object and dict representations
if hasattr(loaded_metadata, 'model_name'):
    # Stored as object
    print(f"Model: {loaded_metadata.model_name}")
    print(f"Status: {loaded_metadata.status}")
else:
    # Stored as dict
    print(f"Model: {loaded_metadata['model_name']}")
    print(f"Status: {loaded_metadata['status']}")
```

### Scientific Experiment Tracking

```python
from zarrcompatibility import ZarrCompatible
from datetime import datetime
import numpy as np
import zarr

class ExperimentTracker(ZarrCompatible):
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

## Advanced Features

### Custom Serialization Methods

Define custom serialization for specific classes:

```python
from datetime import datetime
import zarrcompatibility as zc

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

### Decorator-Based Enhancement

Add serialization to existing classes:

```python
import zarrcompatibility as zc

@zc.make_serializable
class DataProcessor:
    def __init__(self, algorithm, parameters):
        self.algorithm = algorithm
        self.parameters = parameters
        self.processed_count = 0

processor = DataProcessor("gaussian_blur", {"sigma": 1.5})
json_str = processor.to_json()  # Added by decorator
```

## Testing and Validation

### Verify Serialization Compatibility

Test if your objects serialize properly:

```python
import zarrcompatibility as zc

# Test if your objects serialize properly
result = zc.test_serialization(your_complex_object, verbose=True)
print(f"Serialization {'passed' if result else 'failed'}")

# Check JSON compatibility
if zc.is_json_serializable(your_object):
    print("Ready for Zarr storage!")
```

### Running Tests

For development and testing:

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

### Mixins and Decorators

- `JSONSerializable` - Adds serialization methods to any class
- `ZarrCompatible` - Enhanced mixin with Zarr-specific methods
- `@make_serializable` - Decorator to add serialization to existing classes

### Utility Functions

- `is_json_serializable(obj)` - Test JSON compatibility
- `test_serialization(obj)` - Comprehensive serialization testing
- `to_json(obj)` - Direct object to JSON string conversion

## Error Handling and Troubleshooting

### Common Issues

1. **Circular References**: The library detects and handles circular references automatically
2. **Large Objects**: Very large objects may impact performance; consider chunking data
3. **Custom Types**: For unusual types, implement `__json__()` method for custom serialization

### Best Practices

1. **Enable Once**: Call `enable_universal_serialization()` once at application startup
2. **Test Thoroughly**: Use `test_serialization()` to verify complex objects work correctly
3. **Document Custom Methods**: When implementing `__json__()`, document the serialization format
4. **Handle Loading**: Remember that loaded objects may be dicts rather than original types

## Conclusion

The `zarrcompatibility` library makes it effortless to store complex Python objects as metadata in Zarr arrays. By providing universal JSON serialization, it eliminates the common pain points of scientific data storage and enables seamless integration between your Python objects and Zarr's efficient array storage format.

Whether you're tracking machine learning experiments, storing scientific metadata, or building data pipelines, this library ensures that your Python objects work seamlessly with Zarr's JSON-based metadata system.
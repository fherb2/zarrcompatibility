# ZarrCompatibility

Universal JSON Serialization for Python Objects with Zarr Compatibility.

## Quick Start

```python
import zarrcompatibility as zc

# Enable universal serialization
zc.enable_universal_serialization()

# Now everything works with JSON!
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Config:
    name: str
    timestamp: datetime

config = Config("test", datetime.now())
json.dumps(config)  # Just works!

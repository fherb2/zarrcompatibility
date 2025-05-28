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
```


### Motivation

I first encountered this problem when I wanted to save the meta information from the original audio files in Zarr as attributes in addition to the audio PCM data arrays for my project [ZarrWildlifeRecording Library for Python](https://github.com/fherb2/zarr_wildlife_recording_py). Zarr saves attributes in files in JSON coding. Different structures and enums required individual special solutions in the application. With zarrcompatibility, however, the conversion to JSON now takes place in the background and does not need to be handled separately in the application.

_Frank_

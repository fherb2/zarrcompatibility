 # Initial und Tests

- welche Imports im Quellcode können weg?
- Imports vorzugsweise am Filebeginn.

- versuchsweise mal mit Zarr 2 testen.
- die ersten Zarr-Versionen schrittweise mit dem CI per Hand getriggert testen.

# Testumfang

- alle vorhandenen Tests

Sieht so aus, dass dem schon so ist:

```
def run_compatibility_test():
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/", "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    return {
        "success": result.returncode == 0,
        "output": result.stdout,
        "errors": result.stderr
    }
```



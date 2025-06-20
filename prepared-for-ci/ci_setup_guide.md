# GitHub CI Setup Guide für Zarr Compatibility Checker

## 🎯 Überblick

Diese GitHub Actions Workflow implementiert ein vollautomatisches System für Zarr-Versionskompatibilitätstests. Es läuft monatlich und:

1. **Erkennt neue Zarr-Versionen** von PyPI
2. **Testet Kompatibilität** auf Python 3.8-3.12
3. **Aktualisiert automatisch** `supported_zarr_versions.json`
4. **Erstellt Pull Requests** mit Updates
5. **Generiert Releases** bei Erfolg

## 📁 Datei-Setup

### 1. Workflow-Datei erstellen
```bash
mkdir -p .github/workflows
# Kopiere zarr-compatibility.yml in .github/workflows/
```

### 2. Repository-Berechtigungen konfigurieren

#### GitHub Token Permissions
In den Repository Settings → Actions → General:

- **Workflow permissions**: "Read and write permissions" ✅
- **Allow GitHub Actions to create and approve pull requests** ✅

#### Secrets (optional, für erweiterte Features)
- `GITHUB_TOKEN` ist automatisch verfügbar
- Für Slack/Discord Notifications: `SLACK_WEBHOOK` oder `DISCORD_WEBHOOK`

## ⚙️ Workflow-Konfiguration

### Trigger-Optionen

#### 1. Automatisch (Monatlich)
```yaml
schedule:
  - cron: '0 2 1 * *'  # 1. des Monats, 02:00 UTC
```

#### 2. Manuell
```yaml
workflow_dispatch:
  inputs:
    force_update:
      description: 'Force update even if no new versions'
      type: boolean
    test_version:
      description: 'Test specific Zarr version'
      type: string
```

### Anpassbare Parameter

```yaml
env:
  PYTHON_VERSION: "3.9"           # Basis Python-Version
  MIN_PYTHON: "3.8"               # Minimum unterstützte Python-Version
  MAX_PYTHON: "3.12"              # Maximum getestete Python-Version
```

## 🧪 Test-Matrix

Der Workflow testet jede neue Zarr-Version gegen:

| Python Version | Test Scope |
|----------------|------------|
| 3.8 | Minimum compatibility |
| 3.9 | Core functionality |
| 3.10 | Standard testing |
| 3.11 | Modern features |
| 3.12 | Latest Python |

### Test-Kategorien

1. **Basic Import & Enable**
   - Import von zarrcompatibility
   - Aktivierung der Zarr-Serialisierung

2. **Tuple Preservation**
   - Einfache Tuples in Zarr-Metadaten
   - Verschachtelte Tuple-Strukturen

3. **Complex Types**
   - datetime, Enum, UUID
   - Complex numbers, Decimal
   - Dataclasses

4. **JSON Isolation**
   - Globaler json-Modul unverändert
   - Keine Seiteneffekte

5. **Real-world Scenarios**
   - File-basierte Zarr-Gruppen
   - Verschachtelte Metadaten-Strukturen

## 📊 Automatische Updates

### supported_zarr_versions.json
```json
{
  "min_version": "3.0.0",
  "max_tested": "3.0.8",
  "known_working": ["3.0.0", "3.0.1", ...],
  "recommended": "3.0.8",
  "last_update": "2025-01-19",
  "update_source": "ci",
  "testing_info": {
    "test_date": "2025-01-19",
    "ci_run": true,
    "test_coverage": [...]
  }
}
```

### README.md Updates
Automatische Aktualisierung der Kompatibilitäts-Matrix:

```markdown
| zarrcompatibility | Zarr Versions | Python | Status |
|------------------|---------------|---------|--------|
| v3.0.0 | 3.0.0 - 3.0.8 | 3.8+ | ✅ Supported |
```

## 🔄 Workflow-Ablauf im Detail

### Phase 1: Version Detection
```python
# Holt alle Zarr v3.x Releases von PyPI
# Vergleicht mit aktueller supported_zarr_versions.json
# Identifiziert neue Versionen zum Testen
```

### Phase 2: Compatibility Testing
```python
# Matrix-Test: Neue Zarr-Versionen × Python-Versionen
# Umfassende Funktionalitätstests
# Resultat-Sammlung als JSON-Artefakte
```

### Phase 3: Configuration Update
```python
# Aggregiert Testergebnisse
# Aktualisiert supported_zarr_versions.json
# Modifiziert README.md Kompatibilitäts-Matrix
```

### Phase 4: Pull Request Creation
```python
# Erstellt automatisch PR mit Updates
# Detaillierte Beschreibung der Änderungen
# Links zu Test-Logs
```

### Phase 5: Release Generation (Optional)
```python
# Erstellt Draft-Release bei größeren Updates
# Automatische Release-Notes
# Versionierung basierend auf Zarr-Updates
```

## 🛠️ Lokale Entwicklung & Testing

### Workflow lokal testen
```bash
# Mit act (GitHub Actions local runner)
gh extension install https://github.com/nektos/act
act workflow_dispatch

# Oder spezifische Jobs
act -j detect-zarr-versions
act -j test-zarr-versions
```

### Manueller Test-Lauf
```bash
# Workflow manuell triggern
gh workflow run zarr-compatibility.yml \
  --field force_update=true \
  --field test_version=3.0.9
```

## 📈 Monitoring & Maintenance

### Workflow-Status überwachen
- GitHub Actions Tab für Erfolg/Fehler
- Email-Benachrichtigungen bei Fehlschlägen
- Step Summary mit detaillierten Resultaten

### Typische Wartungsaufgaben

#### 1. Python-Versionen aktualisieren
```yaml
strategy:
  matrix:
    python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]  # Neue Version hinzufügen
```

#### 2. Test-Abdeckung erweitern
```python
# In der test-zarr-versions Step neue Tests hinzufügen
def run_extended_compatibility_test():
    # Zusätzliche Szenarien testen
    pass
```

#### 3. Benachrichtigungen hinzufügen
```yaml
- name: Slack Notification
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🚨 Troubleshooting

### Häufige Probleme

#### 1. Permissions Error
```bash
Error: Resource not accessible by integration
```
**Lösung**: Repository Settings → Actions → General → Workflow permissions → "Read and write"

#### 2. Test Failures
```bash
❌ Zarr X.Y.Z failed tests
```
**Lösung**: 
- Check Workflow-Logs für Details
- Möglicherweise Breaking Changes in Zarr
- Anpassung der Tests erforderlich

#### 3. PR Creation Failed
```bash
Error: Pull request already exists
```
**Lösung**:
- Alter PR schließen/mergen
- Branch-Name in Workflow anpassen

### Debug-Modi

#### Verbose Logging aktivieren
```yaml
env:
  ACTIONS_RUNNER_DEBUG: true
  ACTIONS_STEP_DEBUG: true
```

#### Test-Matrix reduzieren (für Debugging)
```yaml
strategy:
  matrix:
    zarr-version: ["3.0.8"]  # Nur eine Version
    python-version: ["3.9"]  # Nur eine Python-Version
```

## 🎯 Best Practices

### 1. **Regelmäßige Reviews**
- Monatliche PR-Reviews der Auto-Updates
- Verifizierung der Test-Resultate vor Merge

### 2. **Release-Strategie**
- Auto-Releases als Draft erstellen
- Manuelle Review vor Veröffentlichung
- Semantic Versioning einhalten

### 3. **Test-Qualität**
- Umfassende Real-World Szenarien
- Edge-Cases abdecken
- Performance-Regression Tests

### 4. **Dokumentation**
- CHANGELOG.md automatisch updaten
- Migration-Guides bei Breaking Changes
- Kompatibilitäts-Hinweise aktuell halten

## 🚀 Erweiterte Features (Optional)

### 1. Performance Benchmarking
```python
# Benchmark-Tests zu Workflow hinzufügen
import time
start = time.time()
# ... zarrcompatibility tests ...
duration = time.time() - start
print(f"Performance: {duration:.2f}s")
```

### 2. Multi-OS Testing
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, windows-latest, macos-latest]
    zarr-version: ${{ fromJson(needs.detect-zarr-versions.outputs.new-versions) }}
```

### 3. Dependency Conflict Detection
```python
# Test mit verschiedenen numpy/pandas Versionen
pip install numpy==1.21.0 pandas==1.3.0
pip install numpy==1.24.0 pandas==2.0.0
```

### 4. Security Scanning
```yaml
- name: Security Scan
  uses: pypa/gh-action-pip-audit@v1.0.8
  with:
    inputs: requirements.txt
```

### 5. Documentation Auto-Generation
```python
# Auto-generiere Kompatibilitäts-Docs
def generate_compatibility_docs():
    """Generate comprehensive compatibility documentation."""
    versions = load_supported_versions()
    
    docs = f"""
# Zarr Compatibility Report
Generated: {datetime.now()}

## Supported Versions
{generate_version_table(versions)}

## Test Coverage
{generate_test_coverage(versions)}

## Known Issues
{generate_known_issues(versions)}
"""
    
    with open("docs/compatibility.md", "w") as f:
        f.write(docs)
```

### 6. Integration mit Package Registries
```yaml
- name: Update PyPI Classifiers
  run: |
    # Update pyproject.toml mit neuen Zarr-Versionen
    python update_classifiers.py ${{ steps.update-compatibility.outputs.updated-max-version }}
```

## 🏗️ Erweiterte Workflow-Konfiguration

### Custom Test Scenarios
```python
# Erweiterte Test-Szenarien hinzufügen
EXTENDED_TEST_SCENARIOS = [
    {
        "name": "large_arrays",
        "description": "Test with large Zarr arrays",
        "test": test_large_array_metadata
    },
    {
        "name": "concurrent_access", 
        "description": "Test concurrent metadata access",
        "test": test_concurrent_metadata
    },
    {
        "name": "memory_pressure",
        "description": "Test under memory pressure",
        "test": test_memory_pressure
    }
]
```

### Conditional Logic für Breaking Changes
```yaml
- name: Detect Breaking Changes
  run: |
    python << 'EOF'
    import zarr
    from packaging import version
    
    zarr_ver = version.parse(zarr.__version__)
    
    # Check for known breaking changes
    if zarr_ver >= version.parse("4.0.0"):
        print("BREAKING_CHANGE=true")
        print("Major version change detected - extra caution needed")
    elif zarr_ver >= version.parse("3.1.0"):
        print("MINOR_CHANGE=true") 
        print("Minor version change - review API changes")
    else:
        print("PATCH_CHANGE=true")
        print("Patch version - likely safe")
    EOF
```

### Smart Test Selection
```python
# Intelligente Test-Auswahl basierend auf Zarr-Änderungen
def select_tests_for_zarr_version(zarr_version):
    """Select appropriate tests based on Zarr version changes."""
    
    base_tests = ["import", "enable", "tuple_preservation"]
    
    if version.parse(zarr_version) >= version.parse("3.1.0"):
        # Test neue Features
        base_tests.extend(["new_metadata_features", "v3_1_compatibility"])
    
    if version.parse(zarr_version) >= version.parse("3.0.5"):
        # Test Performance-Verbesserungen
        base_tests.append("performance_regression")
    
    return base_tests
```

## 📊 Monitoring & Alerting

### Slack Integration
```yaml
- name: Notify Team
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    channel: '#zarrcompatibility-alerts'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    text: |
      🚨 Zarr Compatibility Check Failed
      
      **Version**: ${{ matrix.zarr-version }}
      **Python**: ${{ matrix.python-version }}
      **Logs**: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
```

### Email Notifications
```yaml
- name: Email on Major Failure
  if: failure() && contains(matrix.zarr-version, '4.0')
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: "URGENT: Zarr 4.0 Compatibility Failure"
    to: maintainer@example.com
    from: ci@example.com
    body: |
      Critical compatibility failure detected with Zarr 4.0.
      
      This may indicate breaking changes that require immediate attention.
```

### Dashboard Integration
```python
# Sende Metriken an Monitoring-Dashboard
import requests

def send_metrics_to_dashboard(test_results):
    """Send test results to monitoring dashboard."""
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "zarr_versions_tested": len(test_results),
        "success_rate": calculate_success_rate(test_results),
        "python_coverage": ["3.8", "3.9", "3.10", "3.11", "3.12"],
        "test_duration": calculate_test_duration(test_results)
    }
    
    # Send to Grafana/DataDog/etc.
    requests.post(
        "https://api.datadoghq.com/api/v1/series",
        headers={"DD-API-KEY": os.environ["DATADOG_API_KEY"]},
        json={"series": [{"metric": "zarrcompatibility.test_results", "points": [[time.time(), metrics]]}]}
    )
```

## 🔒 Security Best Practices

### Secure Secrets Management
```yaml
env:
  # Nie Geheimnisse in Logs ausgeben
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
  
steps:
- name: Mask Sensitive Data
  run: |
    echo "::add-mask::${{ secrets.SLACK_WEBHOOK }}"
    echo "Webhook configured"
```

### Dependency Pinning
```yaml
- name: Install Trusted Dependencies
  run: |
    # Pin dependency versions für Sicherheit
    pip install \
      requests==2.31.0 \
      packaging==23.2 \
      --only-binary=all \
      --no-deps
```

### Input Validation
```python
def validate_zarr_version(version_string):
    """Validate Zarr version string to prevent injection."""
    import re
    
    # Only allow semantic version format
    pattern = r'^3\.\d+\.\d+(?:rc\d+)?
    if not re.match(pattern, version_string):
        raise ValueError(f"Invalid Zarr version format: {version_string}")
    
    return version_string
```

## 🎯 Customization Guide

### Anpassung für eigene Projekte

#### 1. Package-Namen ändern
```yaml
# In der gesamten Workflow-Datei ersetzen:
zarrcompatibility -> your_package_name
src/zarrcompatibility -> src/your_package
```

#### 2. Test-Framework anpassen
```python
# Für pytest statt unittest:
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

#### 3. Multiple Dependencies testen
```yaml
strategy:
  matrix:
    zarr-version: ${{ fromJson(needs.detect-zarr-versions.outputs.new-versions) }}
    numpy-version: ["1.21.0", "1.24.0", "latest"]
    pandas-version: ["1.5.0", "2.0.0", "latest"]
```

#### 4. Custom Release Strategy
```python
def determine_release_type(old_config, new_config):
    """Determine if this should be major/minor/patch release."""
    
    old_max = version.parse(old_config["max_tested"])
    new_max = version.parse(new_config["max_tested"])
    
    if new_max.major > old_max.major:
        return "major"
    elif new_max.minor > old_max.minor:
        return "minor" 
    else:
        return "patch"
```

## 💡 Pro Tips

### 1. **Incremental Testing**
```python
# Teste nur neue Versionen, nicht alle jedes Mal
def get_versions_to_test(current_config, all_versions):
    """Smart version selection for testing."""
    
    tested_versions = set(current_config.get("known_working", []))
    new_versions = [v for v in all_versions if v not in tested_versions]
    
    # Always re-test the last 2 versions for regression
    recent_versions = sorted(tested_versions, key=version.parse)[-2:]
    
    return list(set(new_versions + recent_versions))
```

### 2. **Failure Recovery**
```yaml
- name: Retry on Failure
  uses: nick-invision/retry@v2
  with:
    timeout_minutes: 10
    max_attempts: 3
    retry_on: error
    command: python run_compatibility_tests.py
```

### 3. **Resource Optimization**
```yaml
# Parallelize wo möglich, aber respektiere GitHub Limits
strategy:
  matrix:
    include:
      - zarr-version: "3.0.8"
        python-version: "3.9"
        test-suite: "full"
      - zarr-version: "3.0.8" 
        python-version: "3.8"
        test-suite: "minimal"
  max-parallel: 5  # GitHub Free hat 20 concurrent jobs limit
```

### 4. **Cache Optimization**
```yaml
- name: Cache Dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ matrix.zarr-version }}
    restore-keys: |
      ${{ runner.os }}-pip-${{ matrix.python-version }}-
      ${{ runner.os }}-pip-
```

## 🎉 Fazit

Dieses CI-System bietet:

✅ **Vollautomatische Zarr-Kompatibilitätsprüfung**  
✅ **Multi-Python-Version Testing**  
✅ **Automatische Dokumentation-Updates**  
✅ **Smart Release Management**  
✅ **Umfassende Benachrichtigungen**  
✅ **Security Best Practices**  
✅ **Einfache Anpassbarkeit**

Das Resultat ist ein **professionelles, wartungsarmes System**, das zarrcompatibility immer auf dem neuesten Stand mit Zarr-Releases hält und Benutzern Vertrauen in die Kompatibilität gibt.

### Next Steps nach Setup:

1. **Workflow deployen** und ersten manuellen Lauf starten
2. **Benachrichtigungen konfigurieren** (Slack/Email)
3. **Erste Auto-PR reviewen** und mergen
4. **Monitoring einrichten** für langfristige Überwachung
5. **Team schulen** im Umgang mit Auto-Updates

**Das System zahlt sich aus** durch reduzierten manuellen Aufwand und erhöhte Benutzer-Zufriedenheit! 🚀
# Technische Schulden - Priorisierte Liste

## 🔴 Kritisch (Sofort angehen)

### 1. i18n-Funktionalität implementieren ✅ ERLEDIGT
**Datei:** `src/socdata/api.py:62-177`  
**Status:** ✅ Vollständig implementiert  
**Details:**
- Parquet-Metadaten werden gelesen
- Variable/Value Labels werden übersetzt
- Labels werden auf DataFrame angewendet
- Fallback-Mechanismen vorhanden

### 2. Logging-Infrastruktur einrichten ✅ ERLEDIGT
**Datei:** `src/socdata/core/logging.py`  
**Status:** ✅ Vollständig implementiert  
**Details:**
- `logging`-Modul integriert
- Logger pro Modul
- Log-Level konfigurierbar (Config)
- Strukturierte Logs

### 3. Testabdeckung für Core-Module ⚠️ IN ARBEIT
**Datei:** `tests/`  
**Status:** ⚠️ Teilweise implementiert
- ✅ `test_api.py` - 11 Tests (vollständig)
- ✅ `test_registry.py` - 16 Tests (vollständig)
- ❌ Keine Tests für `cli.py`
- ❌ Keine Tests für `server.py`
- ❌ Keine Tests für `parsers.py`, `download.py`, `cloud_storage.py`
**Impact:** Regressionsrisiko bei Änderungen  
**Aufwand:** Hoch  
**Lösung:**
- Unit-Tests für alle Core-Funktionen
- Integration-Tests für CLI
- API-Tests für Server-Endpunkte
- Mock-Tests für Adapter

## 🟡 Wichtig (Nächste Iteration)

### 4. Config-System vervollständigen ✅ ERLEDIGT
**Datei:** `src/socdata/core/config.py:56-88`  
**Status:** ✅ Vollständig implementiert  
**Details:**
- YAML/JSON-Parsing implementiert
- Config-Datei validiert
- Environment-Variable-Override funktioniert

### 5. Fehlerbehandlung spezifischer gestalten
**Datei:** Projektweit (41 Stellen mit `except Exception:`)  
**Problem:** Zu generische Exception-Handler  
**Impact:** Fehler werden verschluckt, Debugging erschwert  
**Aufwand:** Mittel  
**Lösung:**
- Spezifische Exceptions definieren
- Nur erwartete Fehler abfangen
- Wichtige Fehler weiterwerfen
- Logging für alle Fehler

### 6. Eurostat Dynamic Discovery
**Datei:** `src/socdata/sources/eurostat.py:31-37`  
**Problem:** Nur kuratierte Liste, keine API-Integration  
**Impact:** Neue Datasets werden nicht automatisch erkannt  
**Aufwand:** Mittel  
**Lösung:**
- Eurostat API für Dataset-Liste nutzen
- Caching der API-Ergebnisse
- Fallback auf kuratierte Liste

## 🟢 Verbesserungen (Nice-to-have)

### 7. Code-Duplikation reduzieren
**Datei:** Adapter (gss.py, soep.py, ess.py, etc.)  
**Problem:** Ähnliche `except Exception: pass`-Blöcke  
**Impact:** Wartbarkeit  
**Aufwand:** Niedrig  
**Lösung:**
- Gemeinsame Fehlerbehandlung in BaseAdapter
- Utility-Funktionen für häufige Patterns

### 8. Typisierung vervollständigen
**Datei:** Projektweit  
**Problem:** Einige Funktionen haben unvollständige Type Hints  
**Impact:** IDE-Unterstützung, Type-Checking  
**Aufwand:** Niedrig  
**Lösung:**
- Alle Funktionen typisieren
- mypy-Checks in CI/CD

### 9. Dokumentation erweitern
**Datei:** `docs/`  
**Problem:** Fehlende Beispiele, Troubleshooting  
**Impact:** Nutzerfreundlichkeit  
**Aufwand:** Mittel  
**Lösung:**
- Beispiele für alle Adapter
- Troubleshooting-Guide
- API-Referenz vervollständigen

### 10. Performance-Optimierungen
**Datei:** Projektweit  
**Problem:** Lazy Loading teilweise vorhanden, könnte optimiert werden  
**Impact:** Performance bei großen Datasets  
**Aufwand:** Hoch  
**Lösung:**
- Caching-Strategien optimieren
- Parquet-Optimierungen (Compression, Partitioning)
- Lazy Loading konsistent implementieren

## Code-Qualität Details

### Exception-Handler (41 Stellen)

**Kritische Stellen:**
- `src/socdata/core/registry.py:76-78` - Index-Fehler stillschweigend ignoriert
- `src/socdata/core/search_index.py:404-405` - Manifest-Lesefehler ignoriert
- `src/socdata/sources/manual.py:124-126` - Parquet-Metadaten-Fehler ignoriert

**Empfehlung:** Diese sollten mindestens geloggt werden.

### NotImplementedError (9 Stellen)

**Erwartet (Adapter-Interface):**
- `src/socdata/sources/base.py` - BaseAdapter Interface
- `src/socdata/sources/eurostat.py:79` - ingest() nicht unterstützt (erwartet)

**Unvollständig:**
- `src/socdata/core/cloud_storage.py:17-29` - CloudStorageBackend abstrakt (aber S3 implementiert)

### Fehlende Validierung

**Beispiele:**
- `src/socdata/api.py:28` - Keine dataset_id-Format-Validierung
- `src/socdata/cli.py:122` - Filter-Parsing ohne klare Fehlermeldung
- `src/socdata/server.py:100-148` - Keine Input-Validierung

**Empfehlung:** Pydantic-Models für alle Inputs nutzen.

## Testabdeckung

**Aktuell:** 59 Test-Funktionen (10 Test-Dateien)  
**Vorhanden:**
- ✅ api.py (11 Tests)
- ✅ registry.py (16 Tests)
- ✅ search_index.py (9 Tests)
- ✅ config.py (10 Tests)
- ✅ i18n.py (3 Tests)
- ✅ cache.py (2 Tests)
- ✅ gss.py (3 Tests)
- ✅ soep.py (2 Tests)
- ✅ icpsr.py (2 Tests)
- ✅ manual_wvs.py (1 Test)

**Fehlend:**
- ❌ cli.py (0 Tests)
- ❌ server.py (0 Tests)
- ❌ cloud_storage.py (0 Tests)
- ❌ download.py (0 Tests)
- ❌ parsers.py (0 Tests)
- ❌ eurostat.py (0 Tests)
- ❌ ess.py, cses.py, evs.py, issp.py (0 Tests)

**Ziel:** Mindestens 80% Code-Coverage für Core-Module

## Metriken

- **Exception-Handler:** 54 (zu generisch, aber Logging vorhanden)
- **NotImplementedError:** 22 (teilweise erwartet)
- **Tests:** 59 Funktionen (10 Test-Dateien)
- **Adapter:** 9 implementiert
- **Code-Zeilen:** ~4.600
- **Module:** 27 Python-Dateien
- **Dokumentation:** Umfangreich vorhanden

**Siehe auch:** `TECHNISCHE_ANALYSE_2024.md` für eine detaillierte aktuelle Analyse.

# Projektanalyse: socdata

## Übersicht

**Projekt:** socdata - Einheitlicher Zugriff auf sozialwissenschaftliche Datensätze  
**Version:** 0.1.0  
**Status:** Phase 3 größtenteils abgeschlossen, Phase 4 geplant

## Aktueller Projektzustand

### Implementierte Features

#### Phase 1 (MVP) - ✅ Abgeschlossen
- Eurostat adapter (search + load)
- Manual adapter mit WVS recipe
- Parsers und Parquet export
- CLI commands: list, search, load, ingest, show-config
- Basis-Tests und Dokumentation

#### Phase 2 - ✅ Abgeschlossen
- SOEP ODF adapter
- GSS scripted ingestion
- Lokaler Suchindex über Metadaten
- Optionale REST API (FastAPI)

#### Phase 3 - ✅ Abgeschlossen
- ESS adapter
- ICPSR adapter
- ISSP adapter
- CSES adapter
- EVS adapter
- i18n Variable Labels und Mappings
- Performance Tuning und Cloud Storage Option
- Erweiterte Tests und Tutorials
- Eurostat adapter: erweiterte Dataset-Liste

### Projektstruktur

```
src/socdata/
├── __init__.py          # API exports (load, ingest)
├── api.py               # Haupt-API (load, ingest)
├── cli.py               # Typer-basierte CLI
├── server.py            # FastAPI REST Server
└── core/
    ├── cache.py         # Cache-Management mit TTL
    ├── cloud_storage.py # Cloud Storage Backend (S3)
    ├── config.py        # Konfiguration
    ├── download.py      # HTTP Downloads mit Retry
    ├── i18n.py          # Internationalisierung
    ├── models.py        # Pydantic Models
    ├── parsers.py       # Datei-Parser (CSV, Stata, SPSS)
    ├── registry.py      # Adapter-Registry
    ├── search_index.py  # SQLite-basierter Suchindex (FTS5)
    ├── storage.py       # Cache-Pfad-Helpers
    └── types.py         # Typ-Definitionen
└── sources/
    ├── base.py          # BaseAdapter Interface
    ├── cses.py          # CSES Adapter
    ├── ess.py           # ESS Adapter
    ├── eurostat.py      # Eurostat Adapter
    ├── evs.py           # EVS Adapter
    ├── gss.py           # GSS Adapter
    ├── icpsr.py         # ICPSR Adapter
    ├── issp.py          # ISSP Adapter
    ├── manual.py        # Manual Adapter (WVS)
    └── soep.py          # SOEP Adapter
```

## Technische Schulden

### 1. Unvollständige Implementierungen

#### 1.1 i18n-Funktionalität nicht genutzt
**Datei:** `src/socdata/api.py:32-38`
```python
# Apply i18n if language is specified
if language:
    # Note: Variable/value labels are stored in Parquet metadata,
    # not in the DataFrame itself. This would require reading metadata
    # and applying translations, which is a more complex operation.
    # For now, we return the DataFrame as-is.
    # Future enhancement: add method to apply translations to DataFrame columns
    pass
```
**Problem:** Der `language`-Parameter wird ignoriert, obwohl ein I18nManager existiert.  
**Impact:** Nutzer können keine übersetzten Labels erhalten.  
**Lösung:** Parquet-Metadaten lesen und Labels übersetzen, dann auf DataFrame anwenden.

#### 1.2 Config-Loading aus Umgebungsvariablen unvollständig
**Datei:** `src/socdata/core/config.py:28-31`
```python
env_path = os.getenv("SOCDATA_CONFIG")
if env_path and Path(env_path).exists():
    # Simple env-based override later can parse YAML/JSON
    pass
```
**Problem:** Config-Datei wird nicht geladen, obwohl der Pfad geprüft wird.  
**Impact:** Keine Möglichkeit, Konfiguration über Umgebungsvariablen zu setzen.  
**Lösung:** YAML/JSON-Parsing implementieren.

#### 1.3 Cloud Storage Backend abstrakt
**Datei:** `src/socdata/core/cloud_storage.py:10-29`
```python
class CloudStorageBackend:
    def upload_file(self, local_path: Path, remote_path: str) -> None:
        raise NotImplementedError
    # ... weitere NotImplementedError
```
**Problem:** Basis-Klasse ist abstrakt, aber S3StorageBackend ist implementiert.  
**Status:** Funktional, aber könnte klarer strukturiert sein (ABC-Metaclass).

#### 1.4 Eurostat Dynamic Discovery nicht implementiert
**Datei:** `src/socdata/sources/eurostat.py:31-37`
```python
try:
    # eurostat package may have a method to list datasets
    # This is a placeholder - actual implementation depends on eurostat package API
    # For now, we use a curated list but with more datasets
    pass
except Exception:
    pass
```
**Problem:** Dynamische Dataset-Erkennung fehlt, nur kuratierte Liste.  
**Impact:** Neue Eurostat-Datasets werden nicht automatisch erkannt.  
**Lösung:** Eurostat API für Dataset-Liste nutzen.

### 2. Fehlerbehandlung

#### 2.1 Zu generische Exception-Handler
**Gefunden:** 41 Stellen mit `except Exception:` oder `except Exception as e:`

**Problematische Beispiele:**
- `src/socdata/core/registry.py:76-78` - Index-Fehler werden stillschweigend ignoriert
- `src/socdata/core/search_index.py:404-405` - Manifest-Lesefehler werden ignoriert
- `src/socdata/sources/manual.py:124-126` - Parquet-Metadaten-Fehler werden ignoriert

**Problem:** 
- Fehler werden verschluckt, Debugging wird erschwert
- Keine Unterscheidung zwischen erwarteten und unerwarteten Fehlern
- Keine Logging-Infrastruktur

**Empfehlung:**
- Spezifische Exceptions fangen
- Logging einrichten (z.B. `logging`-Modul)
- Wichtige Fehler weiterwerfen, nur erwartete Fehler abfangen

#### 2.2 Fehlende Validierung
**Beispiele:**
- `src/socdata/api.py:28` - Keine Validierung von `dataset_id`-Format
- `src/socdata/cli.py:122` - Filter-Parsing kann fehlschlagen ohne klare Fehlermeldung
- `src/socdata/server.py:100-148` - API-Endpunkte haben keine Input-Validierung

**Empfehlung:**
- Pydantic-Models für Input-Validierung nutzen
- Klare Fehlermeldungen bei ungültigen Eingaben

### 3. Code-Qualität

#### 3.1 Inkonsistente Fehlerbehandlung in Adaptern
Viele Adapter haben ähnliche `except Exception: pass`-Blöcke:
- `src/socdata/sources/gss.py:225-227`
- `src/socdata/sources/soep.py:222-224`
- `src/socdata/sources/ess.py:318-320`
- etc.

**Problem:** Code-Duplikation, keine einheitliche Fehlerbehandlung.  
**Lösung:** Gemeinsame Fehlerbehandlung in BaseAdapter oder Utility-Funktionen.

#### 3.2 Fehlende Typisierung
Einige Funktionen haben unvollständige Typ-Hints:
- `src/socdata/core/search_index.py:340` - Rückgabetyp `Optional[Dict[str, Any]]` könnte spezifischer sein
- `src/socdata/server.py:50` - `root()` hat keinen Rückgabetyp

**Empfehlung:** Vollständige Typisierung für bessere IDE-Unterstützung und Type-Checking.

#### 3.3 SQL-Injection-Risiko (gering)
**Datei:** `src/socdata/core/search_index.py:324-331`
```python
sql = f"""
    SELECT DISTINCT d.id, d.source, d.title
    FROM datasets d
    {join_clause}
    WHERE {where_clause}
    ...
"""
```
**Status:** Aktuell sicher, da `where_clause` aus kontrollierten Bedingungen gebaut wird.  
**Empfehlung:** Explizite Parameterisierung für bessere Lesbarkeit.

### 4. Testabdeckung

**Aktuelle Tests:**
- `test_cache.py` - 2 Tests
- `test_gss.py` - 3 Tests
- `test_i18n.py` - 3 Tests
- `test_icpsr.py` - 2 Tests
- `test_manual_wvs.py` - 1 Test
- `test_search_index.py` - 9 Tests
- `test_soep.py` - 2 Tests

**Fehlende Tests:**
- Keine Tests für `api.py` (load, ingest)
- Keine Tests für `cli.py`
- Keine Tests für `server.py`
- Keine Tests für `registry.py`
- Keine Tests für `cloud_storage.py`
- Keine Tests für `download.py`
- Keine Tests für `parsers.py`
- Keine Tests für Eurostat-Adapter
- Keine Tests für ESS, CSES, EVS, ISSP Adapter

**Empfehlung:** Testabdeckung deutlich erhöhen, besonders für Core-Funktionalität.

### 5. Dokumentation

**Vorhanden:**
- README.md (grundlegend)
- docs/ (MkDocs-basiert)
  - adapters.md
  - api.md
  - architecture.md
  - cli.md
  - configuration.md
  - getting-started.md
  - roadmap.md
  - search.md
  - tutorials/

**Fehlend:**
- API-Dokumentation für Python-API (Docstrings vorhanden, aber nicht vollständig)
- Beispiele für alle Adapter
- Troubleshooting-Guide
- Performance-Tipps

## TODOs und geplante Features

### Phase 4 (Future) - Roadmap
Aus `docs/roadmap.md`:

1. **Zusätzliche Datenquellen**
   - ICPSR Studies (erweitert)
   - Nationale Surveys

2. **Erweiterte i18n**
   - Automatische Übersetzung
   - Aktuell: nur manuelle Übersetzungen

3. **Distributed Caching**
   - Aktuell: nur lokaler Cache
   - Geplant: verteilter Cache

4. **Data Validation und Quality Checks**
   - Aktuell: keine Validierung
   - Geplant: Schema-Validierung, Quality-Checks

5. **Integration mit Analysis Tools**
   - Jupyter Integration
   - R Integration

### Weitere identifizierte TODOs

1. **i18n-Implementierung vervollständigen**
   - Parquet-Metadaten lesen
   - Labels auf DataFrame anwenden
   - Siehe `src/socdata/api.py:32-38`

2. **Config-System erweitern**
   - YAML/JSON-Parsing für Config-Dateien
   - Siehe `src/socdata/core/config.py:28-31`

3. **Eurostat Dynamic Discovery**
   - API-Integration für automatische Dataset-Erkennung
   - Siehe `src/socdata/sources/eurostat.py:31-37`

4. **Logging-Infrastruktur**
   - `logging`-Modul integrieren
   - Strukturierte Logs
   - Log-Level konfigurierbar

5. **Fehlerbehandlung verbessern**
   - Spezifische Exceptions
   - Klare Fehlermeldungen
   - Fehler-Logging

6. **Testabdeckung erhöhen**
   - Core-Module testen
   - Adapter testen
   - Integration-Tests
   - CI/CD Pipeline

7. **Performance-Optimierungen**
   - Lazy Loading für große Datasets (teilweise vorhanden)
   - Caching-Strategien optimieren
   - Parquet-Optimierungen

8. **Dokumentation erweitern**
   - API-Referenz vervollständigen
   - Beispiele für alle Adapter
   - Troubleshooting-Guide

## Empfohlene Prioritäten

### Hoch (Kritisch)
1. **i18n-Funktionalität implementieren** - Feature ist dokumentiert, aber nicht funktional
2. **Logging einrichten** - Wichtig für Debugging und Production
3. **Testabdeckung erhöhen** - Besonders für Core-Module

### Mittel (Wichtig)
4. **Fehlerbehandlung verbessern** - Spezifische Exceptions, bessere Fehlermeldungen
5. **Config-System vervollständigen** - YAML/JSON-Support
6. **Eurostat Dynamic Discovery** - Bessere Dataset-Erkennung

### Niedrig (Nice-to-have)
7. **Dokumentation erweitern** - Beispiele, Troubleshooting
8. **Performance-Optimierungen** - Caching, Lazy Loading
9. **Code-Qualität** - Typisierung, Code-Duplikation reduzieren

## Metriken

- **Code-Zeilen:** ~3000+ (geschätzt)
- **Adapter:** 9 implementiert
- **Tests:** 22 Test-Funktionen
- **Dokumentation:** Umfangreich vorhanden (MkDocs)
- **Technische Schulden:** Mittel (mehrere unvollständige Features, fehlende Tests)

## Zusammenfassung

Das Projekt ist in einem **guten Zustand** mit funktionierender Basis-Infrastruktur. Die Hauptprobleme sind:

1. **Unvollständige Features:** i18n, Config-Loading, Eurostat Discovery
2. **Fehlende Tests:** Besonders für Core-Module und API
3. **Fehlerbehandlung:** Zu generisch, keine Logging-Infrastruktur
4. **Code-Qualität:** Einige Verbesserungen möglich (Typisierung, Duplikation)

Die Architektur ist **solide** und **erweiterbar**. Die meisten technischen Schulden sind nicht kritisch, sollten aber vor größeren Features adressiert werden.

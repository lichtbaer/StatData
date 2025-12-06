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

#### 1.1 i18n-Funktionalität ✅ IMPLEMENTIERT
**Datei:** `src/socdata/api.py:62-177`
**Status:** ✅ Vollständig implementiert
**Details:** 
- Parquet-Metadaten werden gelesen
- Variable/Value Labels werden übersetzt
- Labels werden auf DataFrame angewendet
- Fallback-Mechanismen vorhanden
**Hinweis:** Diese technische Schuld wurde behoben.

#### 1.2 Config-Loading aus Umgebungsvariablen ✅ IMPLEMENTIERT
**Datei:** `src/socdata/core/config.py:32-88`
**Status:** ✅ Vollständig implementiert
**Details:**
- YAML/JSON-Parsing implementiert
- Environment-Variable-Override funktioniert
- Fehlerbehandlung vorhanden
**Hinweis:** Diese technische Schuld wurde behoben.

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
**Gefunden:** 54 Stellen mit `except Exception:` oder `except Exception as e:`

**Status:** ⚠️ Teilweise verbessert
- ✅ Logging-Infrastruktur vorhanden (`src/socdata/core/logging.py`)
- ✅ Spezifische Exceptions definiert (`src/socdata/core/exceptions.py`)
- ⚠️ Viele Adapter nutzen noch generische Exception-Handler

**Problematische Beispiele:**
- `src/socdata/core/registry.py:162` - Index-Fehler werden geloggt, aber stillschweigend ignoriert
- Viele Adapter haben ähnliche `except Exception: pass`-Blöcke

**Empfehlung:**
- Spezifischere Exceptions in Adaptern verwenden
- Gemeinsame Fehlerbehandlung in BaseAdapter
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

**Aktuelle Tests:**
- ✅ `test_api.py` - 11 Tests (vollständig)
- ✅ `test_registry.py` - 16 Tests (vollständig)
- ✅ `test_search_index.py` - 9 Tests
- ✅ `test_config.py` - 10 Tests
- ✅ `test_i18n.py` - 3 Tests
- ✅ `test_cache.py` - 2 Tests
- ✅ `test_gss.py` - 3 Tests
- ✅ `test_soep.py` - 2 Tests
- ✅ `test_icpsr.py` - 2 Tests
- ✅ `test_manual_wvs.py` - 1 Test

**Fehlende Tests:**
- ❌ Keine Tests für `cli.py`
- ❌ Keine Tests für `server.py`
- ❌ Keine Tests für `cloud_storage.py`
- ❌ Keine Tests für `download.py`
- ❌ Keine Tests für `parsers.py`
- ❌ Keine Tests für Eurostat-Adapter
- ❌ Keine Tests für ESS, CSES, EVS, ISSP Adapter

**Empfehlung:** Testabdeckung auf mindestens 80% für Core-Module erhöhen.

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

1. **i18n-Implementierung vervollständigen** ✅ ERLEDIGT
   - ✅ Parquet-Metadaten lesen
   - ✅ Labels auf DataFrame anwenden
   - Status: Vollständig implementiert in `src/socdata/api.py:62-177`

2. **Config-System erweitern** ✅ ERLEDIGT
   - ✅ YAML/JSON-Parsing für Config-Dateien
   - Status: Vollständig implementiert in `src/socdata/core/config.py:56-88`

3. **Eurostat Dynamic Discovery**
   - API-Integration für automatische Dataset-Erkennung
   - Siehe `src/socdata/sources/eurostat.py:31-37`

4. **Logging-Infrastruktur** ✅ ERLEDIGT
   - ✅ `logging`-Modul integriert
   - ✅ Strukturierte Logs
   - ✅ Log-Level konfigurierbar
   - Status: Vollständig implementiert in `src/socdata/core/logging.py`

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
1. **i18n-Funktionalität implementieren** ✅ ERLEDIGT - Vollständig implementiert
2. **Logging einrichten** ✅ ERLEDIGT - Vollständig implementiert
3. **Testabdeckung erhöhen** ⚠️ IN ARBEIT - API und Registry getestet, CLI/Server/Parser fehlen noch

### Mittel (Wichtig)
4. **Fehlerbehandlung verbessern** - Spezifische Exceptions, bessere Fehlermeldungen
5. **Config-System vervollständigen** - YAML/JSON-Support
6. **Eurostat Dynamic Discovery** - Bessere Dataset-Erkennung

### Niedrig (Nice-to-have)
7. **Dokumentation erweitern** - Beispiele, Troubleshooting
8. **Performance-Optimierungen** - Caching, Lazy Loading
9. **Code-Qualität** - Typisierung, Code-Duplikation reduzieren

## Metriken

- **Code-Zeilen:** ~4.600 (gemessen)
- **Module:** 27 Python-Dateien
- **Adapter:** 9 implementiert
- **Tests:** 59 Test-Funktionen (10 Test-Dateien)
- **Dokumentation:** Umfangreich vorhanden (MkDocs)
- **Technische Schulden:** Niedrig-Mittel (mehrere Features implementiert, Testabdeckung noch unvollständig)

## Zusammenfassung

Das Projekt ist in einem **guten Zustand** mit funktionierender Basis-Infrastruktur. Die meisten kritischen technischen Schulden wurden bereits behoben:

1. **✅ Implementierte Features:** i18n, Config-Loading, Logging
2. **⚠️ Testabdeckung:** API und Registry getestet, CLI/Server/Parser fehlen noch
3. **⚠️ Fehlerbehandlung:** Logging vorhanden, aber noch zu generische Exception-Handler in Adaptern
4. **Code-Qualität:** Einige Verbesserungen möglich (Typisierung, Duplikation)

Die Architektur ist **solide** und **erweiterbar**. Die verbleibenden technischen Schulden sind nicht kritisch, sollten aber vor größeren Features adressiert werden.

**Siehe auch:** `TECHNISCHE_ANALYSE_2024.md` für eine detaillierte aktuelle Analyse.

# Adapters

## Eurostat (direct)

- Source: official Eurostat API via the `eurostat` Python package
- Status: implemented (search + load)

Example:

```python
import socdata as sd

# Minimal filter
df = sd.load("eurostat:une_rt_m", filters={"geo": "DE"})
```

CLI:

```bash
socdata load-cmd eurostat:une_rt_m --filters 'geo=DE'
```

Notes:
- Certain dimension combinations are invalid. Start with a minimal filter (e.g., `geo`).
- Expanded dataset list includes 10 common Eurostat datasets (unemployment, GDP, population, education, health, crime, migration, etc.)

## Manual (recipes)

- Purpose: ingest from locally downloaded files when no API/package exists
- Example target: WVS (World Values Survey)

Usage:

```bash
# Either pass the downloaded ZIP directly (auto-extracts and picks the main file)
socdata ingest-cmd manual:wvs ~/Downloads/WVS_Cross-National_Wave7.zip --export wvs.parquet

# Or pass an extracted data file directly
socdata ingest-cmd manual:wvs ~/path/to/WVS_Extract.dta --export wvs.parquet
```

Artifacts written to cache:
- Normalized Parquet with Arrow metadata (variable/value labels, provenance): `~/.socdata/manual/manual_wvs/latest/processed/data.parquet`
- Manifest JSON: `~/.socdata/manual/manual_wvs/latest/meta/ingestion_manifest.json`

## SOEP (ODF)

- Source: SOEP (Socio-Economic Panel) Open Data Format
- Status: implemented (ingest from ODF ZIP files)

SOEP ODF files are ZIP archives containing data files and documentation. The adapter automatically extracts and processes the main data file.

Usage:

```bash
# Ingest from local ODF ZIP file
socdata ingest-cmd soep:soep-core ~/Downloads/soep_core.zip --export soep.parquet
```

Python:

```python
import socdata as sd

# Ingest from local file
df = sd.ingest("soep:soep-core", file_path="~/Downloads/soep_core.zip")

# Load from cache (after ingestion)
df = sd.load("soep:soep-core")
```

Notes:
- SOEP data requires registration and data use agreement
- ODF ZIP files are automatically extracted
- The adapter prefers Stata/SPSS formats over CSV when multiple files are present
- Original ZIP is cached in `raw/` directory

## GSS (scripted)

- Source: General Social Survey (NORC at University of Chicago)
- Status: implemented (ingest from local files)

GSS data is available after registration. This adapter supports ingestion from downloaded GSS data files.

Usage:

```bash
# Ingest from local GSS data file
socdata ingest-cmd gss:gss-2022 ~/Downloads/GSS2022.dta --export gss.parquet
```

Python:

```python
import socdata as sd

# Ingest from local file
df = sd.ingest("gss:gss-2022", file_path="~/Downloads/GSS2022.dta")

# Load from cache with filters
df = sd.load("gss:gss-cumulative", filters={"year": 2022})
```

Notes:
- GSS data requires registration at https://gss.norc.org
- Supports Stata (.dta), SPSS (.sav), and CSV formats
- Version detection from filename (e.g., GSS2022.dta → gss-2022)
- Filters can be applied when loading from cache

## ESS (European Social Survey)

- Source: European Social Survey (https://www.europeansocialsurvey.org/)
- Status: implemented (ingest from local files)

ESS data is available after registration. This adapter supports ingestion from downloaded ESS data files (SPSS, Stata, or CSV formats).

Usage:

```bash
# Ingest from local ESS data file
socdata ingest-cmd ess:ess-round-10 ~/Downloads/ESS10e01_1.sav --export ess10.parquet

# Or from ZIP archive
socdata ingest-cmd ess:ess-round-10 ~/Downloads/ESS10.zip --export ess10.parquet
```

Python:

```python
import socdata as sd

# Ingest from local file
df = sd.ingest("ess:ess-round-10", file_path="~/Downloads/ESS10e01_1.sav")

# Load from cache with filters
df = sd.load("ess:ess-round-10", filters={"cntry": "DE"})
```

Notes:
- ESS data requires registration at https://www.europeansocialsurvey.org/
- Supports Stata (.dta), SPSS (.sav), and CSV formats
- Auto-detects round from filename (e.g., ESS10e01_1.sav → ess-round-10)
- Supports all ESS rounds (1-10) and cumulative file
- Filters can be applied when loading from cache

## ICPSR

- Source: Inter-university Consortium for Political and Social Research
- Status: implemented (ingest from local files)

ICPSR data is available after registration. This adapter supports ingestion from downloaded ICPSR data files.

Usage:

```bash
socdata ingest-cmd icpsr:icpsr-general ~/Downloads/ICPSR_12345.zip --export icpsr.parquet
```

Notes:
- ICPSR data requires registration at https://www.icpsr.umich.edu/
- Auto-detects study number from filename (e.g., ICPSR_12345.zip → icpsr-12345)
- Supports ANES and WVS datasets from ICPSR

## ISSP

- Source: International Social Survey Programme
- Status: implemented (ingest from local files)

ISSP data is available after registration. This adapter supports all ISSP waves from 1985 to 2020.

Usage:

```bash
socdata ingest-cmd issp:issp-2019 ~/Downloads/ISSP2019.sav --export issp.parquet
```

Notes:
- ISSP data requires registration at https://www.issp.org/
- Auto-detects year from filename
- Supports all ISSP waves (1985-2020)

## CSES

- Source: Comparative Study of Electoral Systems
- Status: implemented (ingest from local files)

CSES data is available after registration. This adapter supports all CSES modules.

Usage:

```bash
socdata ingest-cmd cses:cses-module-5 ~/Downloads/CSES_Module5.sav --export cses.parquet
```

Notes:
- CSES data requires registration at https://cses.org/
- Auto-detects module from filename
- Supports modules 1-5 and integrated dataset

## EVS

- Source: European Values Study
- Status: implemented (ingest from local files)

EVS data is available after registration. This adapter supports all EVS waves.

Usage:

```bash
socdata ingest-cmd evs:evs-2017 ~/Downloads/EVS_2017.sav --export evs.parquet
```

Notes:
- EVS data requires registration at https://europeanvaluesstudy.eu/
- Auto-detects wave from filename
- Supports waves 1981, 1990, 1999, 2008, 2017 and integrated dataset

## ALLBUS (German General Social Survey)

- Source: ALLBUS (Allgemeine Bevölkerungsumfrage der Sozialwissenschaften) by GESIS
- Status: implemented (ingest from local files)

ALLBUS is the German equivalent of the GSS, conducted by GESIS. This adapter supports all ALLBUS waves from 1980 to 2021.

Usage:

```bash
# Ingest from local ALLBUS data file
socdata ingest-cmd allbus:allbus-2021 ~/Downloads/ALLBUS2021.sav --export allbus.parquet
```

Python:

```python
import socdata as sd

# Ingest from local file
df = sd.ingest("allbus:allbus-2021", file_path="~/Downloads/ALLBUS2021.sav")

# Load from cache with filters
df = sd.load("allbus:allbus-2021", filters={"year": 2021})
```

Notes:
- ALLBUS data requires registration at https://www.gesis.org/allbus/
- Auto-detects year from filename
- Supports all ALLBUS waves (1980-2021) and cumulative dataset
- Filters can be applied when loading from cache

## ICPSR (Extended)

- Source: Inter-university Consortium for Political and Social Research
- Status: implemented (ingest from local files, extended with more studies)

ICPSR provides access to a wide range of social science datasets. This adapter has been extended to support additional major studies.

Supported Studies:
- General Archive (various studies)
- American National Election Studies (ANES)
- World Values Survey (via ICPSR)
- General Social Survey (GSS via ICPSR)
- Panel Study of Income Dynamics (PSID)
- National Longitudinal Survey (NLS)
- Health and Retirement Study (HRS)
- Add Health (National Longitudinal Study of Adolescent to Adult Health)
- Current Population Survey (CPS)
- Behavioral Risk Factor Surveillance System (BRFSS)

Usage:

```bash
# Ingest ICPSR study
socdata ingest-cmd icpsr:icpsr-general ~/Downloads/ICPSR_12345.zip --export icpsr.parquet
```

Notes:
- ICPSR data requires registration at https://www.icpsr.umich.edu/
- Auto-detects study number from filename (e.g., ICPSR_12345.zip → icpsr-12345)
- Supports ANES, WVS, GSS, PSID, NLS, HRS, Add Health, CPS, and BRFSS datasets

## Open Data Portals

- Source: Various open data portals (data.gov, data.gouv.fr, data.gov.uk, etc.)
- Status: implemented (generic CKAN API support)

This adapter provides generic support for open data portals that use the CKAN API standard, including:
- data.gov (US)
- data.gouv.fr (France)
- data.gov.uk (UK)
- And other CKAN-based portals

Usage:

```python
import socdata as sd

# Load from open data portal (CKAN API)
df = sd.load("opendata:package-name")

# Or ingest from URL
df = sd.ingest("opendata", file_path="https://data.gov/api/3/action/datastore_search?resource_id=...")
```

Notes:
- Uses CKAN API standard (version 3)
- Supports CSV, TSV, JSON, and Excel formats
- May require API key for some portals
- Can work with direct URLs to data files
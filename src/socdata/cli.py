from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .api import load, ingest
from .core.config import get_config
from .core.registry import list_datasets, search_datasets


console = Console()
app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def version() -> None:
    from . import __version__

    console.print(f"socdata {__version__}")


@app.command()
def show_config() -> None:
    cfg = get_config()
    console.print_json(data=cfg.model_dump())


@app.command()
def list(source: Optional[str] = None) -> None:  # noqa: A001 - shadow builtins ok for CLI
    datasets = list_datasets(source)
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID")
    table.add_column("Source")
    table.add_column("Title")
    for ds in datasets:
        table.add_row(ds.id, ds.source, ds.title)
    console.print(table)


@app.command()
def search(query: str) -> None:
    results = search_datasets(query)
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID")
    table.add_column("Source")
    table.add_column("Title")
    for ds in results:
        table.add_row(ds.id, ds.source, ds.title)
    console.print(table)


@app.command()
def load_cmd(dataset: str, filters: Optional[str] = None, export: Optional[Path] = None) -> None:
    filters_dict = None
    if filters:
        try:
            filters_dict = json.loads(filters)
        except json.JSONDecodeError:
            # accept simple key=value,key2=value2 format
            parts = [p.strip() for p in filters.split(",") if p.strip()]
            kv = {}
            for p in parts:
                if "=" in p:
                    k, v = p.split("=", 1)
                    kv[k.strip()] = v.strip()
            filters_dict = kv or None
    df = load(dataset, filters=filters_dict)
    console.print(df.head())
    if export:
        export = Path(export)
        export.parent.mkdir(parents=True, exist_ok=True)
        if export.suffix.lower() in {".parquet"}:
            df.to_parquet(export)
        else:
            df.to_csv(export, index=False)
        console.print(f"Exported to {export}")


@app.command()
def ingest_cmd(adapter: str, file_path: Path, export: Optional[Path] = None) -> None:
    df = ingest(adapter, file_path=str(file_path))
    console.print(df.head())
    if export:
        export = Path(export)
        export.parent.mkdir(parents=True, exist_ok=True)
        if export.suffix.lower() in {".parquet"}:
            df.to_parquet(export)
        else:
            df.to_csv(export, index=False)
        console.print(f"Exported to {export}")


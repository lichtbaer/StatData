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
def search(
	query: str,
	source: Optional[str] = None,
	variable: Optional[str] = None,
	no_index: bool = False,
) -> None:
	"""
	Search datasets using full-text search.
	
	Examples:
		socdata search "unemployment"
		socdata search "income" --source gss
		socdata search "age" --variable age
	"""
	if variable:
		from .core.registry import search_datasets_advanced
		results = search_datasets_advanced(query=query, source=source, variable_name=variable)
	else:
		results = search_datasets(query, source=source, use_index=not no_index)
	
	table = Table(show_header=True, header_style="bold magenta")
	table.add_column("ID")
	table.add_column("Source")
	table.add_column("Title")
	for ds in results:
		table.add_row(ds.id, ds.source, ds.title)
	console.print(table)
	if not results:
		console.print("[yellow]No datasets found[/yellow]")


@app.command()
def info(dataset: str) -> None:
	"""Show detailed information about a dataset."""
	from .core.search_index import get_index
	
	try:
		index = get_index()
		info = index.get_dataset_info(dataset)
		if info:
			console.print(f"[bold]Dataset:[/bold] {info['id']}")
			console.print(f"[bold]Source:[/bold] {info['source']}")
			console.print(f"[bold]Title:[/bold] {info['title']}")
			if info.get("description"):
				console.print(f"[bold]Description:[/bold] {info['description']}")
			if info.get("license"):
				console.print(f"[bold]License:[/bold] {info['license']}")
			if info.get("variable_labels"):
				console.print(f"\n[bold]Variables:[/bold] {len(info['variable_labels'])}")
				# Show first 10 variables
				for var_name, label in list(info['variable_labels'].items())[:10]:
					console.print(f"  - {var_name}: {label}")
				if len(info['variable_labels']) > 10:
					console.print(f"  ... and {len(info['variable_labels']) - 10} more")
		else:
			console.print(f"[red]Dataset '{dataset}' not found in index[/red]")
			console.print("[yellow]Try rebuilding the index with: socdata rebuild-index[/yellow]")
	except Exception as e:
		console.print(f"[red]Error: {e}[/red]")


@app.command()
def rebuild_index() -> None:
	"""Rebuild the search index from all available datasets."""
	from .core.search_index import get_index
	
	console.print("[yellow]Rebuilding search index...[/yellow]")
	try:
		index = get_index()
		index.rebuild_index()
		console.print("[green]Search index rebuilt successfully[/green]")
	except Exception as e:
		console.print(f"[red]Error rebuilding index: {e}[/red]")


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
def ingest_cmd(dataset: str, file_path: Path, export: Optional[Path] = None) -> None:
	df = ingest(dataset, file_path=str(file_path))
	console.print(df.head())
	if export:
		export = Path(export)
		export.parent.mkdir(parents=True, exist_ok=True)
		if export.suffix.lower() in {".parquet"}:
			df.to_parquet(export)
		else:
			df.to_csv(export, index=False)
		console.print(f"Exported to {export}")


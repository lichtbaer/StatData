from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import pyreadstat
from pandas.io.stata import StataReader


def read_table(path: Path, *, encoding: Optional[str] = None, sep: Optional[str] = None) -> pd.DataFrame:
	lower = path.suffix.lower()
	if lower in {".csv", ".tsv"}:
		if lower == ".tsv" and sep is None:
			sep = "\t"
		return pd.read_csv(path, encoding=encoding, sep=sep)
	if lower in {".dta"}:
		return pd.read_stata(path)
	if lower in {".sav", ".zsav"}:
		df, _meta = pyreadstat.read_sav(path)
		return df
	raise ValueError(f"Unsupported file type: {path.suffix}")


def read_table_with_meta(path: Path, *, encoding: Optional[str] = None, sep: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
	lower = path.suffix.lower()
	if lower in {".csv", ".tsv"}:
		if lower == ".tsv" and sep is None:
			sep = "\t"
		df = pd.read_csv(path, encoding=encoding, sep=sep)
		return df, {"variable_labels": {}, "value_labels": {}}
	if lower in {".dta"}:
		# Keep codes; collect variable labels via StataReader
		with StataReader(str(path)) as rdr:
			var_labels = rdr.variable_labels()
		df = pd.read_stata(path, convert_categoricals=False)
		return df, {"variable_labels": var_labels or {}, "value_labels": {}}
	if lower in {".sav", ".zsav"}:
		# Keep numeric codes, collect labels
		df, meta = pyreadstat.read_sav(path, apply_value_formats=False)
		var_labels = {}
		if getattr(meta, "column_names", None) and getattr(meta, "column_labels", None):
			var_labels = {name: label for name, label in zip(meta.column_names, meta.column_labels)}
		val_labels = {}
		if getattr(meta, "variable_value_labels", None):
			for col, mapping in meta.variable_value_labels.items():
				val_labels[col] = {str(k): str(v) for k, v in mapping.items()}
		return df, {"variable_labels": var_labels, "value_labels": val_labels}
	raise ValueError(f"Unsupported file type: {path.suffix}")


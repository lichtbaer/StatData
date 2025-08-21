from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import pyreadstat


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


from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DatasetSummary:
    id: str
    source: str
    title: str


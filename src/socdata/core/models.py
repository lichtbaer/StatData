from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class DatasetDescriptor(BaseModel):
    id: str
    source: str
    title: str
    homepage: Optional[HttpUrl] = None
    license: Optional[str] = None
    terms_url: Optional[HttpUrl] = None
    access_mode: str = Field(description="direct|semi|manual")


class ReleaseInfo(BaseModel):
    version: str
    published_at: Optional[datetime] = None
    urls: List[HttpUrl] = Field(default_factory=list)
    checksum: Optional[str] = None
    size_bytes: Optional[int] = None


class VariableDescriptor(BaseModel):
    name: str
    label: Optional[str] = None
    dtype: Optional[str] = None
    categories: Optional[Dict[str, str]] = None
    original_name: Optional[str] = None


class IngestionManifest(BaseModel):
    timestamp: datetime
    adapter: str
    parameters: Dict[str, str]
    source_hashes: Dict[str, str] = Field(default_factory=dict)
    transforms: List[str] = Field(default_factory=list)


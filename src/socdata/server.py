from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .api import load, ingest
from .core.registry import list_datasets, search_datasets, search_datasets_advanced
from .core.search_index import get_index
from .core.types import DatasetSummary


app = FastAPI(
    title="SocData API",
    description="Unified access to social science datasets",
    version="0.1.0",
)


class LoadRequest(BaseModel):
    dataset_id: str
    filters: Optional[Dict[str, Any]] = None
    format: str = "json"  # json, csv, parquet


class IngestRequest(BaseModel):
    dataset_id: str
    file_path: str
    format: str = "json"  # json, csv, parquet


class DatasetInfoResponse(BaseModel):
    id: str
    source: str
    title: str
    description: Optional[str] = None
    license: Optional[str] = None
    access_mode: Optional[str] = None
    variable_labels: Optional[Dict[str, str]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@app.get("/")
async def root():
    return {
        "name": "SocData API",
        "version": "0.1.0",
        "endpoints": {
            "datasets": "/datasets",
            "search": "/search",
            "info": "/datasets/{dataset_id}/info",
            "load": "/datasets/{dataset_id}/load",
            "ingest": "/ingest",
        },
    }


@app.get("/datasets", response_model=List[Dict[str, str]])
async def get_datasets(source: Optional[str] = None):
    """List all available datasets, optionally filtered by source."""
    datasets = list_datasets(source)
    return [{"id": ds.id, "source": ds.source, "title": ds.title} for ds in datasets]


@app.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    source: Optional[str] = None,
    variable: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """Search datasets using full-text search."""
    if variable:
        results = search_datasets_advanced(query=q, source=source, variable_name=variable)
    else:
        results = search_datasets(q, source=source)
    
    return [{"id": ds.id, "source": ds.source, "title": ds.title} for ds in results[:limit]]


@app.get("/datasets/{dataset_id}/info", response_model=DatasetInfoResponse)
async def get_dataset_info(dataset_id: str):
    """Get detailed information about a dataset."""
    try:
        index = get_index()
        info = index.get_dataset_info(dataset_id)
        if info:
            return DatasetInfoResponse(**info)
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/datasets/{dataset_id}/load")
async def load_dataset(
    dataset_id: str,
    request: Optional[LoadRequest] = None,
    filters: Optional[str] = Query(None, description="JSON filters"),
    format: str = Query("json", description="Output format: json, csv, parquet"),
):
    """Load a dataset with optional filters."""
    try:
        filters_dict = None
        if request and request.filters:
            filters_dict = request.filters
        elif filters:
            filters_dict = json.loads(filters)
        
        df = load(dataset_id, filters=filters_dict or {})
        
        if format == "csv":
            from io import StringIO
            output = StringIO()
            df.to_csv(output, index=False)
            return JSONResponse(
                content={"data": output.getvalue()},
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="{dataset_id.replace(":", "_")}.csv"'},
            )
        elif format == "parquet":
            from io import BytesIO
            from fastapi.responses import Response
            output = BytesIO()
            df.to_parquet(output, index=False)
            output.seek(0)
            return Response(
                content=output.getvalue(),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{dataset_id.replace(":", "_")}.parquet"'},
            )
        else:
            return {
                "dataset_id": dataset_id,
                "filters": filters_dict,
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.head(100).to_dict(orient="records"),
            }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest")
async def ingest_dataset(request: IngestRequest):
    """Ingest a dataset from a local file path."""
    try:
        file_path = Path(request.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        
        df = ingest(request.dataset_id, file_path=str(file_path))
        
        if request.format == "csv":
            from io import StringIO
            output = StringIO()
            df.to_csv(output, index=False)
            return JSONResponse(
                content={"data": output.getvalue()},
                media_type="text/csv",
            )
        elif request.format == "parquet":
            from io import BytesIO
            from fastapi.responses import Response
            output = BytesIO()
            df.to_parquet(output, index=False)
            output.seek(0)
            return Response(
                content=output.getvalue(),
                media_type="application/octet-stream",
                headers={"Content-Disposition": f'attachment; filename="{request.dataset_id.replace(":", "_")}.parquet"'},
            )
        else:
            return {
                "dataset_id": request.dataset_id,
                "file_path": str(file_path),
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.head(100).to_dict(orient="records"),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rebuild-index")
async def rebuild_index():
    """Rebuild the search index from all available datasets."""
    try:
        index = get_index()
        index.rebuild_index()
        return {"status": "success", "message": "Search index rebuilt successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

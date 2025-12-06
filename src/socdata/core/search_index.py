from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .config import get_config
from .types import DatasetSummary
from .logging import get_logger
from .exceptions import SearchIndexError

logger = get_logger(__name__)


class SearchIndex:
    """
    Local search index for dataset metadata.
    
    Uses SQLite with FTS5 for full-text search over:
    - Dataset titles and IDs
    - Variable labels
    - Value labels
    - Source information
    """

    def __init__(self, index_path: Optional[Path] = None):
        if index_path is None:
            cfg = get_config()
            index_path = cfg.cache_dir / "search_index.db"
        
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database with FTS5 tables."""
        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()
        
        # Check if FTS5 is available
        try:
            # Try to create a test FTS5 table
            cursor.execute("CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_test USING fts5(test)")
            cursor.execute("DROP TABLE IF EXISTS _fts5_test")
            self._fts5_available = True
        except (sqlite3.OperationalError, sqlite3.DatabaseError):
            self._fts5_available = False
        
        # Main datasets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                license TEXT,
                access_mode TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # FTS5 virtual table for full-text search (if available)
        if self._fts5_available:
            try:
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS datasets_fts USING fts5(
                        id,
                        source,
                        title,
                        description,
                        variable_labels,
                        value_labels,
                        content='datasets',
                        content_rowid='rowid'
                    )
                """)
            except sqlite3.OperationalError:
                self._fts5_available = False
        
        # Variable labels table (for detailed search)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS variable_labels (
                dataset_id TEXT NOT NULL,
                variable_name TEXT NOT NULL,
                label TEXT,
                PRIMARY KEY (dataset_id, variable_name),
                FOREIGN KEY (dataset_id) REFERENCES datasets(id)
            )
        """)
        
        # Index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_datasets_source 
            ON datasets(source)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_variable_labels_dataset 
            ON variable_labels(dataset_id)
        """)
        
        conn.commit()
        conn.close()

    def index_dataset(
        self,
        dataset_id: str,
        source: str,
        title: str,
        description: Optional[str] = None,
        license: Optional[str] = None,
        access_mode: str = "direct",
        variable_labels: Optional[Dict[str, str]] = None,
        value_labels: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> None:
        """
        Index a dataset with its metadata.
        
        Args:
            dataset_id: Full dataset ID (e.g., 'eurostat:une_rt_m')
            source: Source name (e.g., 'eurostat')
            title: Dataset title
            description: Optional description
            license: Optional license information
            access_mode: Access mode (direct|semi|manual)
            variable_labels: Dictionary of variable name -> label
            value_labels: Dictionary of variable name -> {value: label}
        """
        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        # Check if exists
        cursor.execute("SELECT rowid FROM datasets WHERE id = ?", (dataset_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update
            cursor.execute("""
                UPDATE datasets 
                SET title = ?, description = ?, license = ?, access_mode = ?, updated_at = ?
                WHERE id = ?
            """, (title, description, license, access_mode, now, dataset_id))
            rowid = exists[0]
        else:
            # Insert
            cursor.execute("""
                INSERT INTO datasets (id, source, title, description, license, access_mode, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (dataset_id, source, title, description, license, access_mode, now, now))
            rowid = cursor.lastrowid
        
        # Update variable labels
        cursor.execute("DELETE FROM variable_labels WHERE dataset_id = ?", (dataset_id,))
        if variable_labels:
            for var_name, label in variable_labels.items():
                cursor.execute("""
                    INSERT INTO variable_labels (dataset_id, variable_name, label)
                    VALUES (?, ?, ?)
                """, (dataset_id, var_name, label))
        
        # Update FTS5 index (if available)
        if self._fts5_available:
            var_labels_text = json.dumps(variable_labels or {}) if variable_labels else ""
            val_labels_text = json.dumps(value_labels or {}) if value_labels else ""
            
            try:
                if exists:
                    cursor.execute("""
                        UPDATE datasets_fts 
                        SET title = ?, description = ?, variable_labels = ?, value_labels = ?
                        WHERE rowid = ?
                    """, (title, description or "", var_labels_text, val_labels_text, rowid))
                else:
                    cursor.execute("""
                        INSERT INTO datasets_fts (rowid, id, source, title, description, variable_labels, value_labels)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (rowid, dataset_id, source, title, description or "", var_labels_text, val_labels_text))
            except sqlite3.OperationalError:
                # FTS5 not available, continue without it
                pass
        
        conn.commit()
        conn.close()

    def search(
        self,
        query: str,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[DatasetSummary]:
        """
        Search datasets using full-text search.
        
        Args:
            query: Search query (supports FTS5 syntax if available, otherwise simple LIKE)
            source: Optional source filter
            limit: Maximum number of results
        
        Returns:
            List of matching DatasetSummary objects
        """
        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()
        
        if self._fts5_available:
            # Use FTS5 for full-text search
            if source:
                sql = """
                    SELECT d.id, d.source, d.title
                    FROM datasets d
                    JOIN datasets_fts fts ON d.rowid = fts.rowid
                    WHERE datasets_fts MATCH ? AND d.source = ?
                    ORDER BY rank
                    LIMIT ?
                """
                params = (query, source, limit)
            else:
                sql = """
                    SELECT d.id, d.source, d.title
                    FROM datasets d
                    JOIN datasets_fts fts ON d.rowid = fts.rowid
                    WHERE datasets_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """
                params = (query, limit)
        else:
            # Fallback to simple LIKE search
            query_pattern = f"%{query}%"
            if source:
                sql = """
                    SELECT id, source, title
                    FROM datasets
                    WHERE (title LIKE ? OR id LIKE ? OR description LIKE ?) AND source = ?
                    LIMIT ?
                """
                params = (query_pattern, query_pattern, query_pattern, source, limit)
            else:
                sql = """
                    SELECT id, source, title
                    FROM datasets
                    WHERE title LIKE ? OR id LIKE ? OR description LIKE ?
                    LIMIT ?
                """
                params = (query_pattern, query_pattern, query_pattern, limit)
        
        try:
            cursor.execute(sql, params)
            results = cursor.fetchall()
        except sqlite3.OperationalError:
            # Fallback if FTS5 query fails
            query_pattern = f"%{query}%"
            if source:
                sql = """
                    SELECT id, source, title
                    FROM datasets
                    WHERE (title LIKE ? OR id LIKE ?) AND source = ?
                    LIMIT ?
                """
                cursor.execute(sql, (query_pattern, query_pattern, source, limit))
            else:
                sql = """
                    SELECT id, source, title
                    FROM datasets
                    WHERE title LIKE ? OR id LIKE ?
                    LIMIT ?
                """
                cursor.execute(sql, (query_pattern, query_pattern, limit))
            results = cursor.fetchall()
        
        conn.close()
        
        return [DatasetSummary(id=row[0], source=row[1], title=row[2]) for row in results]

    def search_advanced(
        self,
        query: Optional[str] = None,
        source: Optional[str] = None,
        variable_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[DatasetSummary]:
        """
        Advanced search with multiple filters.
        
        Args:
            query: Full-text search query
            source: Filter by source
            variable_name: Search for datasets containing this variable
            limit: Maximum number of results
        
        Returns:
            List of matching DatasetSummary objects
        """
        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()
        
        conditions = []
        params: List[Any] = []
        
        if query:
            if self._fts5_available:
                conditions.append("datasets_fts MATCH ?")
                params.append(query)
            else:
                query_pattern = f"%{query}%"
                conditions.append("(d.title LIKE ? OR d.id LIKE ? OR d.description LIKE ?)")
                params.extend([query_pattern, query_pattern, query_pattern])
        
        if source:
            conditions.append("d.source = ?")
            params.append(source)
        
        if variable_name:
            conditions.append("EXISTS (SELECT 1 FROM variable_labels vl WHERE vl.dataset_id = d.id AND vl.variable_name LIKE ?)")
            params.append(f"%{variable_name}%")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        join_clause = ""
        if query and self._fts5_available:
            join_clause = "JOIN datasets_fts fts ON d.rowid = fts.rowid"
        
        sql = f"""
            SELECT DISTINCT d.id, d.source, d.title
            FROM datasets d
            {join_clause}
            WHERE {where_clause}
            ORDER BY d.updated_at DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        
        return [DatasetSummary(id=row[0], source=row[1], title=row[2]) for row in results]

    def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a dataset."""
        conn = sqlite3.connect(self.index_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, source, title, description, license, access_mode, created_at, updated_at
            FROM datasets
            WHERE id = ?
        """, (dataset_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        # Get variable labels
        cursor.execute("""
            SELECT variable_name, label
            FROM variable_labels
            WHERE dataset_id = ?
            ORDER BY variable_name
        """, (dataset_id,))
        
        var_labels = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            "id": row[0],
            "source": row[1],
            "title": row[2],
            "description": row[3],
            "license": row[4],
            "access_mode": row[5],
            "created_at": row[6],
            "updated_at": row[7],
            "variable_labels": var_labels,
        }

    def rebuild_index(self) -> None:
        """Rebuild the entire index from cached datasets."""
        from ..core.registry import list_datasets
        from ..core.storage import get_dataset_dir
        
        # Get all datasets from adapters
        all_datasets = list_datasets()
        
        # Index each dataset
        for ds in all_datasets:
            # Try to load additional metadata from cache
            cache_dir = get_dataset_dir(ds.source, ds.id.replace(":", "_"), "latest")
            manifest_path = cache_dir / "meta" / "ingestion_manifest.json"
            
            variable_labels = {}
            value_labels = {}
            license_info = None
            
            if manifest_path.exists():
                try:
                    manifest_data = json.loads(manifest_path.read_text())
                    variable_labels = manifest_data.get("variable_labels", {})
                    value_labels = manifest_data.get("value_labels", {})
                    license_info = manifest_data.get("license")
                except Exception as e:
                    logger.debug(f"Could not load manifest for {ds.id}: {e}")
            
            self.index_dataset(
                dataset_id=ds.id,
                source=ds.source,
                title=ds.title,
                variable_labels=variable_labels,
                value_labels=value_labels,
                license=license_info,
            )

    def clear_index(self) -> None:
        """Clear the entire index."""
        if self.index_path.exists():
            self.index_path.unlink()
        self._init_db()


# Global index instance
_index: Optional[SearchIndex] = None


def get_index() -> SearchIndex:
    """Get or create the global search index instance."""
    global _index
    if _index is None:
        _index = SearchIndex()
    return _index

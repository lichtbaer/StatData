from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .config import get_config


class CloudStorageBackend:
    """
    Abstract base class for cloud storage backends.
    """

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        """Upload a file to cloud storage."""
        raise NotImplementedError

    def download_file(self, remote_path: str, local_path: Path) -> None:
        """Download a file from cloud storage."""
        raise NotImplementedError

    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in cloud storage."""
        raise NotImplementedError

    def delete_file(self, remote_path: str) -> None:
        """Delete a file from cloud storage."""
        raise NotImplementedError


class S3StorageBackend(CloudStorageBackend):
    """
    S3-compatible storage backend.
    
    Requires boto3 package: pip install boto3
    """

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )
        
        self.bucket_name = bucket_name
        
        # Create S3 client
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=region_name or os.getenv("AWS_REGION", "us-east-1"),
        )
        
        self.s3_client = session.client(
            "s3",
            endpoint_url=endpoint_url or os.getenv("AWS_ENDPOINT_URL"),
        )

    def upload_file(self, local_path: Path, remote_path: str) -> None:
        """Upload a file to S3."""
        self.s3_client.upload_file(str(local_path), self.bucket_name, remote_path)

    def download_file(self, remote_path: str, local_path: Path) -> None:
        """Download a file from S3."""
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.s3_client.download_file(self.bucket_name, remote_path, str(local_path))

    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=remote_path)
            return True
        except Exception:
            return False

    def delete_file(self, remote_path: str) -> None:
        """Delete a file from S3."""
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=remote_path)


class CloudStorageManager:
    """
    Manager for cloud storage operations.
    
    Supports multiple backends (S3, etc.) and provides a unified interface.
    """

    def __init__(self, backend: Optional[CloudStorageBackend] = None):
        self.backend = backend
        self._init_from_config()

    def _init_from_config(self) -> None:
        """Initialize backend from configuration."""
        if self.backend is not None:
            return
        
        cfg = get_config()
        
        # Check for S3 configuration
        s3_bucket = os.getenv("SOCDATA_S3_BUCKET")
        if s3_bucket:
            try:
                self.backend = S3StorageBackend(bucket_name=s3_bucket)
            except ImportError:
                pass  # boto3 not installed

    def is_available(self) -> bool:
        """Check if cloud storage is available."""
        return self.backend is not None

    def upload_dataset(
        self,
        source: str,
        dataset: str,
        version: str = "latest",
    ) -> None:
        """
        Upload a dataset to cloud storage.
        
        Args:
            source: Source name (e.g., 'eurostat')
            dataset: Dataset name
            version: Dataset version
        """
        if not self.is_available():
            raise RuntimeError("Cloud storage backend not configured")
        
        from .storage import get_dataset_dir
        
        cache_dir = get_dataset_dir(source, dataset, version)
        parquet_path = cache_dir / "processed" / "data.parquet"
        manifest_path = cache_dir / "meta" / "ingestion_manifest.json"
        
        if parquet_path.exists():
            remote_path = f"{source}/{dataset}/{version}/processed/data.parquet"
            self.backend.upload_file(parquet_path, remote_path)
        
        if manifest_path.exists():
            remote_path = f"{source}/{dataset}/{version}/meta/ingestion_manifest.json"
            self.backend.upload_file(manifest_path, remote_path)

    def download_dataset(
        self,
        source: str,
        dataset: str,
        version: str = "latest",
    ) -> None:
        """
        Download a dataset from cloud storage.
        
        Args:
            source: Source name
            dataset: Dataset name
            version: Dataset version
        """
        if not self.is_available():
            raise RuntimeError("Cloud storage backend not configured")
        
        from .storage import get_dataset_dir
        
        cache_dir = get_dataset_dir(source, dataset, version)
        parquet_path = cache_dir / "processed" / "data.parquet"
        manifest_path = cache_dir / "meta" / "ingestion_manifest.json"
        
        # Download parquet file
        remote_path = f"{source}/{dataset}/{version}/processed/data.parquet"
        if self.backend.file_exists(remote_path):
            self.backend.download_file(remote_path, parquet_path)
        
        # Download manifest
        remote_path = f"{source}/{dataset}/{version}/meta/ingestion_manifest.json"
        if self.backend.file_exists(remote_path):
            self.backend.download_file(remote_path, manifest_path)


# Global cloud storage manager instance
_cloud_storage_manager: Optional[CloudStorageManager] = None


def get_cloud_storage_manager() -> CloudStorageManager:
    """Get or create the global cloud storage manager instance."""
    global _cloud_storage_manager
    if _cloud_storage_manager is None:
        _cloud_storage_manager = CloudStorageManager()
    return _cloud_storage_manager

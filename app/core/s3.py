"""
AWS S3 Client for Data Lake Operations.

This module provides async S3 operations for the Echo Analytics Platform data lake.
Supports file upload, download, listing, and presigned URL generation.
"""

import io
from datetime import datetime
from typing import BinaryIO, Optional

import boto3
import pandas as pd
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import get_settings

settings = get_settings()


class S3Client:
    """AWS S3 client wrapper for data lake operations."""

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """
        Initialize S3 client.

        Args:
            bucket_name: S3 bucket name (defaults to settings)
            region: AWS region (defaults to settings)
        """
        self.bucket_name = bucket_name or settings.S3_BUCKET_NAME
        self.region = region or settings.AWS_REGION

        # Configure boto3 client
        config = Config(
            region_name=self.region,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            region_name=self.region,
            config=config,
        )

        self._resource = boto3.resource(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
            region_name=self.region,
        )

    def upload_file(
        self,
        file_content: bytes | BinaryIO,
        key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Upload file to S3.

        Args:
            file_content: File content as bytes or file-like object
            key: S3 object key (path)
            content_type: MIME type of the file

        Returns:
            S3 URI of the uploaded file
        """
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        if isinstance(file_content, bytes):
            file_obj = io.BytesIO(file_content)
        else:
            file_obj = file_content

        self._client.upload_fileobj(
            file_obj,
            self.bucket_name,
            key,
            ExtraArgs=extra_args if extra_args else None,
        )

        return f"s3://{self.bucket_name}/{key}"

    def upload_dataframe(
        self,
        df: pd.DataFrame,
        key: str,
        file_format: str = "parquet",
    ) -> str:
        """
        Upload pandas DataFrame to S3.

        Args:
            df: DataFrame to upload
            key: S3 object key (path)
            file_format: Output format ('parquet', 'csv', 'json')

        Returns:
            S3 URI of the uploaded file
        """
        buffer = io.BytesIO()

        if file_format == "parquet":
            df.to_parquet(buffer, index=False, engine="pyarrow")
            content_type = "application/octet-stream"
        elif file_format == "csv":
            df.to_csv(buffer, index=False)
            content_type = "text/csv"
        elif file_format == "json":
            df.to_json(buffer, orient="records", lines=True)
            content_type = "application/json"
        else:
            raise ValueError(f"Unsupported format: {file_format}")

        buffer.seek(0)
        return self.upload_file(buffer, key, content_type)

    def download_file(self, key: str) -> bytes:
        """
        Download file from S3.

        Args:
            key: S3 object key

        Returns:
            File content as bytes
        """
        buffer = io.BytesIO()
        self._client.download_fileobj(self.bucket_name, key, buffer)
        buffer.seek(0)
        return buffer.read()

    def download_dataframe(
        self,
        key: str,
        file_format: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Download file from S3 as pandas DataFrame.

        Args:
            key: S3 object key
            file_format: File format (auto-detected from extension if None)

        Returns:
            pandas DataFrame
        """
        if file_format is None:
            if key.endswith(".parquet"):
                file_format = "parquet"
            elif key.endswith(".csv"):
                file_format = "csv"
            elif key.endswith(".json") or key.endswith(".jsonl"):
                file_format = "json"
            else:
                raise ValueError(f"Cannot auto-detect format for: {key}")

        content = self.download_file(key)
        buffer = io.BytesIO(content)

        if file_format == "parquet":
            return pd.read_parquet(buffer)
        elif file_format == "csv":
            return pd.read_csv(buffer)
        elif file_format == "json":
            return pd.read_json(buffer, orient="records", lines=True)
        else:
            raise ValueError(f"Unsupported format: {file_format}")

    def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[dict]:
        """
        List files in S3 bucket with prefix.

        Args:
            prefix: S3 prefix to filter objects
            max_keys: Maximum number of keys to return

        Returns:
            List of file metadata dicts
        """
        paginator = self._client.get_paginator("list_objects_v2")
        files = []

        for page in paginator.paginate(
            Bucket=self.bucket_name,
            Prefix=prefix,
            PaginationConfig={"MaxItems": max_keys},
        ):
            for obj in page.get("Contents", []):
                files.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                    "etag": obj["ETag"],
                })

        return files

    def delete_file(self, key: str) -> bool:
        """
        Delete file from S3.

        Args:
            key: S3 object key

        Returns:
            True if deleted successfully
        """
        try:
            self._client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    def move_file(self, source_key: str, dest_key: str) -> str:
        """
        Move file within S3 bucket (copy + delete).

        Args:
            source_key: Source object key
            dest_key: Destination object key

        Returns:
            S3 URI of the new location
        """
        copy_source = {"Bucket": self.bucket_name, "Key": source_key}
        self._client.copy_object(
            CopySource=copy_source,
            Bucket=self.bucket_name,
            Key=dest_key,
        )
        self.delete_file(source_key)
        return f"s3://{self.bucket_name}/{dest_key}"

    def get_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        operation: str = "get_object",
    ) -> str:
        """
        Generate presigned URL for S3 object.

        Args:
            key: S3 object key
            expiration: URL expiration in seconds
            operation: S3 operation ('get_object' or 'put_object')

        Returns:
            Presigned URL
        """
        return self._client.generate_presigned_url(
            operation,
            Params={"Bucket": self.bucket_name, "Key": key},
            ExpiresIn=expiration,
        )

    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            key: S3 object key

        Returns:
            True if file exists
        """
        try:
            self._client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False


# Convenience functions for data lake paths
def get_raw_path(data_type: str, filename: str) -> str:
    """Get S3 key for raw data."""
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    return f"{settings.S3_RAW_PREFIX}{data_type}/{date_prefix}/{filename}"


def get_staging_path(data_type: str, filename: str) -> str:
    """Get S3 key for staging data."""
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    return f"{settings.S3_STAGING_PREFIX}{data_type}/{date_prefix}/{filename}"


def get_archive_path(data_type: str, filename: str) -> str:
    """Get S3 key for archived data."""
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
    return f"{settings.S3_ARCHIVE_PREFIX}{data_type}/{date_prefix}/{filename}"


# Singleton instance
_s3_client: Optional[S3Client] = None


def get_s3_client() -> S3Client:
    """Get or create S3 client singleton."""
    global _s3_client
    if _s3_client is None:
        _s3_client = S3Client()
    return _s3_client

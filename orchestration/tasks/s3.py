"""
S3 Prefect Tasks for Data Lake Operations.

This module provides Prefect tasks for interacting with AWS S3,
enabling data lake workflows in the Echo Analytics Platform.
"""

from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from prefect import task
from prefect.logging import get_run_logger

from app.config import get_settings
from app.core.s3 import S3Client, get_archive_path, get_raw_path, get_staging_path

settings = get_settings()


@task(retries=3, retry_delay_seconds=30)
def upload_to_s3(
    df: pd.DataFrame,
    data_type: str,
    filename: Optional[str] = None,
    file_format: str = "parquet",
    prefix: str = "raw",
) -> dict:
    """
    Upload DataFrame to S3 data lake.

    Args:
        df: DataFrame to upload
        data_type: Type of data (e.g., 'revenue', 'customers')
        filename: Custom filename (auto-generated if None)
        file_format: Output format ('parquet', 'csv', 'json')
        prefix: S3 prefix ('raw', 'staging', 'archive')

    Returns:
        Dict with upload details
    """
    logger = get_run_logger()
    s3 = S3Client()

    if filename is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{data_type}_{timestamp}.{file_format}"

    if prefix == "raw":
        key = get_raw_path(data_type, filename)
    elif prefix == "staging":
        key = get_staging_path(data_type, filename)
    elif prefix == "archive":
        key = get_archive_path(data_type, filename)
    else:
        key = f"{prefix}/{data_type}/{filename}"

    s3_uri = s3.upload_dataframe(df, key, file_format)

    logger.info(f"Uploaded {len(df)} rows to {s3_uri}")

    return {
        "s3_uri": s3_uri,
        "key": key,
        "rows": len(df),
        "format": file_format,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }


@task(retries=3, retry_delay_seconds=30)
def download_from_s3(
    key: str,
    bucket: Optional[str] = None,
    file_format: Optional[str] = None,
) -> pd.DataFrame:
    """
    Download file from S3 as DataFrame.

    Args:
        key: S3 object key
        bucket: S3 bucket (defaults to settings)
        file_format: File format (auto-detected if None)

    Returns:
        pandas DataFrame
    """
    logger = get_run_logger()
    s3 = S3Client(bucket_name=bucket) if bucket else S3Client()

    df = s3.download_dataframe(key, file_format)

    logger.info(f"Downloaded {len(df)} rows from s3://{s3.bucket_name}/{key}")

    return df


@task(retries=2, retry_delay_seconds=10)
def list_s3_files(
    prefix: str,
    bucket: Optional[str] = None,
    max_keys: int = 1000,
) -> list[dict]:
    """
    List files in S3 with given prefix.

    Args:
        prefix: S3 prefix to filter
        bucket: S3 bucket (defaults to settings)
        max_keys: Maximum files to return

    Returns:
        List of file metadata dicts
    """
    logger = get_run_logger()
    s3 = S3Client(bucket_name=bucket) if bucket else S3Client()

    files = s3.list_files(prefix, max_keys)

    logger.info(f"Found {len(files)} files with prefix '{prefix}'")

    return files


@task(retries=2, retry_delay_seconds=10)
def archive_file(
    source_key: str,
    data_type: str,
    bucket: Optional[str] = None,
) -> dict:
    """
    Move file from raw/staging to archive.

    Args:
        source_key: Source S3 key
        data_type: Type of data for archive path
        bucket: S3 bucket (defaults to settings)

    Returns:
        Dict with archive details
    """
    logger = get_run_logger()
    s3 = S3Client(bucket_name=bucket) if bucket else S3Client()

    filename = source_key.split("/")[-1]
    archive_key = get_archive_path(data_type, filename)

    new_uri = s3.move_file(source_key, archive_key)

    logger.info(f"Archived {source_key} to {archive_key}")

    return {
        "source_key": source_key,
        "archive_key": archive_key,
        "s3_uri": new_uri,
        "archived_at": datetime.now(timezone.utc).isoformat(),
    }


@task(retries=2, retry_delay_seconds=10)
def delete_s3_file(
    key: str,
    bucket: Optional[str] = None,
) -> dict:
    """
    Delete file from S3.

    Args:
        key: S3 object key
        bucket: S3 bucket (defaults to settings)

    Returns:
        Dict with deletion status
    """
    logger = get_run_logger()
    s3 = S3Client(bucket_name=bucket) if bucket else S3Client()

    success = s3.delete_file(key)

    if success:
        logger.info(f"Deleted {key}")
    else:
        logger.warning(f"Failed to delete {key}")

    return {
        "key": key,
        "deleted": success,
        "deleted_at": datetime.now(timezone.utc).isoformat() if success else None,
    }


@task
def get_presigned_upload_url(
    data_type: str,
    filename: str,
    expiration: int = 3600,
) -> dict:
    """
    Generate presigned URL for direct upload to S3.

    Args:
        data_type: Type of data for path
        filename: Target filename
        expiration: URL expiration in seconds

    Returns:
        Dict with presigned URL and key
    """
    logger = get_run_logger()
    s3 = S3Client()

    key = get_raw_path(data_type, filename)
    url = s3.get_presigned_url(key, expiration, "put_object")

    logger.info(f"Generated presigned URL for {key}")

    return {
        "url": url,
        "key": key,
        "expires_in": expiration,
    }


@task
def check_file_exists(
    key: str,
    bucket: Optional[str] = None,
) -> bool:
    """
    Check if file exists in S3.

    Args:
        key: S3 object key
        bucket: S3 bucket (defaults to settings)

    Returns:
        True if file exists
    """
    s3 = S3Client(bucket_name=bucket) if bucket else S3Client()
    return s3.file_exists(key)

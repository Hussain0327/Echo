"""
S3 to Redshift Pipeline Flow.

This flow orchestrates the complete data pipeline from S3 data lake
to Redshift data warehouse with validation, transformation, and archival.
"""

from datetime import datetime, timezone
from typing import Optional

from prefect import flow, get_run_logger

from app.config import get_settings
from orchestration.notifications import notify_on_failure
from orchestration.tasks.transform import run_dbt
from orchestration.tasks.load import copy_s3_to_redshift, test_redshift_connection
from orchestration.tasks.s3 import archive_file, download_from_s3, list_s3_files
from orchestration.tasks.validate import run_expectations

settings = get_settings()


@flow(
    name="s3_to_redshift_pipeline",
    description="Load data from S3 data lake to Redshift warehouse",
    retries=2,
    retry_delay_seconds=120,
    timeout_seconds=3600,
    on_failure=[notify_on_failure],
)
def s3_to_redshift_pipeline(
    s3_prefix: str,
    data_type: str,
    target_table: str,
    target_schema: str = "staging",
    file_format: str = "PARQUET",
    run_dbt_models: bool = True,
    archive_after_load: bool = True,
    validate_data: bool = True,
    iam_role: Optional[str] = None,
    bucket: Optional[str] = None,
) -> dict:
    """
    Complete S3 to Redshift data pipeline.

    Pipeline steps:
    1. Test Redshift connectivity
    2. List new files in S3 prefix
    3. For each file:
       a. Download and validate (optional)
       b. COPY from S3 to Redshift staging
       c. Archive processed file (optional)
    4. Run dbt transformations (optional)

    Args:
        s3_prefix: S3 prefix to scan for files (e.g., 'raw/revenue/')
        data_type: Type of data for validation suite selection
        target_table: Redshift target table name
        target_schema: Redshift target schema
        file_format: Data format (PARQUET, CSV, JSON)
        run_dbt_models: Whether to run dbt after loading
        archive_after_load: Whether to move files to archive
        validate_data: Whether to validate data before loading
        iam_role: IAM role ARN for COPY (uses creds if None)
        bucket: S3 bucket (defaults to settings)

    Returns:
        Dict with pipeline execution summary
    """
    logger = get_run_logger()
    bucket = bucket or settings.S3_BUCKET_NAME

    logger.info(f"Starting S3 to Redshift pipeline for {data_type}")
    logger.info(f"Source: s3://{bucket}/{s3_prefix}")
    logger.info(f"Target: {target_schema}.{target_table}")

    # Track pipeline results
    results = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_type": data_type,
        "s3_prefix": s3_prefix,
        "target_table": f"{target_schema}.{target_table}",
        "files_processed": 0,
        "files_failed": 0,
        "total_rows": 0,
        "validation_passed": True,
        "dbt_run": False,
        "errors": [],
    }

    # Step 1: Test Redshift connection
    logger.info("Testing Redshift connection...")
    conn_result = test_redshift_connection()
    if not conn_result.get("success"):
        error = f"Redshift connection failed: {conn_result.get('error')}"
        logger.error(error)
        results["errors"].append(error)
        results["success"] = False
        return results

    logger.info(f"Connected to Redshift: {conn_result.get('database')}")

    # Step 2: List files in S3
    logger.info(f"Scanning S3 prefix: {s3_prefix}")
    files = list_s3_files(prefix=s3_prefix, bucket=bucket)

    if not files:
        logger.warning(f"No files found in s3://{bucket}/{s3_prefix}")
        results["success"] = True
        results["message"] = "No new files to process"
        return results

    logger.info(f"Found {len(files)} files to process")

    # Step 3: Process each file
    for file_info in files:
        file_key = file_info["key"]
        logger.info(f"Processing: {file_key}")

        try:
            # Step 3a: Validate data (optional)
            if validate_data:
                logger.info(f"Validating {file_key}...")
                df = download_from_s3(key=file_key, bucket=bucket)

                # Run Great Expectations validation
                validation = run_expectations(
                    df=df,
                    expectation_suite=f"{data_type}_data_suite",
                )

                if not validation.get("success", False):
                    logger.warning(f"Validation failed for {file_key}")
                    results["validation_passed"] = False
                    results["files_failed"] += 1
                    results["errors"].append({
                        "file": file_key,
                        "error": "Validation failed",
                        "details": validation.get("results", [])[:5],
                    })
                    continue

                results["total_rows"] += len(df)
                logger.info(f"Validation passed: {len(df)} rows")

            # Step 3b: COPY from S3 to Redshift
            s3_path = f"s3://{bucket}/{file_key}"
            logger.info(f"Loading {s3_path} to Redshift...")

            copy_result = copy_s3_to_redshift(
                s3_path=s3_path,
                table_name=target_table,
                schema=target_schema,
                iam_role=iam_role,
                file_format=file_format,
            )

            if not copy_result.get("success"):
                error = copy_result.get("error", "Unknown error")
                logger.error(f"COPY failed for {file_key}: {error}")
                results["files_failed"] += 1
                results["errors"].append({
                    "file": file_key,
                    "error": error,
                })
                continue

            results["files_processed"] += 1
            logger.info(f"Loaded {file_key} successfully")

            # Step 3c: Archive processed file (optional)
            if archive_after_load:
                logger.info(f"Archiving {file_key}...")
                archive_result = archive_file(
                    source_key=file_key,
                    data_type=data_type,
                    bucket=bucket,
                )
                logger.info(f"Archived to: {archive_result.get('archive_key')}")

        except Exception as e:
            logger.error(f"Error processing {file_key}: {str(e)}")
            results["files_failed"] += 1
            results["errors"].append({
                "file": file_key,
                "error": str(e),
            })

    # Step 4: Run dbt transformations (optional)
    if run_dbt_models and results["files_processed"] > 0:
        logger.info("Running dbt transformations...")
        try:
            dbt_result = run_dbt(
                command="run",
                target="redshift",
                select=f"staging.stg_{data_type}+",
            )
            results["dbt_run"] = True
            results["dbt_result"] = dbt_result
            logger.info("dbt run completed successfully")
        except Exception as e:
            logger.error(f"dbt run failed: {str(e)}")
            results["errors"].append({"dbt": str(e)})

    # Finalize results
    results["completed_at"] = datetime.now(timezone.utc).isoformat()
    results["success"] = results["files_failed"] == 0 and len(results["errors"]) == 0

    logger.info(f"Pipeline completed: {results['files_processed']} files processed, "
                f"{results['files_failed']} failed")

    return results


@flow(
    name="bulk_s3_to_redshift",
    description="Process multiple data types from S3 to Redshift",
    retries=1,
    timeout_seconds=7200,
    on_failure=[notify_on_failure],
)
def bulk_s3_to_redshift(
    data_types: list[str],
    run_dbt_models: bool = True,
    iam_role: Optional[str] = None,
) -> dict:
    """
    Process multiple data types from S3 to Redshift.

    Args:
        data_types: List of data types to process (e.g., ['revenue', 'customers'])
        run_dbt_models: Whether to run dbt after all loads
        iam_role: IAM role ARN for COPY

    Returns:
        Dict with summary of all pipeline runs
    """
    logger = get_run_logger()
    logger.info(f"Starting bulk S3 to Redshift for: {data_types}")

    results = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "data_types": data_types,
        "pipelines": {},
        "success": True,
    }

    # Process each data type
    for data_type in data_types:
        logger.info(f"Processing data type: {data_type}")

        pipeline_result = s3_to_redshift_pipeline(
            s3_prefix=f"{settings.S3_RAW_PREFIX}{data_type}/",
            data_type=data_type,
            target_table=f"stg_{data_type}",
            target_schema="staging",
            run_dbt_models=False,  # Run dbt once at end
            iam_role=iam_role,
        )

        results["pipelines"][data_type] = pipeline_result
        if not pipeline_result.get("success"):
            results["success"] = False

    # Run dbt once for all data types
    if run_dbt_models:
        logger.info("Running dbt for all loaded data...")
        try:
            dbt_result = run_dbt(
                command="run",
                target="redshift",
            )
            results["dbt_result"] = dbt_result
        except Exception as e:
            logger.error(f"dbt run failed: {str(e)}")
            results["dbt_error"] = str(e)
            results["success"] = False

    results["completed_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(f"Bulk pipeline completed. Success: {results['success']}")

    return results


@flow(
    name="scheduled_s3_redshift_sync",
    description="Scheduled sync from S3 to Redshift",
)
def scheduled_s3_redshift_sync() -> dict:
    """
    Scheduled job to sync all data types from S3 to Redshift.

    This flow is designed to run on a schedule (e.g., hourly, daily).
    """
    return bulk_s3_to_redshift(
        data_types=["revenue", "customers", "products", "marketing"],
        run_dbt_models=True,
    )

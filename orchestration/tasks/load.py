from datetime import datetime
from typing import Optional

import pandas as pd
from prefect import task
from prefect.logging import get_run_logger


@task(retries=2, retry_delay_seconds=10)
def load_to_staging(
    df: pd.DataFrame, table_name: str, connection_string: str, if_exists: str = "replace"
) -> dict:
    logger = get_run_logger()
    from sqlalchemy import create_engine

    staging_table = f"stg_{table_name}"

    engine = create_engine(connection_string)

    df["_loaded_at"] = datetime.utcnow()
    df["_source_rows"] = len(df)

    df.to_sql(
        staging_table, engine, if_exists=if_exists, index=False, method="multi", chunksize=1000
    )

    logger.info(f"Loaded {len(df)} rows to {staging_table}")

    return {
        "table": staging_table,
        "rows": len(df),
        "columns": len(df.columns),
        "loaded_at": datetime.utcnow().isoformat(),
    }


@task(retries=2, retry_delay_seconds=10)
def load_to_warehouse(
    df: pd.DataFrame,
    table_name: str,
    connection_string: str,
    if_exists: str = "append",
    schema: Optional[str] = None,
) -> dict:
    logger = get_run_logger()
    from sqlalchemy import create_engine

    engine = create_engine(connection_string)

    df.to_sql(
        table_name,
        engine,
        schema=schema,
        if_exists=if_exists,
        index=False,
        method="multi",
        chunksize=1000,
    )

    logger.info(
        f"Loaded {len(df)} rows to {schema}.{table_name}"
        if schema
        else f"Loaded {len(df)} rows to {table_name}"
    )

    return {
        "table": table_name,
        "schema": schema,
        "rows": len(df),
        "loaded_at": datetime.utcnow().isoformat(),
    }


@task
def load_to_parquet(
    df: pd.DataFrame, file_path: str, partition_cols: Optional[list[str]] = None
) -> dict:
    logger = get_run_logger()

    df.to_parquet(file_path, partition_cols=partition_cols, index=False)

    logger.info(f"Saved {len(df)} rows to {file_path}")

    return {
        "path": file_path,
        "rows": len(df),
        "partitions": partition_cols,
    }


@task
def upsert_to_table(
    df: pd.DataFrame, table_name: str, connection_string: str, key_columns: list[str]
) -> dict:
    logger = get_run_logger()
    from sqlalchemy import create_engine, text

    engine = create_engine(connection_string)

    temp_table = f"temp_{table_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    df.to_sql(temp_table, engine, if_exists="replace", index=False)

    key_match = " AND ".join([f"t.{col} = s.{col}" for col in key_columns])
    non_key_cols = [col for col in df.columns if col not in key_columns]
    update_set = ", ".join([f"{col} = s.{col}" for col in non_key_cols])
    all_cols = ", ".join(df.columns)
    source_cols = ", ".join([f"s.{col}" for col in df.columns])

    merge_sql = f"""
    MERGE INTO {table_name} t
    USING {temp_table} s
    ON {key_match}
    WHEN MATCHED THEN UPDATE SET {update_set}
    WHEN NOT MATCHED THEN INSERT ({all_cols}) VALUES ({source_cols})
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(merge_sql))
            conn.execute(text(f"DROP TABLE {temp_table}"))
            conn.commit()
    except Exception:
        logger.warning("MERGE not supported, falling back to delete-insert")
        with engine.connect() as conn:
            for _, row in df.iterrows():
                key_filter = " AND ".join([f"{col} = '{row[col]}'" for col in key_columns])
                conn.execute(text(f"DELETE FROM {table_name} WHERE {key_filter}"))
            conn.commit()
        df.to_sql(table_name, engine, if_exists="append", index=False)

    logger.info(f"Upserted {len(df)} rows to {table_name}")

    return {
        "table": table_name,
        "rows": len(df),
        "key_columns": key_columns,
    }


# =============================================================================
# AWS Redshift Tasks
# =============================================================================


@task(retries=2, retry_delay_seconds=30)
def load_to_redshift(
    df: pd.DataFrame,
    table_name: str,
    schema: str = "staging",
    if_exists: str = "append",
) -> dict:
    """
    Load DataFrame directly to Redshift.

    For large datasets (>100k rows), use copy_s3_to_redshift for better performance.

    Args:
        df: DataFrame to load
        table_name: Target table name
        schema: Target schema
        if_exists: How to handle existing table ('fail', 'replace', 'append')

    Returns:
        Dict with load statistics
    """
    logger = get_run_logger()
    from app.core.redshift import load_dataframe

    df["_loaded_at"] = datetime.utcnow()

    result = load_dataframe(df, table_name, schema, if_exists)

    if result["success"]:
        logger.info(f"Loaded {len(df)} rows to Redshift {schema}.{table_name}")
    else:
        logger.error(f"Failed to load to Redshift: {result.get('error')}")

    return result


@task(retries=3, retry_delay_seconds=60)
def copy_s3_to_redshift(
    s3_path: str,
    table_name: str,
    schema: str = "staging",
    iam_role: Optional[str] = None,
    file_format: str = "PARQUET",
) -> dict:
    """
    Load data from S3 to Redshift using COPY command.

    This is the recommended method for large datasets as it:
    - Uses parallel loading across Redshift nodes
    - Bypasses the leader node bottleneck
    - Handles compression automatically

    Args:
        s3_path: Full S3 path (s3://bucket/key or s3://bucket/prefix/)
        table_name: Target table name
        schema: Target schema
        iam_role: IAM role ARN (uses credentials if None)
        file_format: Data format (PARQUET, CSV, JSON)

    Returns:
        Dict with copy statistics
    """
    logger = get_run_logger()
    from app.core.redshift import copy_from_s3

    result = copy_from_s3(
        s3_path=s3_path,
        table_name=table_name,
        schema=schema,
        iam_role=iam_role,
        file_format=file_format,
    )

    if result["success"]:
        logger.info(f"COPY from {s3_path} to Redshift {schema}.{table_name} completed")
        if result.get("errors"):
            logger.warning(f"COPY had {len(result['errors'])} errors")
    else:
        logger.error(f"COPY failed: {result.get('error')}")

    return result


@task(retries=2, retry_delay_seconds=30)
def unload_redshift_to_s3(
    query: str,
    s3_path: str,
    iam_role: Optional[str] = None,
    file_format: str = "PARQUET",
) -> dict:
    """
    Export data from Redshift to S3 using UNLOAD.

    Args:
        query: SELECT query to export
        s3_path: S3 destination path
        iam_role: IAM role ARN
        file_format: Output format (PARQUET, CSV)

    Returns:
        Dict with unload statistics
    """
    logger = get_run_logger()
    from app.core.redshift import unload_to_s3

    result = unload_to_s3(
        query=query,
        s3_path=s3_path,
        iam_role=iam_role,
        file_format=file_format,
    )

    if result["success"]:
        logger.info(f"UNLOAD to {s3_path} completed")
    else:
        logger.error(f"UNLOAD failed: {result.get('error')}")

    return result


@task
def test_redshift_connection() -> dict:
    """
    Test Redshift connection.

    Returns:
        Dict with connection status
    """
    logger = get_run_logger()
    from app.core.redshift import test_connection

    result = test_connection()

    if result["success"]:
        logger.info(f"Connected to Redshift as {result['user']}@{result['database']}")
    else:
        logger.error(f"Redshift connection failed: {result.get('error')}")

    return result

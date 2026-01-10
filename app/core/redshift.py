"""
AWS Redshift Database Connection.

This module provides Redshift connection management for the Echo Analytics Platform.
Supports both SQLAlchemy ORM operations and raw COPY commands from S3.
"""

from contextlib import contextmanager
from typing import Any, Generator, Optional

import pandas as pd
import redshift_connector
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()


def get_redshift_url() -> str:
    """Build Redshift connection URL for SQLAlchemy."""
    return (
        f"redshift+redshift_connector://"
        f"{settings.REDSHIFT_USER}:{settings.REDSHIFT_PASSWORD}"
        f"@{settings.REDSHIFT_HOST}:{settings.REDSHIFT_PORT}"
        f"/{settings.REDSHIFT_DATABASE}"
    )


# SQLAlchemy engine (lazy initialization)
_engine: Optional[Engine] = None


def get_redshift_engine() -> Engine:
    """
    Get or create SQLAlchemy engine for Redshift.

    Returns:
        SQLAlchemy Engine instance
    """
    global _engine

    if _engine is None:
        _engine = create_engine(
            get_redshift_url(),
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=settings.DEBUG,
        )

    return _engine


def get_redshift_session() -> sessionmaker:
    """Get SQLAlchemy session factory for Redshift."""
    engine = get_redshift_engine()
    return sessionmaker(bind=engine)


@contextmanager
def redshift_session() -> Generator[Session, None, None]:
    """
    Context manager for Redshift session.

    Usage:
        with redshift_session() as session:
            result = session.execute(text("SELECT 1"))
    """
    session_factory = get_redshift_session()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_raw_connection() -> redshift_connector.Connection:
    """
    Get raw Redshift connection for COPY commands.

    Returns:
        redshift_connector Connection instance
    """
    return redshift_connector.connect(
        host=settings.REDSHIFT_HOST,
        port=settings.REDSHIFT_PORT,
        database=settings.REDSHIFT_DATABASE,
        user=settings.REDSHIFT_USER,
        password=settings.REDSHIFT_PASSWORD,
    )


def copy_from_s3(
    s3_path: str,
    table_name: str,
    schema: str = "staging",
    iam_role: Optional[str] = None,
    file_format: str = "PARQUET",
    options: Optional[dict] = None,
) -> dict:
    """
    Execute COPY command to load data from S3 to Redshift.

    Args:
        s3_path: Full S3 path (s3://bucket/key)
        table_name: Target table name
        schema: Target schema
        iam_role: IAM role ARN for S3 access (uses creds if None)
        file_format: Data format (PARQUET, CSV, JSON)
        options: Additional COPY options

    Returns:
        Dict with load statistics
    """
    conn = get_raw_connection()
    cursor = conn.cursor()

    try:
        # Build COPY command
        full_table = f"{schema}.{table_name}"

        if iam_role:
            auth_clause = f"IAM_ROLE '{iam_role}'"
        else:
            auth_clause = (
                f"ACCESS_KEY_ID '{settings.AWS_ACCESS_KEY_ID}' "
                f"SECRET_ACCESS_KEY '{settings.AWS_SECRET_ACCESS_KEY}'"
            )

        # Format-specific options
        format_options = ""
        if file_format == "PARQUET":
            format_options = "FORMAT AS PARQUET"
        elif file_format == "CSV":
            format_options = "FORMAT AS CSV IGNOREHEADER 1 DELIMITER ','"
        elif file_format == "JSON":
            format_options = "FORMAT AS JSON 'auto'"

        # Additional options
        extra_options = ""
        if options:
            extra_options = " ".join(f"{k} {v}" for k, v in options.items())

        copy_sql = f"""
            COPY {full_table}
            FROM '{s3_path}'
            {auth_clause}
            {format_options}
            {extra_options}
            STATUPDATE ON
            COMPUPDATE ON
        """

        cursor.execute(copy_sql)
        conn.commit()

        # Get load statistics
        cursor.execute("""
            SELECT query, filename, line_number, colname, err_code, err_reason
            FROM stl_load_errors
            ORDER BY starttime DESC
            LIMIT 10
        """)
        errors = cursor.fetchall()

        return {
            "success": True,
            "table": full_table,
            "s3_path": s3_path,
            "format": file_format,
            "errors": errors if errors else [],
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "error": str(e),
            "table": f"{schema}.{table_name}",
            "s3_path": s3_path,
        }
    finally:
        cursor.close()
        conn.close()


def unload_to_s3(
    query: str,
    s3_path: str,
    iam_role: Optional[str] = None,
    file_format: str = "PARQUET",
    options: Optional[dict] = None,
) -> dict:
    """
    Execute UNLOAD command to export data from Redshift to S3.

    Args:
        query: SELECT query to export
        s3_path: S3 destination path
        iam_role: IAM role ARN for S3 access
        file_format: Output format (PARQUET, CSV)
        options: Additional UNLOAD options

    Returns:
        Dict with unload statistics
    """
    conn = get_raw_connection()
    cursor = conn.cursor()

    try:
        if iam_role:
            auth_clause = f"IAM_ROLE '{iam_role}'"
        else:
            auth_clause = (
                f"ACCESS_KEY_ID '{settings.AWS_ACCESS_KEY_ID}' "
                f"SECRET_ACCESS_KEY '{settings.AWS_SECRET_ACCESS_KEY}'"
            )

        format_options = ""
        if file_format == "PARQUET":
            format_options = "FORMAT AS PARQUET"
        elif file_format == "CSV":
            format_options = "FORMAT AS CSV HEADER DELIMITER ','"

        extra_options = "PARALLEL ON ALLOWOVERWRITE"
        if options:
            extra_options += " " + " ".join(f"{k} {v}" for k, v in options.items())

        unload_sql = f"""
            UNLOAD ('{query.replace("'", "''")}')
            TO '{s3_path}'
            {auth_clause}
            {format_options}
            {extra_options}
        """

        cursor.execute(unload_sql)
        conn.commit()

        return {
            "success": True,
            "query": query[:100] + "..." if len(query) > 100 else query,
            "s3_path": s3_path,
            "format": file_format,
        }

    except Exception as e:
        conn.rollback()
        return {
            "success": False,
            "error": str(e),
            "s3_path": s3_path,
        }
    finally:
        cursor.close()
        conn.close()


def execute_query(query: str, params: Optional[dict] = None) -> list[dict]:
    """
    Execute query and return results as list of dicts.

    Args:
        query: SQL query
        params: Query parameters

    Returns:
        List of result rows as dicts
    """
    with redshift_session() as session:
        result = session.execute(text(query), params or {})
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]


def load_dataframe(
    df: pd.DataFrame,
    table_name: str,
    schema: str = "staging",
    if_exists: str = "append",
) -> dict:
    """
    Load pandas DataFrame directly to Redshift.

    Note: For large datasets, use copy_from_s3 for better performance.

    Args:
        df: DataFrame to load
        table_name: Target table name
        schema: Target schema
        if_exists: How to handle existing table ('fail', 'replace', 'append')

    Returns:
        Dict with load statistics
    """
    engine = get_redshift_engine()

    try:
        rows = df.to_sql(
            name=table_name,
            con=engine,
            schema=schema,
            if_exists=if_exists,
            index=False,
            method="multi",
            chunksize=1000,
        )

        return {
            "success": True,
            "table": f"{schema}.{table_name}",
            "rows_loaded": len(df),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table": f"{schema}.{table_name}",
        }


def test_connection() -> dict:
    """
    Test Redshift connection.

    Returns:
        Dict with connection status
    """
    try:
        with redshift_session() as session:
            result = session.execute(text("SELECT CURRENT_USER, CURRENT_DATABASE()"))
            row = result.fetchone()
            return {
                "success": True,
                "user": row[0],
                "database": row[1],
                "host": settings.REDSHIFT_HOST,
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "host": settings.REDSHIFT_HOST,
        }


def close_redshift() -> None:
    """Close Redshift engine and connections."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None

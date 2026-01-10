from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.database import get_db
from app.models.schemas import DataSourceResponse, UploadResponse
from app.services.ingestion import IngestionService

router = APIRouter()
settings = get_settings()


# S3 Request/Response Models
class S3UploadResponse(BaseModel):
    """Response for S3 upload operations."""

    success: bool
    s3_uri: str
    key: str
    rows: int
    format: str
    uploaded_at: str


class S3PipelineTriggerRequest(BaseModel):
    """Request to trigger S3 to Redshift pipeline."""

    s3_prefix: str
    data_type: str
    target_table: Optional[str] = None
    target_schema: str = "staging"
    file_format: str = "PARQUET"
    run_dbt: bool = True
    archive_after_load: bool = True
    validate_data: bool = True


class S3PipelineResponse(BaseModel):
    """Response for pipeline trigger."""

    success: bool
    message: str
    pipeline_run_id: Optional[str] = None
    details: Optional[dict] = None


@router.post("/upload/csv", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    use_case: Optional[str] = Query(None, description="Use case: 'revenue' or 'marketing'"),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    service = IngestionService(db)
    return await service.ingest_csv(file, use_case=use_case)


@router.post("/upload/excel", response_model=UploadResponse)
async def upload_excel(
    file: UploadFile = File(...),
    use_case: Optional[str] = Query(None, description="Use case: 'revenue' or 'marketing'"),
    db: AsyncSession = Depends(get_db),
):
    valid_extensions = (".xlsx", ".xls")
    if not file.filename.endswith(valid_extensions):
        raise HTTPException(status_code=400, detail="File must be Excel (.xlsx or .xls)")

    service = IngestionService(db)
    return await service.ingest_excel(file, use_case=use_case)


@router.get("/sources", response_model=List[DataSourceResponse])
async def list_sources(limit: int = Query(10, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    service = IngestionService(db)
    return await service.list_sources(limit=limit)


@router.get("/sources/{source_id}", response_model=DataSourceResponse)
async def get_source(source_id: str, db: AsyncSession = Depends(get_db)):
    service = IngestionService(db)
    source = await service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


# =============================================================================
# AWS S3 Endpoints
# =============================================================================


@router.post("/upload/s3", response_model=S3UploadResponse)
async def upload_to_s3(
    file: UploadFile = File(...),
    data_type: str = Query(..., description="Data type (e.g., 'revenue', 'customers')"),
    file_format: str = Query("parquet", description="Output format: parquet, csv, json"),
    prefix: str = Query("raw", description="S3 prefix: raw, staging, archive"),
):
    """
    Upload file directly to S3 data lake.

    The file is converted to the specified format and stored in the
    appropriate S3 prefix based on the data lake structure.
    """
    import pandas as pd

    from app.core.s3 import S3Client, get_raw_path, get_staging_path

    # Validate file type
    valid_extensions = (".csv", ".xlsx", ".xls", ".json", ".parquet")
    if not file.filename.endswith(valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"File must be one of: {', '.join(valid_extensions)}",
        )

    # Read file content
    content = await file.read()

    try:
        # Parse file based on extension
        import io

        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        elif file.filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(content))
        elif file.filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(content))
        elif file.filename.endswith(".parquet"):
            df = pd.read_parquet(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")

    # Generate S3 key
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{data_type}_{timestamp}.{file_format}"

    if prefix == "raw":
        key = get_raw_path(data_type, filename)
    elif prefix == "staging":
        key = get_staging_path(data_type, filename)
    else:
        key = f"{prefix}/{data_type}/{filename}"

    # Upload to S3
    s3 = S3Client()
    s3_uri = s3.upload_dataframe(df, key, file_format)

    return S3UploadResponse(
        success=True,
        s3_uri=s3_uri,
        key=key,
        rows=len(df),
        format=file_format,
        uploaded_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/s3/files")
async def list_s3_files(
    prefix: str = Query("raw/", description="S3 prefix to list"),
    max_keys: int = Query(100, ge=1, le=1000, description="Maximum files to return"),
):
    """
    List files in S3 data lake.

    Returns metadata for files matching the given prefix.
    """
    from app.core.s3 import S3Client

    s3 = S3Client()
    files = s3.list_files(prefix, max_keys)

    return {
        "prefix": prefix,
        "count": len(files),
        "files": files,
    }


@router.get("/s3/presigned-url")
async def get_presigned_upload_url(
    data_type: str = Query(..., description="Data type for file path"),
    filename: str = Query(..., description="Target filename"),
    expiration: int = Query(3600, ge=60, le=86400, description="URL expiration in seconds"),
):
    """
    Generate presigned URL for direct S3 upload.

    Use this for large files that should be uploaded directly to S3
    without going through the API server.
    """
    from app.core.s3 import S3Client, get_raw_path

    s3 = S3Client()
    key = get_raw_path(data_type, filename)
    url = s3.get_presigned_url(key, expiration, "put_object")

    return {
        "upload_url": url,
        "key": key,
        "expires_in": expiration,
        "method": "PUT",
        "headers": {
            "Content-Type": "application/octet-stream",
        },
    }


@router.post("/trigger/s3-pipeline", response_model=S3PipelineResponse)
async def trigger_s3_pipeline(request: S3PipelineTriggerRequest):
    """
    Trigger S3 to Redshift data pipeline.

    This endpoint starts an async Prefect flow that:
    1. Scans S3 for new files
    2. Validates data quality
    3. Loads data to Redshift
    4. Runs dbt transformations
    5. Archives processed files
    """
    if not settings.USE_REDSHIFT:
        raise HTTPException(
            status_code=400,
            detail="Redshift is not enabled. Set USE_REDSHIFT=true in environment.",
        )

    try:
        from orchestration.flows.s3_redshift_pipeline import s3_to_redshift_pipeline

        # Run the pipeline (in production, this would be async/background)
        target_table = request.target_table or f"stg_{request.data_type}"

        result = s3_to_redshift_pipeline(
            s3_prefix=request.s3_prefix,
            data_type=request.data_type,
            target_table=target_table,
            target_schema=request.target_schema,
            file_format=request.file_format,
            run_dbt_models=request.run_dbt,
            archive_after_load=request.archive_after_load,
            validate_data=request.validate_data,
        )

        return S3PipelineResponse(
            success=result.get("success", False),
            message=f"Processed {result.get('files_processed', 0)} files",
            details=result,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}",
        )

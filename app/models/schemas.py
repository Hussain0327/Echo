from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class SourceTypeEnum(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    STRIPE = "stripe"
    HUBSPOT = "hubspot"


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool
    sample_values: List[Any]
    null_count: int
    unique_count: int


class SchemaInfo(BaseModel):
    columns: Dict[str, ColumnInfo]
    total_rows: int
    total_columns: int


class ValidationError(BaseModel):
    severity: str
    field: str
    message: str
    suggestion: str


class UploadResponse(BaseModel):
    id: str
    source_type: SourceTypeEnum
    file_name: str
    status: str
    message: str
    schema_info: Optional[SchemaInfo] = None
    validation_errors: Optional[List[ValidationError]] = None


class DataSourceResponse(BaseModel):
    id: str
    user_id: str
    source_type: SourceTypeEnum
    file_name: Optional[str]
    upload_timestamp: datetime
    validation_status: str
    row_count: Optional[int]
    schema_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

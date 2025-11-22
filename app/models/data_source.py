from sqlalchemy import Column, String, DateTime, JSON, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class SourceType(str, enum.Enum):
    CSV = "csv"
    EXCEL = "excel"
    STRIPE = "stripe"
    HUBSPOT = "hubspot"


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, default="default")
    source_type = Column(SQLEnum(SourceType), nullable=False)
    file_name = Column(String)
    file_size = Column(Integer)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    schema_info = Column(JSON)
    validation_status = Column(String, default="pending")
    validation_errors = Column(JSON)
    row_count = Column(Integer)
    metadata_ = Column("metadata", JSON)

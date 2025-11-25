from pydantic import BaseModel, Field
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


class TaskTypeEnum(str, Enum):
    REPORT_GENERATION = "report_generation"
    CHAT_INTERACTION = "chat_interaction"
    METRIC_CALCULATION = "metric_calculation"
    DATA_UPLOAD = "data_upload"
    GENERAL_ANALYSIS = "general_analysis"


class InteractionTypeEnum(str, Enum):
    REPORT = "report"
    CHAT = "chat"
    METRIC = "metric"


class AccuracyRatingEnum(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIALLY_CORRECT = "partially_correct"
    NOT_RATED = "not_rated"


class StartSessionRequest(BaseModel):
    task_type: TaskTypeEnum
    baseline_time_seconds: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class EndSessionRequest(BaseModel):
    session_id: str


class SessionResponse(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str]
    task_type: TaskTypeEnum
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    time_saved_seconds: Optional[float]

    class Config:
        from_attributes = True


class SubmitFeedbackRequest(BaseModel):
    interaction_type: InteractionTypeEnum
    session_id: Optional[str] = None
    report_id: Optional[str] = None
    usage_metric_id: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    accuracy_rating: Optional[AccuracyRatingEnum] = None
    accuracy_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    interaction_type: InteractionTypeEnum
    rating: Optional[int]
    feedback_text: Optional[str]
    accuracy_rating: AccuracyRatingEnum
    created_at: datetime

    class Config:
        from_attributes = True


class TimeSavingsStats(BaseModel):
    total_sessions: int
    total_time_saved_hours: float
    avg_time_saved_hours: float
    avg_duration_minutes: float
    sessions_by_task_type: Dict[str, int]


class SatisfactionStats(BaseModel):
    total_ratings: int
    avg_rating: float
    rating_distribution: Dict[int, int]
    ratings_by_interaction_type: Dict[str, float]


class AccuracyStats(BaseModel):
    total_ratings: int
    accuracy_rate: float
    accuracy_distribution: Dict[str, int]


class UsageStats(BaseModel):
    total_sessions: int
    total_reports: int
    total_chats: int
    most_used_metrics: List[str]
    sessions_per_day: Dict[str, int]


class AnalyticsOverview(BaseModel):
    time_savings: TimeSavingsStats
    satisfaction: SatisfactionStats
    accuracy: AccuracyStats
    usage: UsageStats


class PortfolioStats(BaseModel):
    total_sessions: int
    total_time_saved_hours: float
    avg_time_saved_hours: float
    avg_satisfaction_rating: float
    accuracy_rate: float
    total_insights_generated: int
    headline_metrics: Dict[str, str]

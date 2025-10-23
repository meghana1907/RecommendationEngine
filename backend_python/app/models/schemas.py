from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    CLUSTERING = "clustering"
    GENERATING_TESTS = "generating_tests"
    COMPLETED = "completed"
    FAILED = "failed"

class TestType(str, Enum):
    STANDARD = "standard"
    RECOMMENDED = "recommended"

class DocumentType(str, Enum):
    BRD = "BRD"
    USER_STORIES = "user_stories"
    REQUIREMENTS = "requirements"
    JIRA_IMPORT = "jira_import"

# Document Models
class DocumentCreate(BaseModel):
    filename: str
    content: str
    content_type: Optional[str] = "text/plain"
    document_type: DocumentType = DocumentType.REQUIREMENTS

class DocumentResponse(BaseModel):
    id: str
    filename: str
    content_type: str
    file_size: int
    document_type: DocumentType
    processing_status: ProcessingStatus
    total_chunks: int = 0
    upload_timestamp: datetime
    created_at: datetime

class DocumentStatusResponse(BaseModel):
    document_id: str
    status: ProcessingStatus
    total_chunks: int
    upload_timestamp: datetime
    progress_percentage: int = 0

# Jira Models
class JiraCredentials(BaseModel):
    base_url: str
    username: str
    api_token: str

class JiraProject(BaseModel):
    key: str
    name: str
    id: str

class JiraUserStory(BaseModel):
    key: str
    summary: str
    description: Optional[str] = ""
    story_points: Optional[int] = None
    priority: Optional[str] = "Medium"
    status: Optional[str] = "To Do"
    assignee: Optional[str] = None

class JiraImportRequest(BaseModel):
    credentials: JiraCredentials
    project_key: str
    jql_query: Optional[str] = None
    include_subtasks: bool = False

class JiraImportResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    imported_stories: int = 0
    message: str

# Test Recommendation Models
class TestRecommendation(BaseModel):
    test_type: TestType
    category: str
    description: str
    priority: str = "medium"
    estimated_effort: Optional[str] = None

class ClusterSummary(BaseModel):
    cluster_id: int
    summary: str
    feature_category: str
    chunk_count: int
    business_value: str
    complexity: str = "medium"
    risk_level: str = "medium"

class TestRecommendationCluster(BaseModel):
    cluster_id: int
    cluster_summary: str
    feature_category: str
    chunk_count: int
    standard_tests: List[str] = []
    recommended_tests: List[str] = []
    test_categories: Dict[str, List[str]] = {}
    last_updated: datetime

class TestRecommendationsResponse(BaseModel):
    document_id: str
    recommendations: List[TestRecommendationCluster]
    total_clusters: int
    aggregated_stats: Dict[str, Any] = {}

# Authentication Models
class UserCreate(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Payment Models
class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class PaymentCreate(BaseModel):
    plan: SubscriptionPlan
    payment_method_id: str
    billing_email: str

class PaymentResponse(BaseModel):
    success: bool
    subscription_id: Optional[str] = None
    client_secret: Optional[str] = None
    message: str

# Upload Models
class UploadResponse(BaseModel):
    success: bool
    document_id: str
    message: str
    status: ProcessingStatus = ProcessingStatus.PROCESSING

# Error Models
class ErrorResponse(BaseModel):
    error: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

# Analytics Models
class ProcessingMetrics(BaseModel):
    total_documents: int
    total_test_recommendations: int
    avg_processing_time: float
    success_rate: float

class UserUsageMetrics(BaseModel):
    user_id: str
    documents_processed: int
    tests_generated: int
    subscription_plan: SubscriptionPlan
    usage_limit_reached: bool = False

# Export Models
class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"
    EXCEL = "excel"

class ExportRequest(BaseModel):
    document_id: str
    format: ExportFormat
    include_clusters: bool = True
    include_categories: bool = True
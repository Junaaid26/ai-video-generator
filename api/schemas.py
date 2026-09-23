from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import VideoStatus, SocialPlatform

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_admin: bool = True
    
    class Config:
        from_attributes = True

class Scene(BaseModel):
    scene_number: int
    duration: Optional[int] = None  # seconds (preferred)
    scene_duration: Optional[str] = None  # legacy e.g. "5s"
    narration: str
    visual_prompt: str = ""
    environment: str = ""
    characters: str = ""
    objects: str = ""
    camera_style: str = ""
    visual_style: str = "realistic"
    visual_description: Optional[str] = None  # legacy alias
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    visual_status: Optional[str] = None  # pending, generating, completed, failed
    is_mock_visual: Optional[bool] = None

class VideoPlan(BaseModel):
    title: str
    short_description: str
    complete_narration: str
    scenes: List[Scene]
    suggested_background_music: str
    caption: str
    hashtags: List[str]

class VideoBase(BaseModel):
    prompt: str

class VideoCreate(VideoBase):
    duration: Optional[str] = "30-60 seconds"
    language: Optional[str] = "English"
    style: Optional[str] = "Standard"
    target_platform: Optional[str] = "TikTok"
    visual_style: Optional[str] = "realistic"  # realistic, cinematic, 3d, illustration, anime, minimal

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    complete_narration: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    scenes: Optional[List[Scene]] = None

class ApprovalAction(BaseModel):
    action: str = "APPROVE"  # "APPROVE" or "REJECT"
    rejection_reason: Optional[str] = None
    comments: Optional[str] = None

class VideoResponse(VideoBase):
    id: int
    title: Optional[str] = None
    duration: Optional[str] = None
    language: Optional[str] = None
    style: Optional[str] = None
    target_platform: Optional[str] = None
    status: VideoStatus
    script: Optional[str] = None
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    plan: Optional[Dict[str, Any]] = None
    original_plan: Optional[Dict[str, Any]] = None
    video_url: Optional[str] = None
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    subtitles_path: Optional[str] = None
    error_message: Optional[str] = None
    generation_stage: Optional[str] = None
    resolution: Optional[str] = "1080x1920"
    visual_style: Optional[str] = "realistic"
    visual_provider: Optional[str] = None
    visual_generation_status: Optional[Dict[str, Any]] = None
    qa_report: Optional[Dict[str, Any]] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class ApprovalResponse(BaseModel):
    id: int
    video_id: int
    reviewer_id: Optional[int] = None
    action: str
    is_approved: bool
    rejection_reason: Optional[str] = None
    comments: Optional[str] = None
    reviewed_at: datetime
    
    class Config:
        from_attributes = True

class GenerationAttemptResponse(BaseModel):
    id: int
    video_id: int
    attempt_number: int
    stage: str
    status: str
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    video_id: int
    approvals: List[ApprovalResponse]
    generation_attempts: List[GenerationAttemptResponse]


class SceneAssetResponse(BaseModel):
    id: int
    video_id: int
    scene_number: int
    image_path: Optional[str] = None
    image_url: Optional[str] = None
    visual_prompt: Optional[str] = None
    status: str
    provider: Optional[str] = None
    is_mock: bool = False
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VisualProviderStatus(BaseModel):
    provider: str
    is_available: bool
    message: str
    model: Optional[str] = None
    requires_gpu: bool = False
    recommended_vram_gb: Optional[int] = None
    recommended_ram_gb: Optional[int] = None


# ---------------------------------------------------------------------- #
# Phase 5: Social Media & Publishing Configuration Schemas
# ---------------------------------------------------------------------- #

class SocialAccountCreateSandbox(BaseModel):
    platform: str
    account_name: Optional[str] = None
    account_handle: Optional[str] = None

class SocialAccountResponse(BaseModel):
    id: int
    platform: str
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    account_handle: Optional[str] = None
    status: str
    is_mock: bool = False
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class YouTubeMetadata(BaseModel):
    title: str
    description: Optional[str] = ""
    privacy: str = "public"
    tags: Optional[List[str]] = None

class InstagramMetadata(BaseModel):
    caption: str
    hashtags: Optional[List[str]] = None
    share_to_feed: bool = True

class TikTokMetadata(BaseModel):
    caption: str
    privacy: str = "PUBLIC_TO_EVERYONE"
    allow_comments: bool = True
    allow_duet: bool = True
    allow_stitch: bool = True

class PlatformSettingCreate(BaseModel):
    platform: str
    account_id: int
    platform_metadata: Dict[str, Any]

class PlatformSettingResponse(BaseModel):
    id: int
    configuration_id: int
    platform: str
    account_id: Optional[int] = None
    account: Optional[SocialAccountResponse] = None
    platform_metadata: Optional[Dict[str, Any]] = None
    is_validated: bool
    validation_errors: Optional[List[str]] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PublishingConfigCreate(BaseModel):
    settings: List[PlatformSettingCreate]

class PublishingConfigResponse(BaseModel):
    id: int
    video_id: int
    status: str
    settings: List[PlatformSettingResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PublishingValidationResult(BaseModel):
    is_valid: bool
    status: str
    video_id: int
    configuration_id: Optional[int] = None
    errors: Dict[str, List[str]] = {}
    message: str


# ---------------------------------------------------------------------- #
# Phase 6: Scheduling & Publishing Schemas
# ---------------------------------------------------------------------- #
class ScheduledPostCreate(BaseModel):
    video_id: int
    platforms: List[str]  # e.g. ["youtube", "instagram"]
    publish_now: bool = False
    schedule_date: Optional[str] = None  # "YYYY-MM-DD" e.g. "2026-09-25"
    schedule_time: Optional[str] = None  # "HH:MM" e.g. "19:00"
    timezone: str = "UTC"  # e.g. "Asia/Karachi"

class ScheduledPostResponse(BaseModel):
    id: int
    video_id: int
    platform: str
    connected_account_id: Optional[int] = None
    scheduled_time: datetime
    timezone: str
    platform_metadata: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    external_post_id: Optional[str] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    video_title: Optional[str] = None
    account_name: Optional[str] = None
    account_handle: Optional[str] = None
    localized_scheduled_time: Optional[str] = None

    class Config:
        from_attributes = True

class ScheduleBatchResponse(BaseModel):
    success: bool
    scheduled_posts: List[ScheduledPostResponse]
    message: str




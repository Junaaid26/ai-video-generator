from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base


class PublicationStatus(str, enum.Enum):
    NOT_SELECTED = "NOT_SELECTED"
    QUEUED = "QUEUED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class VideoStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    QA_PENDING = "QA_PENDING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REJECTED = "REJECTED"
    APPROVED = "APPROVED"
    READY_TO_SCHEDULE = "READY_TO_SCHEDULE"
    SCHEDULED = "SCHEDULED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=True)
    
    videos = relationship("Video", back_populates="owner")
    social_accounts = relationship("SocialAccount", back_populates="user")
    approvals = relationship("Approval", back_populates="reviewer")

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    duration = Column(String, nullable=True)
    language = Column(String, nullable=True)
    style = Column(String, nullable=True)
    target_platform = Column(String, nullable=True)
    
    # Content metadata
    title = Column(String, nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, nullable=True)
    script = Column(Text, nullable=True)
    plan = Column(JSON, nullable=True)
    original_plan = Column(JSON, nullable=True)  # Preserves initial AI generation
    
    # Generated asset paths
    video_url = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    subtitles_path = Column(String, nullable=True)

    # Visual generation
    visual_style = Column(String, default="realistic")
    visual_provider = Column(String, nullable=True)
    visual_generation_status = Column(JSON, nullable=True)
    
    # Lifecycle and QA
    status = Column(Enum(VideoStatus, values_callable=lambda obj: [e.value for e in obj]), default=VideoStatus.DRAFT)
    generation_stage = Column(String, default="NOT_STARTED")
    resolution = Column(String, default="1080x1920")
    qa_report = Column(JSON, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Social publishing: which platforms were selected at approval time
    selected_platforms = Column(JSON, nullable=True)  # e.g. ["instagram", "tiktok"]

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    owner = relationship("User", back_populates="videos")
    approvals = relationship("Approval", back_populates="video", cascade="all, delete-orphan")
    generation_attempts = relationship("GenerationAttempt", back_populates="video", cascade="all, delete-orphan")
    scene_assets = relationship("SceneAsset", back_populates="video", cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPost", back_populates="video", cascade="all, delete-orphan")
    publishing_configurations = relationship("PublishingConfiguration", back_populates="video", cascade="all, delete-orphan")
    publications = relationship("VideoPublication", back_populates="video", cascade="all, delete-orphan")


class SceneAsset(Base):
    __tablename__ = "scene_assets"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    scene_number = Column(Integer, nullable=False)
    image_path = Column(String, nullable=True)
    visual_prompt = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, generating, completed, failed
    provider = Column(String, nullable=True)
    is_mock = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    video = relationship("Video", back_populates="scene_assets")

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, default="APPROVED")  # "APPROVED" or "REJECTED"
    is_approved = Column(Boolean, default=False)
    rejection_reason = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    
    video = relationship("Video", back_populates="approvals")
    reviewer = relationship("User", back_populates="approvals")

class GenerationAttempt(Base):
    __tablename__ = "generation_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    attempt_number = Column(Integer, default=1)
    stage = Column(String, default="NOT_STARTED")
    status = Column(String, default="STARTED")  # STARTED, COMPLETED, FAILED
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    video = relationship("Video", back_populates="generation_attempts")

class SocialPlatform(str, enum.Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    platform = Column(String, nullable=False, index=True)  # youtube, instagram, tiktok
    account_id = Column(String, nullable=True, index=True)  # External channel/user id
    account_name = Column(String, nullable=True)  # Display name e.g. "TechTalks Channel"
    account_handle = Column(String, nullable=True)  # Handle e.g. "@techtalks"
    encrypted_access_token = Column(Text, nullable=True)  # Never stored in plain text
    encrypted_refresh_token = Column(Text, nullable=True)  # Never stored in plain text
    token_expires_at = Column(DateTime, nullable=True)
    status = Column(String, default="ACTIVE")  # ACTIVE, EXPIRED, REVOKED, DISCONNECTED
    is_mock = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)  # Profile pic url, profile url, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="social_accounts")
    scheduled_posts = relationship("ScheduledPost", back_populates="account", foreign_keys="[ScheduledPost.connected_account_id]")
    publishing_settings = relationship("PlatformPublishingSetting", back_populates="account")

class PublishingConfiguration(Base):
    __tablename__ = "publishing_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    status = Column(String, default="DRAFT")  # DRAFT, VALIDATED, READY_TO_SCHEDULE, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    video = relationship("Video", back_populates="publishing_configurations")
    settings = relationship("PlatformPublishingSetting", back_populates="configuration", cascade="all, delete-orphan")

class PlatformPublishingSetting(Base):
    __tablename__ = "platform_publishing_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    configuration_id = Column(Integer, ForeignKey("publishing_configurations.id"), index=True)
    platform = Column(String, nullable=False, index=True)  # youtube, instagram, tiktok
    account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=True)
    platform_metadata = Column(JSON, nullable=True)  # {title, description, caption, hashtags, privacy, ...}
    is_validated = Column(Boolean, default=False)
    validation_errors = Column(JSON, nullable=True)  # list of error strings
    status = Column(String, default="CONFIGURED")  # CONFIGURED, VALIDATED, ERROR
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    configuration = relationship("PublishingConfiguration", back_populates="settings")
    account = relationship("SocialAccount", back_populates="publishing_settings")

class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    platform = Column(String, nullable=False, index=True)  # youtube, instagram, tiktok
    connected_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=True, index=True)
    scheduled_time = Column(DateTime, nullable=False, index=True)  # Always UTC
    timezone = Column(String, default="UTC")  # e.g. "Asia/Karachi"
    platform_metadata = Column(JSON, nullable=True)
    status = Column(String, default="SCHEDULED", index=True)  # SCHEDULED, PUBLISHING, PUBLISHED, FAILED, RETRY, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    external_post_id = Column(String, nullable=True, index=True)
    post_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    video = relationship("Video", back_populates="scheduled_posts")
    account = relationship("SocialAccount", back_populates="scheduled_posts", foreign_keys=[connected_account_id])


class VideoPublication(Base):
    """
    Per-platform publishing record created at approval time.
    Tracks the status of each selected platform independently.
    One row per (video, platform) pair.
    """
    __tablename__ = "video_publications"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True, nullable=False)
    platform = Column(String, nullable=False, index=True)  # youtube, instagram, tiktok
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=True)
    status = Column(
        Enum(PublicationStatus, values_callable=lambda obj: [e.value for e in obj]),
        default=PublicationStatus.QUEUED
    )
    platform_post_id = Column(String, nullable=True)    # External post/video ID returned by platform
    post_url = Column(String, nullable=True)             # Public URL of the post
    error_message = Column(Text, nullable=True)          # Safe error detail (no tokens)
    attempt_count = Column(Integer, default=0)           # Track retry attempts
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    video = relationship("Video", back_populates="publications")
    social_account = relationship("SocialAccount")

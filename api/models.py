from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class VideoStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ERROR = "error"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    videos = relationship("Video", back_populates="owner")
    social_accounts = relationship("SocialAccount", back_populates="user")

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    duration = Column(String, nullable=True)
    language = Column(String, nullable=True)
    style = Column(String, nullable=True)
    target_platform = Column(String, nullable=True)
    script = Column(Text, nullable=True)
    plan = Column(JSON, nullable=True)
    video_url = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    video_path = Column(String, nullable=True)
    subtitles_path = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    status = Column(Enum(VideoStatus, values_callable=lambda obj: [e.value for e in obj]), default=VideoStatus.PENDING)
    generation_stage = Column(String, default="NOT_STARTED")
    resolution = Column(String, default="1080x1920")
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User", back_populates="videos")
    approvals = relationship("Approval", back_populates="video", cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPost", back_populates="video", cascade="all, delete-orphan")

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    is_approved = Column(Boolean, default=False)
    comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=datetime.utcnow)
    
    video = relationship("Video", back_populates="approvals")
    reviewer = relationship("User")

class SocialPlatform(str, enum.Enum):
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"

class SocialAccount(Base):
    __tablename__ = "social_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(Enum(SocialPlatform, values_callable=lambda obj: [e.value for e in obj]))
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)
    
    user = relationship("User", back_populates="social_accounts")
    scheduled_posts = relationship("ScheduledPost", back_populates="account")

class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    account_id = Column(Integer, ForeignKey("social_accounts.id"))
    publish_time = Column(DateTime, nullable=False)
    is_published = Column(Boolean, default=False)
    
    video = relationship("Video", back_populates="scheduled_posts")
    account = relationship("SocialAccount", back_populates="scheduled_posts")

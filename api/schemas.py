from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import VideoStatus, SocialPlatform

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        orm_mode = True

class VideoBase(BaseModel):
    prompt: str

class VideoCreate(VideoBase):
    duration: Optional[str] = "30-60 seconds"
    language: Optional[str] = "English"
    style: Optional[str] = "Standard"
    target_platform: Optional[str] = "Any"

class VideoResponse(VideoBase):
    id: int
    duration: Optional[str] = None
    language: Optional[str] = None
    style: Optional[str] = None
    target_platform: Optional[str] = None
    status: VideoStatus
    script: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    video_url: Optional[str] = None
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    subtitles_path: Optional[str] = None
    error_message: Optional[str] = None
    generation_stage: Optional[str] = None
    resolution: Optional[str] = None
    created_at: datetime
    owner_id: int
    
    class Config:
        orm_mode = True

class ApprovalBase(BaseModel):
    is_approved: bool
    comments: Optional[str] = None

class ApprovalCreate(ApprovalBase):
    video_id: int
    reviewer_id: int

class ApprovalResponse(ApprovalBase):
    id: int
    video_id: int
    reviewer_id: int
    reviewed_at: datetime
    
    class Config:
        orm_mode = True

class Scene(BaseModel):
    scene_number: int
    scene_duration: str
    narration: str
    visual_description: str

class VideoPlan(BaseModel):
    title: str
    short_description: str
    complete_narration: str
    scenes: List[Scene]
    suggested_background_music: str
    caption: str
    hashtags: List[str]

export interface Scene {
  scene_id: number;
  narration: string;
  image_prompt: string;
  duration: number;
  image_path?: string;
  generated_image_path?: string;
}

export interface VideoPublication {
  id: number;
  video_id: number;
  platform: string;
  social_account_id?: number | null;
  account_name?: string | null;
  account_handle?: string | null;
  is_mock?: boolean;
  status: 'QUEUED' | 'PUBLISHING' | 'PUBLISHED' | 'FAILED';
  platform_post_id?: string | null;
  post_url?: string | null;
  error_message?: string | null;
  attempt_count: number;
  created_at: string;
  published_at?: string | null;
  updated_at?: string;
}

export interface Video {
  id: number;
  title: string;
  topic?: string;
  target_audience?: string;
  tone?: string;
  aspect_ratio?: string;
  status:
    | 'DRAFT'
    | 'GENERATING'
    | 'PROCESSING'
    | 'QA_PENDING'
    | 'PENDING_APPROVAL'
    | 'PENDING_REVIEW'
    | 'APPROVED'
    | 'READY_TO_SCHEDULE'
    | 'SCHEDULED'
    | 'PUBLISHING'
    | 'PUBLISHED'
    | 'REJECTED'
    | 'FAILED'
    | string;
  generation_stage?: string | null;
  resolution?: string | null;
  script?: {
    hook?: string;
    scenes?: Scene[];
    cta?: string;
  } | string | null;
  video_url?: string | null;
  video_path?: string | null;
  final_video_path?: string | null;
  thumbnail_path?: string | null;
  audio_path?: string | null;
  subtitles_path?: string | null;
  visual_style?: string | null;
  visual_provider?: string | null;
  visual_generation_status?: Record<string, any> | null;
  selected_platforms?: string[] | null;
  rejection_reason?: string | null;
  error_message?: string | null;
  qa_report?: Record<string, any> | null;
  approved_at?: string | null;
  published_at?: string | null;
  created_at: string;
  updated_at?: string;
  publications?: VideoPublication[];
}

export interface SocialAccount {
  id: number;
  platform: 'tiktok' | 'youtube' | 'instagram' | string;
  account_id?: string;
  account_name: string;
  account_handle?: string;
  status: 'ACTIVE' | 'REVOKED' | 'EXPIRED' | string;
  is_mock: boolean;
  metadata_json?: Record<string, any> | null;
  token_expires_at?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface CreateVideoPayload {
  prompt?: string;
  topic?: string;
  target_audience?: string;
  tone?: string;
  aspect_ratio?: string;
  visual_style?: string;
  visual_provider?: string;
  selected_platforms?: string[];
  duration?: string;
  language?: string;
  style?: string;
  target_platform?: string;
}


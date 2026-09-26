import { Video } from '../types';

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

/**
 * Resolves a safe, absolute URL for a media asset path or URL.
 */
export function resolveMediaUrl(pathOrUrl?: string | null): string | null {
  if (!pathOrUrl) return null;
  const trimmed = pathOrUrl.trim();
  if (!trimmed) return null;

  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed;
  }

  const cleanPath = trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
  return `${API_BASE}${cleanPath}`;
}

/**
 * Extracts and resolves the final MP4 video URL from a Video object or path string.
 */
export function getVideoUrl(videoOrPath?: Video | string | null): string | null {
  if (!videoOrPath) return null;

  if (typeof videoOrPath === 'string') {
    return resolveMediaUrl(videoOrPath);
  }

  const rawPath =
    videoOrPath.video_url ||
    videoOrPath.video_path ||
    videoOrPath.final_video_path ||
    null;

  return resolveMediaUrl(rawPath);
}

/**
 * Extracts and resolves the thumbnail image URL from a Video object or path string.
 */
export function getThumbnailUrl(videoOrPath?: Video | string | null): string | null {
  if (!videoOrPath) return null;

  if (typeof videoOrPath === 'string') {
    return resolveMediaUrl(videoOrPath);
  }

  const rawPath = videoOrPath.thumbnail_path || null;
  return resolveMediaUrl(rawPath);
}

/**
 * Helper to check if a video is currently being generated/processed by the pipeline.
 */
export function isVideoGenerating(video?: Video | null): boolean {
  if (!video) return false;
  const status = (video.status || '').toUpperCase();
  return status === 'GENERATING' || status === 'PROCESSING' || status === 'QA_PENDING';
}

/**
 * Helper to check if a video is ready for admin review/approval.
 */
export function isVideoPendingReview(video?: Video | null): boolean {
  if (!video) return false;
  const status = (video.status || '').toUpperCase();
  return status === 'PENDING_APPROVAL' || status === 'PENDING_REVIEW' || status === 'GENERATED';
}

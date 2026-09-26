import { Video, VideoPublication, SocialAccount, CreateVideoPayload } from '../types';
import { ApiError, normalizeApiError, logApiInteraction, sanitizePayload } from '../utils/errors';

export { ApiError, normalizeApiError, sanitizePayload };

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const method = options?.method || 'GET';

  // Development request logging
  let parsedPayload: any = undefined;
  if (options?.body) {
    try {
      parsedPayload = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
    } catch {
      parsedPayload = options.body;
    }
  }
  logApiInteraction('REQUEST', { method, endpoint, payload: parsedPayload });

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Role': 'admin',
        ...options?.headers,
      },
    });
  } catch (networkErr: any) {
    const errorMsg = normalizeApiError(networkErr, 'Network request failed. Is backend running?');
    logApiInteraction('ERROR', { method, endpoint, status: 0, error: errorMsg });
    throw new ApiError(errorMsg, 0, networkErr);
  }

  if (!response.ok) {
    let errorData: any = null;
    let rawText = '';
    try {
      rawText = await response.text();
      errorData = JSON.parse(rawText);
    } catch {
      errorData = rawText;
    }

    const normalizedMsg = normalizeApiError(
      errorData || `Request failed with status ${response.status}`,
      `Request failed with status ${response.status}`
    );

    logApiInteraction('ERROR', {
      method,
      endpoint,
      status: response.status,
      error: normalizedMsg,
    });

    throw new ApiError(normalizedMsg, response.status, errorData);
  }

  logApiInteraction('RESPONSE', { method, endpoint, status: response.status });

  // Handle empty responses (204 No Content, etc.)
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  return response.text() as any;
}

export const api = {
  // Video endpoints
  getVideos: () => request<Video[]>('/videos/'),
  getVideo: (id: number) => request<Video>(`/videos/${id}`),

  createVideo: (payload: CreateVideoPayload) => {
    // Ensure prompt is populated from topic or prompt
    const promptText = (payload.prompt || payload.topic || '').trim();
    const primaryPlatform =
      payload.target_platform ||
      (payload.selected_platforms && payload.selected_platforms.length > 0
        ? payload.selected_platforms[0]
        : 'TikTok');

    const formattedPayload = {
      prompt: promptText,
      topic: promptText,
      duration: payload.duration || '30-60 seconds',
      language: payload.language || 'English',
      style: payload.style || payload.tone || 'Standard',
      target_platform: primaryPlatform,
      visual_style: payload.visual_style || 'realistic',
      visual_provider: payload.visual_provider || 'local',
      selected_platforms: payload.selected_platforms || ['tiktok', 'youtube'],
      target_audience: payload.target_audience,
      tone: payload.tone,
      aspect_ratio: payload.aspect_ratio || '9:16',
    };

    return request<Video>('/videos/', {
      method: 'POST',
      body: JSON.stringify(formattedPayload),
    });
  },

  generateVideo: (
    id: number,
    options?: {
      visual_provider?: string;
      visual_style?: string;
      selected_platforms?: string[];
      scene_prompts?: Record<string, string>;
    }
  ) =>
    request<Video>(`/videos/${id}/generate`, {
      method: 'POST',
      body: JSON.stringify(options || {}),
    }),

  regenerateScene: (videoId: number, sceneId: number, prompt?: string, provider?: string) =>
    request<any>(`/videos/${videoId}/scenes/${sceneId}/regenerate`, {
      method: 'POST',
      body: JSON.stringify({ prompt, provider }),
    }),

  approveAndPublish: (id: number, payload?: { selected_platforms?: string[]; auto_publish?: boolean }) =>
    request<any>(`/videos/${id}/approve-and-publish`, {
      method: 'POST',
      body: JSON.stringify(payload || { auto_publish: true }),
    }),

  rejectVideo: (id: number, reason: string) =>
    request<any>(`/videos/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  regenerateVideo: (id: number) =>
    request<any>(`/videos/${id}/regenerate`, {
      method: 'POST',
    }),

  retryPublication: (videoId: number, platform: string) =>
    request<any>(`/videos/${videoId}/publications/${platform}/retry`, {
      method: 'POST',
    }),

  // Publications
  getPublications: () => request<VideoPublication[]>('/publications'),
  getVideoPublications: (id: number) => request<VideoPublication[]>(`/videos/${id}/publications`),


  // Social accounts
  getSocialAccounts: () => request<SocialAccount[]>('/social/accounts'),

  disconnectSocialAccount: (id: number) =>
    request<any>(`/social/accounts/${id}/disconnect`, {
      method: 'POST',
    }),

  getOAuthUrl: (platform: string) =>
    request<{ authorization_url: string; state?: string }>(`/social/oauth/${platform}/authorize`),

  // System
  getHealth: () => request<{ status: string; message: string }>('/health'),
};

"""
Explicit Sandbox / Mock Social Media Provider.
Used for zero-config testing and local development when official app credentials
are not yet registered in developer portals.
Strictly separated from production providers.
"""

import os
from typing import Dict, Any, List, Tuple, Optional
from .base import SocialPlatformProvider, PlatformCapabilities
from .youtube import YouTubeProvider
from .instagram import InstagramProvider
from .tiktok import TikTokProvider


class MockSocialProvider(SocialPlatformProvider):
    """
    Sandbox provider that simulates official platform OAuth and enforces
    the exact same platform-specific validation rules without requiring external API access.
    """

    def __init__(self, platform: str):
        self._platform = platform.lower()
        if self._platform == "youtube":
            self._real_provider = YouTubeProvider()
        elif self._platform == "instagram":
            self._real_provider = InstagramProvider()
        elif self._platform == "tiktok":
            self._real_provider = TikTokProvider()
        else:
            raise ValueError(f"Unsupported sandbox platform: {platform}")

    @property
    def platform_name(self) -> str:
        return self._platform

    @property
    def capabilities(self) -> PlatformCapabilities:
        real_caps = self._real_provider.capabilities
        # Return real capabilities but mark as sandbox
        return PlatformCapabilities(
            platform_name=real_caps.platform_name,
            display_name=f"{real_caps.display_name} (Sandbox/Dev)",
            official_api_name=f"Mock {real_caps.official_api_name}",
            is_cost_free=True,
            supports_video=real_caps.supports_video,
            supports_custom_thumbnail=real_caps.supports_custom_thumbnail,
            supports_tags=real_caps.supports_tags,
            max_title_length=real_caps.max_title_length,
            max_caption_length=real_caps.max_caption_length,
            max_hashtags=real_caps.max_hashtags,
            supported_privacy_levels=real_caps.supported_privacy_levels,
            requires_developer_app=False,
            required_env_vars=[],
            limitations=real_caps.limitations + ["Running in isolated Sandbox Mode for Phase 5 verification."]
        )

    def is_configured(self) -> bool:
        # Sandbox provider is always available for zero-friction local testing
        return True

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        return f"{redirect_uri}?code=sandbox_auth_code_{self._platform}&state={state}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        return {
            "access_token": f"sandbox_access_token_{self._platform}_xyz123",
            "refresh_token": f"sandbox_refresh_token_{self._platform}_ref456",
            "expires_in": 86400 * 30,
            "scopes": ["sandbox_full_access"]
        }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        return {
            "access_token": f"refreshed_sandbox_token_{self._platform}",
            "refresh_token": refresh_token,
            "expires_in": 86400 * 30
        }

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        sandbox_accounts = {
            "youtube": {
                "account_id": "UC_sandbox_channel_001",
                "account_name": "DevStudio Shorts [Sandbox]",
                "account_handle": "@devstudio_shorts",
                "avatar_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop",
                "profile_url": "https://www.youtube.com/@devstudio_shorts"
            },
            "instagram": {
                "account_id": "17841400000000001",
                "account_name": "AI Studio Reels [Sandbox]",
                "account_handle": "@aistudio.reels",
                "avatar_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop",
                "profile_url": "https://www.instagram.com/aistudio.reels"
            },
            "tiktok": {
                "account_id": "tiktok_open_id_sandbox_999",
                "account_name": "ViralShorts Studio [Sandbox]",
                "account_handle": "@viralshorts_studio",
                "avatar_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=100&auto=format&fit=crop",
                "profile_url": "https://www.tiktok.com/@viralshorts_studio"
            }
        }
        return sandbox_accounts.get(self._platform, {
            "account_id": f"mock_id_{self._platform}",
            "account_name": f"{self._platform.capitalize()} Sandbox Account",
            "account_handle": f"@{self._platform}_sandbox",
            "avatar_url": None,
            "profile_url": None
        })

    def validate_publishing_metadata(
        self,
        metadata: Dict[str, Any],
        video_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        # Enforce real platform validation rules even in sandbox mode!
        return self._real_provider.validate_publishing_metadata(metadata, video_path)

    def publish_video(
        self,
        access_token: str,
        video_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simulates official platform publishing with strict validation checks.
        Allows simulated failures when requested via metadata for testing retry paths.
        """
        import uuid
        import time

        # Simulate API network transit
        time.sleep(0.5)

        # Allow test suite to simulate failure
        if metadata.get("simulate_failure"):
            return {
                "success": False,
                "error": metadata.get("simulated_error_message", f"Simulated {self._platform.capitalize()} API rate limit (429 RateLimitExceeded).")
            }

        # Check video file exists on disk
        if not os.path.exists(video_path):
            return {
                "success": False,
                "error": f"Video file not found at '{video_path}'."
            }

        rand_id = str(uuid.uuid4())[:8]
        if self._platform == "youtube":
            post_id = f"yt_{rand_id}"
            url = f"https://www.youtube.com/shorts/{post_id}"
        elif self._platform == "instagram":
            post_id = f"ig_{rand_id}"
            url = f"https://www.instagram.com/reel/{post_id}"
        elif self._platform == "tiktok":
            post_id = f"tt_{rand_id}"
            url = f"https://www.tiktok.com/@creator/video/{post_id}"
        else:
            post_id = f"mock_{self._platform}_{rand_id}"
            url = f"https://{self._platform}.com/post/{post_id}"

        return {
            "success": True,
            "external_post_id": post_id,
            "post_url": url,
            "error": None
        }


"""
Social Publisher Registry, Provider Factory, and Validation Orchestrator.
Coordinates official providers and sandbox providers.
"""

from typing import Dict, Any, List, Tuple, Optional
from .base import SocialPlatformProvider
from .youtube import YouTubeProvider
from .instagram import InstagramProvider
from .tiktok import TikTokProvider
from .mock_provider import MockSocialProvider


class SocialProviderRegistry:
    """
    Registry and factory for social platform providers.
    Supports official providers as well as explicit sandbox providers.
    """

    SUPPORTED_PLATFORMS = ["youtube", "instagram", "tiktok"]

    @classmethod
    def get_provider(cls, platform: str, use_sandbox: bool = False) -> SocialPlatformProvider:
        clean_platform = platform.lower().strip()
        if clean_platform not in cls.SUPPORTED_PLATFORMS:
            raise ValueError(f"Platform '{platform}' is not supported. Supported: {cls.SUPPORTED_PLATFORMS}")

        if use_sandbox:
            return MockSocialProvider(clean_platform)

        if clean_platform == "youtube":
            return YouTubeProvider()
        elif clean_platform == "instagram":
            return InstagramProvider()
        elif clean_platform == "tiktok":
            return TikTokProvider()
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    @classmethod
    def get_platform_info(cls, platform: str) -> Dict[str, Any]:
        clean_platform = platform.lower().strip()
        real_p = cls.get_provider(clean_platform, use_sandbox=False)
        caps = real_p.capabilities
        return {
            "platform": caps.platform_name,
            "display_name": caps.display_name,
            "official_api_name": caps.official_api_name,
            "is_cost_free": caps.is_cost_free,
            "is_configured": real_p.is_configured(),
            "required_env_vars": caps.required_env_vars,
            "max_title_length": caps.max_title_length,
            "max_caption_length": caps.max_caption_length,
            "max_hashtags": caps.max_hashtags,
            "supported_privacy_levels": caps.supported_privacy_levels,
            "limitations": caps.limitations
        }

    @classmethod
    def list_all_platforms(cls) -> List[Dict[str, Any]]:
        return [cls.get_platform_info(p) for p in cls.SUPPORTED_PLATFORMS]

    @classmethod
    def validate_metadata(
        cls,
        platform: str,
        metadata: Dict[str, Any],
        video_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates platform-specific publishing configuration.
        """
        provider = cls.get_provider(platform, use_sandbox=False)
        return provider.validate_publishing_metadata(metadata, video_path)

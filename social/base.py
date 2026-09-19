"""
Abstract Base Class for Social Media Platform Providers.
Every platform (YouTube, Instagram, TikTok) implements this contract.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class PlatformCapabilities:
    platform_name: str
    display_name: str
    official_api_name: str
    is_cost_free: bool = True
    supports_video: bool = True
    supports_custom_thumbnail: bool = True
    supports_tags: bool = True
    max_title_length: int = 100
    max_caption_length: int = 2200
    max_hashtags: int = 30
    supported_privacy_levels: List[str] = field(default_factory=list)
    requires_developer_app: bool = True
    required_env_vars: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)


class SocialPlatformProvider(ABC):
    """
    Abstract interface for official social media platform integration.
    """

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the identifier for the platform (e.g. 'youtube', 'instagram', 'tiktok')."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> PlatformCapabilities:
        """Returns capability specification and constraints for this platform."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the required official developer app credentials exist in environment."""
        pass

    @abstractmethod
    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        """
        Builds the official OAuth2 authorization URL to initiate user consent.
        Raises ValueError if provider is not configured with app credentials.
        """
        pass

    @abstractmethod
    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchanges authorization code for access_token and optional refresh_token.
        Returns dict: {
            "access_token": str,
            "refresh_token": Optional[str],
            "expires_in": Optional[int],
            "scopes": List[str]
        }
        """
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Uses refresh_token to obtain a new access_token.
        """
        pass

    @abstractmethod
    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        """
        Fetches the authenticated user's channel/profile info.
        Returns dict: {
            "account_id": str,
            "account_name": str,
            "account_handle": str,
            "avatar_url": Optional[str],
            "profile_url": Optional[str]
        }
        """
        pass

    @abstractmethod
    def validate_publishing_metadata(
        self,
        metadata: Dict[str, Any],
        video_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validates platform-specific publishing configuration before saving.
        Returns (is_valid: bool, error_messages: List[str]).
        """
        pass

    @abstractmethod
    def publish_video(
        self,
        access_token: str,
        video_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publishes the video to the social platform using the official API.
        Returns dict: {
            "success": bool,
            "external_post_id": Optional[str],
            "post_url": Optional[str],
            "error": Optional[str]
        }
        """
        pass


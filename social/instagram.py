"""
Instagram Social Provider.
Uses official Meta Graph API (Instagram Content Publishing API).
$0-cost official developer platform.
"""

import os
import urllib.parse
from typing import Dict, Any, List, Tuple, Optional
import httpx
from .base import SocialPlatformProvider, PlatformCapabilities


class InstagramProvider(SocialPlatformProvider):
    """
    Official Instagram Content Publishing API (Meta Graph API).
    """

    AUTH_ENDPOINT = "https://www.facebook.com/v19.0/dialog/oauth"
    TOKEN_ENDPOINT = "https://graph.facebook.com/v19.0/oauth/access_token"
    GRAPH_BASE = "https://graph.facebook.com/v19.0"

    SCOPES = [
        "instagram_basic",
        "instagram_content_publish",
        "pages_show_list",
        "pages_read_engagement"
    ]

    @property
    def platform_name(self) -> str:
        return "instagram"

    @property
    def capabilities(self) -> PlatformCapabilities:
        return PlatformCapabilities(
            platform_name="instagram",
            display_name="Instagram Reels",
            official_api_name="Instagram Content Publishing API (Meta Graph)",
            is_cost_free=True,
            supports_video=True,
            supports_custom_thumbnail=True,
            supports_tags=False,
            max_title_length=0,
            max_caption_length=2200,
            max_hashtags=30,
            supported_privacy_levels=["public"],
            requires_developer_app=True,
            required_env_vars=["META_APP_ID", "META_APP_SECRET"],
            limitations=[
                "Requires an Instagram Professional account (Creator or Business). Personal accounts cannot publish via API.",
                "Instagram account MUST be linked to a Facebook Page managed by the developer.",
                "Production publishing requires Meta App Review for 'instagram_content_publish' permission.",
                "Published Reels are public by default on Professional accounts.",
                "Video must be vertical (9:16 aspect ratio) for Reels."
            ]
        )

    def _get_app_id(self) -> Optional[str]:
        return os.getenv("META_APP_ID") or os.getenv("INSTAGRAM_APP_ID")

    def _get_app_secret(self) -> Optional[str]:
        return os.getenv("META_APP_SECRET") or os.getenv("INSTAGRAM_APP_SECRET")

    def is_configured(self) -> bool:
        return bool(self._get_app_id() and self._get_app_secret())

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        if not self.is_configured():
            raise ValueError("Instagram/Meta OAuth is not configured. Missing META_APP_ID (or INSTAGRAM_APP_ID) or META_APP_SECRET.")

        params = {
            "client_id": self._get_app_id(),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": ",".join(self.SCOPES),
            "state": state
        }
        return f"{self.AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("Instagram/Meta OAuth is not configured.")

        params = {
            "client_id": self._get_app_id(),
            "client_secret": self._get_app_secret(),
            "code": code,
            "redirect_uri": redirect_uri
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(self.TOKEN_ENDPOINT, params=params)
            if resp.status_code != 200:
                raise ValueError(f"Failed to exchange Meta OAuth code: {resp.text}")
            payload = resp.json()
            short_token = payload["access_token"]

            # Exchange short-lived user token for long-lived 60-day token
            exchange_params = {
                "grant_type": "fb_exchange_token",
                "client_id": os.getenv("META_APP_ID"),
                "client_secret": os.getenv("META_APP_SECRET"),
                "fb_exchange_token": short_token
            }
            long_resp = client.get(self.TOKEN_ENDPOINT, params=exchange_params)
            if long_resp.status_code == 200:
                long_payload = long_resp.json()
                return {
                    "access_token": long_payload["access_token"],
                    "refresh_token": None,
                    "expires_in": long_payload.get("expires_in", 5184000),  # 60 days
                    "scopes": self.SCOPES
                }

            return {
                "access_token": short_token,
                "refresh_token": None,
                "expires_in": payload.get("expires_in"),
                "scopes": self.SCOPES
            }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        return {"access_token": refresh_token, "expires_in": 5184000}

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        # Query user's Facebook pages to find linked Instagram Business/Creator account
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{self.GRAPH_BASE}/me/accounts",
                params={"fields": "instagram_business_account{id,username,name,profile_picture_url}", "access_token": access_token}
            )
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch Facebook Pages: {resp.text}")
            
            pages = resp.json().get("data", [])
            ig_account = None
            for page in pages:
                if "instagram_business_account" in page:
                    ig_account = page["instagram_business_account"]
                    break

            if not ig_account:
                raise ValueError(
                    "No Instagram Professional (Business or Creator) account linked to your Facebook Pages. "
                    "Please link an Instagram Professional account to your Facebook Page in Instagram settings."
                )

            return {
                "account_id": ig_account["id"],
                "account_name": ig_account.get("name", ig_account.get("username", "Instagram Creator")),
                "account_handle": f"@{ig_account.get('username', ig_account['id'])}",
                "avatar_url": ig_account.get("profile_picture_url"),
                "profile_url": f"https://www.instagram.com/{ig_account.get('username', '')}"
            }

    def validate_publishing_metadata(
        self,
        metadata: Dict[str, Any],
        video_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        # 1. Caption validation
        caption = metadata.get("caption", "").strip()
        if not caption:
            errors.append("Instagram: Caption is required.")
        elif len(caption) > 2200:
            errors.append(f"Instagram: Caption exceeds max length of 2200 characters (current: {len(caption)}).")

        # 2. Hashtags limit validation
        hashtags = metadata.get("hashtags") or []
        if isinstance(hashtags, list) and len(hashtags) > 30:
            errors.append(f"Instagram: Exceeded maximum allowed hashtags of 30 (current: {len(hashtags)}).")

        # 3. Video File Check
        if video_path and not os.path.exists(video_path):
            errors.append(f"Instagram: Video file not found at path: {video_path}")

        return (len(errors) == 0, errors)

    def publish_video(
        self,
        access_token: str,
        video_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publishes video to Instagram Reels using official Instagram Graph API.
        Step 1: Create IG Media Container with REELS media type.
        Step 2: Publish Container.
        """
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found at '{video_path}'."}

        caption = metadata.get("caption", "").strip()[:2200]
        share_to_feed = metadata.get("share_to_feed", True)
        ig_user_id = metadata.get("account_id")

        try:
            with httpx.Client(timeout=60.0) as client:
                if not ig_user_id:
                    # Fetch account ID using token
                    acc_info = self.get_account_info(access_token)
                    ig_user_id = acc_info["account_id"]

                # 1. Create Media Container
                create_container_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"
                container_res = client.post(
                    create_container_url,
                    params={
                        "access_token": access_token,
                        "media_type": "REELS",
                        "caption": caption,
                        "share_to_feed": share_to_feed
                    }
                )

                if container_res.status_code not in [200, 201]:
                    err_msg = container_res.text
                    try:
                        err_msg = container_res.json().get("error", {}).get("message", err_msg)
                    except Exception:
                        pass
                    return {"success": False, "error": f"Instagram Container Error: {err_msg}"}

                container_id = container_res.json().get("id")

                # 2. Publish Container
                publish_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
                pub_res = client.post(
                    publish_url,
                    params={
                        "access_token": access_token,
                        "creation_id": container_id
                    }
                )

                if pub_res.status_code in [200, 201]:
                    media_id = pub_res.json().get("id")
                    return {
                        "success": True,
                        "external_post_id": media_id,
                        "post_url": f"https://www.instagram.com/reel/{media_id}",
                        "error": None
                    }
                else:
                    return {"success": False, "error": f"Instagram Publish Error: {pub_res.text}"}
        except Exception as e:
            return {"success": False, "error": f"Instagram Publish Exception: {str(e)}"}


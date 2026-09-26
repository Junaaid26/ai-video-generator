"""
Instagram Social Provider.
Uses official Meta Graph API (Instagram Content Publishing API).
$0-cost official developer platform.
"""

import os
import time
import urllib.parse
from typing import Dict, Any, List, Tuple, Optional
import httpx
from .base import SocialPlatformProvider, PlatformCapabilities


class InstagramProvider(SocialPlatformProvider):
    """
    Official Instagram Content Publishing API (Meta Graph API).
    """

    AUTH_ENDPOINT = "https://www.facebook.com/v20.0/dialog/oauth"
    TOKEN_ENDPOINT = "https://graph.facebook.com/v20.0/oauth/access_token"
    GRAPH_BASE = "https://graph.facebook.com/v20.0"

    SCOPES = [
        "pages_show_list",
        "instagram_basic",
        "instagram_content_publish",
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
                "Instagram account MUST be linked to a Facebook Page managed by the developer in Meta Business Suite.",
                "Production publishing requires Meta App Review for 'instagram_content_publish' permission.",
                "Published Reels are public by default on Professional accounts.",
                "Video must be accessible via public HTTPS URL for Instagram servers to fetch."
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
            raise ValueError(
                "Instagram/Meta OAuth is not configured. Missing META_APP_ID or META_APP_SECRET in .env."
            )

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

        # Step 1: Exchange authorization code for short-lived user token
        params = {
            "client_id": self._get_app_id(),
            "client_secret": self._get_app_secret(),
            "code": code,
            "redirect_uri": redirect_uri
        }
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(self.TOKEN_ENDPOINT, params=params)
            if resp.status_code != 200:
                err_detail = resp.text
                try:
                    err_detail = resp.json().get("error", {}).get("message", err_detail)
                except Exception:
                    pass
                raise ValueError(f"Meta OAuth code exchange failed: {err_detail}")
            
            payload = resp.json()
            short_token = payload["access_token"]

            # Step 2: Exchange short-lived token for 60-day long-lived User Access Token
            long_lived_params = {
                "grant_type": "fb_exchange_token",
                "client_id": self._get_app_id(),
                "client_secret": self._get_app_secret(),
                "fb_exchange_token": short_token
            }
            long_resp = client.get(self.TOKEN_ENDPOINT, params=long_lived_params)
            if long_resp.status_code == 200:
                long_payload = long_resp.json()
                return {
                    "access_token": long_payload["access_token"],
                    "refresh_token": long_payload["access_token"],
                    "expires_in": long_payload.get("expires_in", 5184000),  # 60 days
                    "scopes": self.SCOPES
                }

            return {
                "access_token": short_token,
                "refresh_token": None,
                "expires_in": payload.get("expires_in", 3600),
                "scopes": self.SCOPES
            }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refreshes a long-lived user token using fb_exchange_token.
        """
        if not self.is_configured():
            raise ValueError("Instagram/Meta OAuth is not configured.")

        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self._get_app_id(),
            "client_secret": self._get_app_secret(),
            "fb_exchange_token": refresh_token
        }
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(self.TOKEN_ENDPOINT, params=params)
            if resp.status_code == 200:
                payload = resp.json()
                return {
                    "access_token": payload["access_token"],
                    "expires_in": payload.get("expires_in", 5184000)
                }
        return {"access_token": refresh_token, "expires_in": 5184000}

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        """
        Discovers the linked Instagram Business/Creator account from the user's managed Facebook Pages.
        """
        with httpx.Client(timeout=20.0) as client:
            # Query user's Facebook pages with connected instagram_business_account
            resp = client.get(
                f"{self.GRAPH_BASE}/me/accounts",
                params={
                    "fields": "id,name,access_token,instagram_business_account{id,username,name,profile_picture_url}",
                    "access_token": access_token
                }
            )
            if resp.status_code != 200:
                err_msg = resp.text
                try:
                    err_msg = resp.json().get("error", {}).get("message", err_msg)
                except Exception:
                    pass
                raise ValueError(f"Failed to fetch Meta/Facebook Pages: {err_msg}")
            
            pages_data = resp.json().get("data", [])
            if not pages_data:
                raise ValueError(
                    "No Facebook Pages found for this Meta account. "
                    "Instagram Graph API requires your Instagram Professional account to be linked to a Facebook Page."
                )

            matched_page = None
            ig_account = None

            # First pass: check embedded instagram_business_account
            for page in pages_data:
                if "instagram_business_account" in page and page["instagram_business_account"]:
                    matched_page = page
                    ig_account = page["instagram_business_account"]
                    break

            # Second pass: query page directly if not embedded
            if not ig_account:
                for page in pages_data:
                    page_id = page.get("id")
                    page_tok = page.get("access_token", access_token)
                    p_resp = client.get(
                        f"{self.GRAPH_BASE}/{page_id}",
                        params={
                            "fields": "instagram_business_account{id,username,name,profile_picture_url}",
                            "access_token": page_tok
                        }
                    )
                    if p_resp.status_code == 200:
                        p_data = p_resp.json()
                        if "instagram_business_account" in p_data and p_data["instagram_business_account"]:
                            matched_page = page
                            ig_account = p_data["instagram_business_account"]
                            break

            if not ig_account:
                raise ValueError(
                    "No Instagram Professional (Business or Creator) account linked to your Facebook Pages. "
                    "Please ensure your Instagram account is switched to Professional/Creator mode and linked to a Facebook Page in Meta Business Suite."
                )

            ig_id = str(ig_account["id"])
            ig_username = ig_account.get("username", "")
            ig_name = ig_account.get("name") or ig_username or f"Instagram ({ig_id})"
            avatar_url = ig_account.get("profile_picture_url")
            page_name = matched_page.get("name") if matched_page else None
            page_id = matched_page.get("id") if matched_page else None
            page_access_token = matched_page.get("access_token") if matched_page else None

            return {
                "account_id": ig_id,
                "account_name": ig_name,
                "account_handle": f"@{ig_username}" if ig_username else f"@{ig_id}",
                "avatar_url": avatar_url,
                "profile_url": f"https://www.instagram.com/{ig_username}" if ig_username else None,
                "page_name": page_name,
                "page_id": page_id,
                "page_access_token": page_access_token,
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

    def _resolve_public_video_url(self, video_path_or_url: str) -> Optional[str]:
        """
        Determines the publicly reachable HTTPS URL for the video.
        Instagram requires an external HTTPS URL to download the video.
        """
        if not video_path_or_url:
            return None

        # If already an HTTPS URL (not pointing to localhost/127.0.0.1)
        if video_path_or_url.startswith("https://"):
            if not any(lh in video_path_or_url for lh in ["localhost", "127.0.0.1", "0.0.0.0"]):
                return video_path_or_url

        # Check configured public base URL (e.g. ngrok, reverse proxy, production domain)
        public_base = (
            os.getenv("PUBLIC_BASE_URL") or
            os.getenv("NGROK_URL") or
            os.getenv("HOST_URL") or
            os.getenv("APP_URL")
        )
        if public_base and public_base.startswith("https://"):
            clean_base = public_base.rstrip("/")
            clean_path = video_path_or_url.lstrip("/")
            if not clean_path.startswith("assets/"):
                clean_path = f"assets/{clean_path}"
            return f"{clean_base}/{clean_path}"

        return None

    def publish_video(
        self,
        access_token: str,
        video_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publishes video to Instagram Reels using official Instagram Graph API.
        Step 1: Validate public HTTPS video URL.
        Step 2: Create IG Media Container with REELS media type.
        Step 3: Poll Container status until FINISHED.
        Step 4: Publish Container.
        Step 5: Fetch permalink.
        """
        # Validate local file existence
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found at '{video_path}'."}

        # Validate public HTTPS URL
        video_url = metadata.get("video_url") or video_path
        public_video_url = self._resolve_public_video_url(video_url)
        if not public_video_url:
            return {
                "success": False,
                "error": "Instagram publishing requires a publicly accessible HTTPS video URL. Localhost media cannot be fetched by Instagram."
            }

        caption = metadata.get("caption", "").strip()[:2200]
        share_to_feed = metadata.get("share_to_feed", True)
        ig_user_id = metadata.get("account_id")

        try:
            with httpx.Client(timeout=90.0) as client:
                if not ig_user_id:
                    acc_info = self.get_account_info(access_token)
                    ig_user_id = acc_info["account_id"]

                # 1. Create Media Container for REELS
                create_container_url = f"{self.GRAPH_BASE}/{ig_user_id}/media"
                container_res = client.post(
                    create_container_url,
                    params={
                        "access_token": access_token,
                        "media_type": "REELS",
                        "video_url": public_video_url,
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
                if not container_id:
                    return {"success": False, "error": "Instagram Container ID was not returned."}

                # 2. Poll Container Status until ready (up to 60s)
                poll_url = f"{self.GRAPH_BASE}/{container_id}"
                container_ready = False
                for _ in range(20):
                    time.sleep(3)
                    poll_res = client.get(
                        poll_url,
                        params={"fields": "status_code,status", "access_token": access_token}
                    )
                    if poll_res.status_code == 200:
                        status_data = poll_res.json()
                        status_code = (status_data.get("status_code") or status_data.get("status") or "").upper()
                        if status_code == "FINISHED":
                            container_ready = True
                            break
                        elif status_code in ["ERROR", "EXPIRED"]:
                            return {"success": False, "error": f"Instagram Video Processing failed with status: {status_code}"}

                if not container_ready:
                    return {"success": False, "error": "Instagram Video Container processing timed out."}

                # 3. Publish Container
                publish_url = f"{self.GRAPH_BASE}/{ig_user_id}/media_publish"
                pub_res = client.post(
                    publish_url,
                    params={
                        "access_token": access_token,
                        "creation_id": container_id
                    }
                )

                if pub_res.status_code not in [200, 201]:
                    err_pub = pub_res.text
                    try:
                        err_pub = pub_res.json().get("error", {}).get("message", err_pub)
                    except Exception:
                        pass
                    return {"success": False, "error": f"Instagram Publish Error: {err_pub}"}

                media_id = pub_res.json().get("id")

                # 4. Fetch published Reel permalink
                permalink = None
                try:
                    media_info_res = client.get(
                        f"{self.GRAPH_BASE}/{media_id}",
                        params={"fields": "permalink,shortcode", "access_token": access_token}
                    )
                    if media_info_res.status_code == 200:
                        permalink = media_info_res.json().get("permalink")
                except Exception:
                    pass

                return {
                    "success": True,
                    "external_post_id": media_id,
                    "post_url": permalink or f"https://www.instagram.com/reel/{media_id}",
                    "error": None
                }
        except Exception as e:
            return {"success": False, "error": f"Instagram Publish Exception: {str(e)}"}

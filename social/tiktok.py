"""
TikTok Social Provider.
Uses official TikTok for Developers Content Posting API.
$0-cost official developer platform.
"""

import os
import urllib.parse
import hashlib
import secrets
from typing import Dict, Any, List, Tuple, Optional
import httpx
from .base import SocialPlatformProvider, PlatformCapabilities


def generate_pkce_verifier() -> str:
    """
    Generates a cryptographically secure PKCE code_verifier (43-128 chars).
    Uses secrets.token_urlsafe(64) producing ~86 URL-safe characters.
    """
    return secrets.token_urlsafe(64)


def generate_pkce_challenge(code_verifier: str) -> str:
    """
    Generates TikTok Desktop-compatible code_challenge using SHA-256 HEX encoding.
    """
    return hashlib.sha256(code_verifier.encode("utf-8")).hexdigest()


class TikTokProvider(SocialPlatformProvider):
    """
    Official TikTok Content Posting API.
    """

    AUTH_ENDPOINT = "https://www.tiktok.com/v2/auth/authorize/"
    TOKEN_ENDPOINT = "https://open.tiktokapis.com/v2/oauth/token/"
    USER_INFO_ENDPOINT = "https://open.tiktokapis.com/v2/user/info/"

    SCOPES = [
        "user.info.basic",
        "video.publish"
    ]

    @property
    def platform_name(self) -> str:
        return "tiktok"

    @property
    def capabilities(self) -> PlatformCapabilities:
        return PlatformCapabilities(
            platform_name="tiktok",
            display_name="TikTok",
            official_api_name="TikTok Content Posting API (Direct Post)",
            is_cost_free=True,
            supports_video=True,
            supports_custom_thumbnail=False,
            supports_tags=False,
            max_title_length=0,
            max_caption_length=2200,
            max_hashtags=30,
            supported_privacy_levels=[
                "PUBLIC_TO_EVERYONE",
                "MUTUAL_FOLLOW_FRIENDS",
                "SELF_ONLY"
            ],
            requires_developer_app=True,
            required_env_vars=["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
            limitations=[
                "Requires an approved TikTok Developer App with 'Content Posting API' permissions.",
                "In Sandbox/Development mode, videos can only be published to authorized testing accounts.",
                "Videos must be MP4 or WebM format, between 3s and 10 minutes.",
                "User must explicitly set privacy level (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, or SELF_ONLY)."
            ]
        )

    def is_configured(self) -> bool:
        client_key = os.getenv("TIKTOK_CLIENT_KEY")
        client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        return bool(client_key and client_secret)

    def get_authorization_url(
        self,
        state: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> str:
        if not self.is_configured():
            raise ValueError("TikTok OAuth is not configured. Missing TIKTOK_CLIENT_KEY or TIKTOK_CLIENT_SECRET.")

        if not code_verifier:
            code_verifier = generate_pkce_verifier()

        challenge = generate_pkce_challenge(code_verifier)

        params = {
            "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
            "scope": ",".join(self.SCOPES),
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256"
        }
        return f"{self.AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_tokens(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("TikTok OAuth is not configured.")

        if not code_verifier:
            raise ValueError("Missing required PKCE code_verifier for TikTok token exchange.")

        data = {
            "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
            "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_ENDPOINT, data=data, headers=headers)
            try:
                payload = resp.json()
            except Exception:
                payload = {}

            # Extract TikTok diagnostic fields (non-sensitive)
            log_id = payload.get("log_id") or (
                payload.get("error", {}).get("log_id") if isinstance(payload.get("error"), dict) else None
            )

            # Handle non-200 HTTP responses
            if resp.status_code != 200:
                err_code = payload.get("error")
                err_desc = (
                    payload.get("error_description")
                    or (payload.get("error", {}).get("message") if isinstance(payload.get("error"), dict) else None)
                    or payload.get("message")
                    or resp.text
                )
                diag = f"status={resp.status_code}, error={err_code}, error_description={err_desc}, log_id={log_id}"
                raise ValueError(f"Failed to exchange TikTok code: {diag}")

            # Handle API-level error objects in 200 OK responses
            if payload.get("error"):
                err_val = payload.get("error")
                if isinstance(err_val, dict):
                    err_code = err_val.get("code")
                    err_msg = err_val.get("message", "Unknown error")
                else:
                    err_code = err_val
                    err_msg = payload.get("error_description", "Unknown error")
                diag = f"status={resp.status_code}, error={err_code}, error_description={err_msg}, log_id={log_id}"
                raise ValueError(f"TikTok token exchange rejected: {diag}")
            elif payload.get("error_description"):
                diag = f"status={resp.status_code}, error_description={payload.get('error_description')}, log_id={log_id}"
                raise ValueError(f"TikTok token exchange rejected: {diag}")

            # TikTok v2 /v2/oauth/token/ returns tokens directly at root level (RFC 6749):
            # {"access_token": "...", "expires_in": 86400, "refresh_token": "...", "scope": "...", "open_id": "..."}
            # Support both root-level tokens and legacy/wrapper 'data' objects:
            data_obj = payload if "access_token" in payload else payload.get("data", {})
            if not data_obj or "access_token" not in data_obj:
                sanitized_keys = [k for k in payload.keys() if "token" not in k.lower() and "secret" not in k.lower() and "code" not in k.lower()]
                diag = f"status={resp.status_code}, keys={sanitized_keys}, log_id={log_id}"
                raise ValueError(f"TikTok token exchange failed: No access_token returned by TikTok ({diag})")

            return {
                "access_token": data_obj["access_token"],
                "refresh_token": data_obj.get("refresh_token"),
                "expires_in": data_obj.get("expires_in"),
                "scopes": data_obj.get("scope", "").split(",") if isinstance(data_obj.get("scope"), str) else data_obj.get("scope", [])
            }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("TikTok OAuth is not configured.")

        data = {
            "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
            "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_ENDPOINT, data=data, headers=headers)
            try:
                payload = resp.json()
            except Exception:
                payload = {}

            log_id = payload.get("log_id")
            if resp.status_code != 200:
                err_desc = (
                    payload.get("error_description")
                    or (payload.get("error", {}).get("message") if isinstance(payload.get("error"), dict) else None)
                    or payload.get("message")
                    or resp.text
                )
                raise ValueError(f"Failed to refresh TikTok token (status={resp.status_code}): {err_desc} (log_id={log_id})")

            data_obj = payload if "access_token" in payload else payload.get("data", {})
            if not data_obj or "access_token" not in data_obj:
                raise ValueError(f"TikTok refresh failed: No access_token returned (status={resp.status_code}, log_id={log_id})")

            return {
                "access_token": data_obj["access_token"],
                "refresh_token": data_obj.get("refresh_token", refresh_token),
                "expires_in": data_obj.get("expires_in")
            }

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"fields": "open_id,union_id,avatar_url,display_name"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(self.USER_INFO_ENDPOINT, headers=headers, params=params)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch TikTok user info: {resp.text}")
            user_data = resp.json().get("data", {}).get("user", {})
            return {
                "account_id": user_data.get("open_id", "tiktok_user"),
                "account_name": user_data.get("display_name", "TikTok Creator"),
                "account_handle": f"@{user_data.get('display_name', 'creator').lower().replace(' ', '_')}",
                "avatar_url": user_data.get("avatar_url"),
                "profile_url": f"https://www.tiktok.com/@{user_data.get('display_name', '')}"
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
            errors.append("TikTok: Caption / Post Title is required.")
        elif len(caption) > 2200:
            errors.append(f"TikTok: Caption exceeds max length of 2200 characters (current: {len(caption)}).")

        # 2. Privacy level validation
        privacy = metadata.get("privacy", "PUBLIC_TO_EVERYONE")
        valid_levels = self.capabilities.supported_privacy_levels
        if privacy not in valid_levels:
            errors.append(f"TikTok: Invalid privacy '{privacy}'. Must be one of: {', '.join(valid_levels)}.")

        # 3. Video File Check
        if video_path and not os.path.exists(video_path):
            errors.append(f"TikTok: Video file not found at path: {video_path}")

        return (len(errors) == 0, errors)

    def publish_video(
        self,
        access_token: str,
        video_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publishes video to TikTok using official TikTok Content Posting API v2.
        1. Initialize Video Post (`/v2/post/publish/video/init/`).
        2. Upload binary bytes to the received upload_url.
        """
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found at '{video_path}'."}

        caption = metadata.get("caption", "AI Generated Short")[:2200]
        privacy = metadata.get("privacy", "PUBLIC_TO_EVERYONE")
        allow_comments = metadata.get("allow_comments", True)
        allow_duet = metadata.get("allow_duet", True)
        allow_stitch = metadata.get("allow_stitch", True)

        file_size = os.path.getsize(video_path)
        init_url = "https://open.tiktokapis.com/v2/post/publish/video/init/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }
        body = {
            "post_info": {
                "title": caption,
                "privacy_level": privacy,
                "disable_duet": not allow_duet,
                "disable_comment": not allow_comments,
                "disable_stitch": not allow_stitch
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": file_size,
                "chunk_size": file_size,
                "total_chunk_count": 1
            }
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                # 1. Initialize upload
                init_res = client.post(init_url, headers=headers, json=body)
                if init_res.status_code != 200:
                    err_msg = init_res.text
                    try:
                        err_msg = init_res.json().get("error", {}).get("message", err_msg)
                    except Exception:
                        pass
                    return {"success": False, "error": f"TikTok API Init Error ({init_res.status_code}): {err_msg}"}

                init_data = init_res.json().get("data", {})
                publish_id = init_data.get("publish_id")
                upload_url = init_data.get("upload_url")

                if not upload_url:
                    return {"success": False, "error": "TikTok API did not return upload_url."}

                # 2. Upload file bytes
                with open(video_path, "rb") as f:
                    video_bytes = f.read()

                upload_headers = {
                    "Content-Type": "video/mp4",
                    "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
                }
                upload_res = client.put(upload_url, headers=upload_headers, content=video_bytes)

                if upload_res.status_code in [200, 201]:
                    return {
                        "success": True,
                        "external_post_id": publish_id,
                        "post_url": f"https://www.tiktok.com/@creator/video/{publish_id}",
                        "error": None
                    }
                else:
                    return {"success": False, "error": f"TikTok Upload Error ({upload_res.status_code}): {upload_res.text}"}
        except Exception as e:
            return {"success": False, "error": f"TikTok Publish Exception: {str(e)}"}


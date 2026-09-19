"""
YouTube Social Provider.
Uses official Google OAuth 2.0 and YouTube Data API v3.
$0-cost official developer quota (10,000 units/day).
"""

import os
import urllib.parse
from typing import Dict, Any, List, Tuple, Optional
import httpx
from .base import SocialPlatformProvider, PlatformCapabilities


class YouTubeProvider(SocialPlatformProvider):
    """
    Official YouTube Data API v3 Integration.
    """

    AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    CHANNEL_ENDPOINT = "https://www.googleapis.com/youtube/v3/channels"

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly"
    ]

    @property
    def platform_name(self) -> str:
        return "youtube"

    @property
    def capabilities(self) -> PlatformCapabilities:
        return PlatformCapabilities(
            platform_name="youtube",
            display_name="YouTube",
            official_api_name="YouTube Data API v3",
            is_cost_free=True,
            supports_video=True,
            supports_custom_thumbnail=True,
            supports_tags=True,
            max_title_length=100,
            max_caption_length=5000,
            max_hashtags=15,
            supported_privacy_levels=["public", "unlisted", "private"],
            requires_developer_app=True,
            required_env_vars=["YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET"],
            limitations=[
                "Upload costs 1,600 quota units per video (free tier has 10,000 units/day).",
                "App in Google Cloud Console 'Testing' mode requires adding tester emails.",
                "Shorts automatically detect vertical 9:16 aspect ratio <= 60s."
            ]
        )

    def is_configured(self) -> bool:
        client_id = os.getenv("YOUTUBE_CLIENT_ID")
        client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
        return bool(client_id and client_secret)

    def get_authorization_url(self, state: str, redirect_uri: str) -> str:
        if not self.is_configured():
            raise ValueError("YouTube OAuth is not configured. Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET.")

        params = {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        return f"{self.AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("YouTube OAuth is not configured.")

        data = {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_ENDPOINT, data=data)
            if resp.status_code != 200:
                raise ValueError(f"Failed to exchange YouTube OAuth code: {resp.text}")
            payload = resp.json()
            return {
                "access_token": payload["access_token"],
                "refresh_token": payload.get("refresh_token"),
                "expires_in": payload.get("expires_in"),
                "scopes": payload.get("scope", "").split()
            }

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("YouTube OAuth is not configured.")

        data = {
            "client_id": os.getenv("YOUTUBE_CLIENT_ID"),
            "client_secret": os.getenv("YOUTUBE_CLIENT_SECRET"),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(self.TOKEN_ENDPOINT, data=data)
            if resp.status_code != 200:
                raise ValueError(f"Failed to refresh YouTube token: {resp.text}")
            payload = resp.json()
            return {
                "access_token": payload["access_token"],
                "refresh_token": payload.get("refresh_token", refresh_token),
                "expires_in": payload.get("expires_in")
            }

    def get_account_info(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"part": "snippet", "mine": "true"}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(self.CHANNEL_ENDPOINT, headers=headers, params=params)
            if resp.status_code != 200:
                raise ValueError(f"Failed to fetch YouTube channel info: {resp.text}")
            items = resp.json().get("items", [])
            if not items:
                raise ValueError("No YouTube channel found for the authenticated account.")
            ch = items[0]
            snippet = ch.get("snippet", {})
            return {
                "account_id": ch["id"],
                "account_name": snippet.get("title", "YouTube Channel"),
                "account_handle": snippet.get("customUrl", f"@{ch['id']}"),
                "avatar_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
                "profile_url": f"https://www.youtube.com/channel/{ch['id']}"
            }

    def validate_publishing_metadata(
        self,
        metadata: Dict[str, Any],
        video_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        # 1. Title validation
        title = metadata.get("title", "").strip()
        if not title:
            errors.append("YouTube: Video title is required.")
        elif len(title) > 100:
            errors.append(f"YouTube: Video title exceeds max length of 100 characters (current: {len(title)}).")

        # 2. Description validation
        description = metadata.get("description", "")
        if description and len(description) > 5000:
            errors.append(f"YouTube: Description exceeds max length of 5000 characters (current: {len(description)}).")

        # 3. Privacy status validation
        privacy = metadata.get("privacy", "public").lower()
        if privacy not in ["public", "unlisted", "private"]:
            errors.append(f"YouTube: Privacy '{privacy}' is invalid. Must be one of: public, unlisted, private.")

        # 4. Tags validation
        tags = metadata.get("tags") or metadata.get("hashtags") or []
        if isinstance(tags, list):
            total_tag_chars = sum(len(t) for t in tags)
            if total_tag_chars > 500:
                errors.append(f"YouTube: Total tags length exceeds 500 characters limit (current: {total_tag_chars}).")

        # 5. Video File Check
        if video_path and not os.path.exists(video_path):
            errors.append(f"YouTube: Video file not found at path: {video_path}")

        return (len(errors) == 0, errors)

    def publish_video(
        self,
        access_token: str,
        video_path: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Publishes video to YouTube using official YouTube Data API v3.
        Uses multipart or resumable upload protocol.
        """
        if not os.path.exists(video_path):
            return {"success": False, "error": f"Video file not found at '{video_path}'."}

        title = metadata.get("title", "AI Generated Short")[:100]
        desc = metadata.get("description", "")[:5000]
        privacy = metadata.get("privacy", "public").lower()
        tags = metadata.get("tags") or metadata.get("hashtags") or []

        upload_init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
        }
        body = {
            "snippet": {
                "title": title,
                "description": desc,
                "tags": tags if isinstance(tags, list) else [tags]
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                # 1. Initiate upload session
                init_res = client.post(upload_init_url, headers=headers, json=body)
                if init_res.status_code not in [200, 201]:
                    err_msg = init_res.text
                    try:
                        err_json = init_res.json()
                        err_msg = err_json.get("error", {}).get("message", err_msg)
                    except Exception:
                        pass
                    return {"success": False, "error": f"YouTube API Error ({init_res.status_code}): {err_msg}"}

                upload_url = init_res.headers.get("Location")
                if not upload_url:
                    return {"success": False, "error": "YouTube API did not return upload Location header."}

                # 2. Upload video binary
                with open(video_path, "rb") as video_file:
                    video_bytes = video_file.read()

                upload_res = client.put(
                    upload_url,
                    headers={"Content-Type": "video/mp4"},
                    content=video_bytes
                )

                if upload_res.status_code in [200, 201]:
                    res_data = upload_res.json()
                    video_id = res_data.get("id")
                    return {
                        "success": True,
                        "external_post_id": video_id,
                        "post_url": f"https://www.youtube.com/shorts/{video_id}",
                        "error": None
                    }
                else:
                    return {"success": False, "error": f"YouTube Video Upload Failed ({upload_res.status_code}): {upload_res.text}"}
        except Exception as e:
            return {"success": False, "error": f"YouTube Upload Exception: {str(e)}"}


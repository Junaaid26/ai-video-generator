"""
Phase 6: Reliable Background Scheduler & Multi-Platform Publisher Worker.
Uses APScheduler (in-process, $0-cost) to continuously detect due posts,
enforce strict duplicate-publishing protection, decrypt tokens, dispatch to
official APIs or Sandbox providers, and manage retries.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from api.database import SessionLocal
from api import models
from social.publisher import SocialProviderRegistry
from social.crypto import decrypt_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler_worker")

# Global BackgroundScheduler instance
scheduler: Optional[BackgroundScheduler] = None


def process_single_scheduled_post(post_id: int) -> Dict[str, Any]:
    """
    Core publishing execution unit for a single post.
    Enforces duplicate-publishing protection, file validation, credential decryption,
    and platform API execution.
    """
    db = SessionLocal()
    try:
        post = db.query(models.ScheduledPost).filter(models.ScheduledPost.id == post_id).first()
        if not post:
            return {"success": False, "error": f"ScheduledPost #{post_id} not found."}

        # Ignore if post was cancelled or already published
        if post.status == "PUBLISHED":
            return {"success": True, "message": "Post already published."}
        if post.status == "CANCELLED":
            return {"success": False, "message": "Post was cancelled."}

        logger.info(f"[Scheduler] Processing post #{post.id} (Video #{post.video_id}, Platform: {post.platform})")

        # ------------------------------------------------------------------ #
        # 1. Duplicate Publishing Protection Check
        # ------------------------------------------------------------------ #
        existing_published = db.query(models.ScheduledPost).filter(
            models.ScheduledPost.video_id == post.video_id,
            models.ScheduledPost.platform == post.platform,
            models.ScheduledPost.connected_account_id == post.connected_account_id,
            models.ScheduledPost.status == "PUBLISHED",
            models.ScheduledPost.external_post_id.isnot(None),
            models.ScheduledPost.id != post.id
        ).first()

        if existing_published:
            err = (
                f"Duplicate publishing blocked: Video #{post.video_id} has already been published to "
                f"{post.platform.capitalize()} (Post ID: {existing_published.external_post_id})."
            )
            logger.warning(f"[DuplicateGuard] {err}")
            post.status = "FAILED"
            post.error_message = err
            db.commit()
            return {"success": False, "error": err}

        # ------------------------------------------------------------------ #
        # 2. Lock State to PUBLISHING
        # ------------------------------------------------------------------ #
        post.status = "PUBLISHING"
        db.commit()

        # ------------------------------------------------------------------ #
        # 3. Validate Video & Media File
        # ------------------------------------------------------------------ #
        video = db.query(models.Video).filter(models.Video.id == post.video_id).first()
        if not video:
            post.status = "FAILED"
            post.retry_count += 1
            post.error_message = f"Video #{post.video_id} does not exist."
            db.commit()
            return {"success": False, "error": post.error_message}

        if not video.video_path or not os.path.exists(video.video_path):
            post.status = "FAILED"
            post.retry_count += 1
            post.error_message = f"Video file not found on disk at: {video.video_path}"
            db.commit()
            return {"success": False, "error": post.error_message}

        # ------------------------------------------------------------------ #
        # 4. Resolve Connected Account & Decrypt Credentials
        # ------------------------------------------------------------------ #
        account = db.query(models.SocialAccount).filter(
            models.SocialAccount.id == post.connected_account_id
        ).first()

        if not account:
            post.status = "FAILED"
            post.retry_count += 1
            post.error_message = f"Connected social account #{post.connected_account_id} not found."
            db.commit()
            return {"success": False, "error": post.error_message}

        if account.status != "ACTIVE":
            post.status = "FAILED"
            post.retry_count += 1
            post.error_message = f"Social account '{account.account_name}' is not ACTIVE (status: {account.status})."
            db.commit()
            return {"success": False, "error": post.error_message}

        # Decrypt access token securely
        try:
            raw_token = decrypt_token(account.encrypted_access_token)
            access_token = raw_token or "sandbox_token"
        except Exception as e:
            post.status = "FAILED"
            post.retry_count += 1
            post.error_message = f"Failed to decrypt credentials for {account.account_name}: {str(e)}"
            db.commit()
            return {"success": False, "error": post.error_message}

        # ------------------------------------------------------------------ #
        # 5. Dispatch to Official API or Sandbox Provider
        # ------------------------------------------------------------------ #
        provider = SocialProviderRegistry.get_provider(post.platform, use_sandbox=account.is_mock)
        meta = post.platform_metadata or {}
        # Pass account ID in metadata if needed by provider
        if "account_id" not in meta and account.account_id:
            meta["account_id"] = account.account_id

        logger.info(f"[Publishing] Uploading Video #{video.id} to {post.platform.upper()} ({'Sandbox' if account.is_mock else 'Live Official API'})...")
        result = provider.publish_video(
            access_token=access_token,
            video_path=video.video_path,
            metadata=meta
        )

        # ------------------------------------------------------------------ #
        # 6. Record Publishing Outcome
        # ------------------------------------------------------------------ #
        if result.get("success"):
            post.status = "PUBLISHED"
            post.published_at = datetime.utcnow()
            post.external_post_id = result.get("external_post_id")
            post.post_url = result.get("post_url")
            post.error_message = None
            db.commit()
            logger.info(f"[Success] Post #{post.id} PUBLISHED to {post.platform.upper()}! URL: {post.post_url}")

            # Check if all scheduled posts for this video have completed
            pending_count = db.query(models.ScheduledPost).filter(
                models.ScheduledPost.video_id == post.video_id,
                models.ScheduledPost.status.in_(["SCHEDULED", "PUBLISHING", "RETRY"])
            ).count()

            if pending_count == 0:
                video.status = models.VideoStatus.PUBLISHED
                db.commit()

            return {
                "success": True,
                "external_post_id": post.external_post_id,
                "post_url": post.post_url
            }
        else:
            post.status = "FAILED"
            post.retry_count += 1
            post.error_message = result.get("error", f"Publishing to {post.platform} failed.")
            db.commit()
            logger.error(f"[Failed] Post #{post.id} to {post.platform.upper()} FAILED: {post.error_message} (retry #{post.retry_count})")
            return {
                "success": False,
                "error": post.error_message
            }

    except Exception as e:
        logger.exception(f"[SchedulerError] Unexpected exception in post #{post_id}: {e}")
        try:
            post = db.query(models.ScheduledPost).filter(models.ScheduledPost.id == post_id).first()
            if post:
                post.status = "FAILED"
                post.retry_count += 1
                post.error_message = f"Scheduler execution error: {str(e)}"
                db.commit()
        except Exception:
            pass
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def check_and_publish_due_posts():
    """
    Interval job running every 5 seconds.
    Detects any scheduled or retry posts whose scheduled_time in UTC has arrived.
    """
    db = SessionLocal()
    try:
        now_utc = datetime.utcnow()
        due_posts = db.query(models.ScheduledPost).filter(
            models.ScheduledPost.status.in_(["SCHEDULED", "RETRY"]),
            models.ScheduledPost.scheduled_time <= now_utc
        ).order_by(models.ScheduledPost.scheduled_time.asc()).all()

        if due_posts:
            logger.info(f"[Scheduler] Found {len(due_posts)} due post(s) to publish at {now_utc.isoformat()}Z.")
            for post in due_posts:
                process_single_scheduled_post(post.id)
    except Exception as e:
        logger.exception(f"[Scheduler] Error during check_and_publish_due_posts: {e}")
    finally:
        db.close()


def start_scheduler():
    """
    Initializes and starts the APScheduler background worker.
    Called on FastAPI application startup.
    """
    global scheduler
    if scheduler and scheduler.running:
        return

    scheduler = BackgroundScheduler(timezone="UTC")
    # Trigger check every 5 seconds
    scheduler.add_job(
        func=check_and_publish_due_posts,
        trigger=IntervalTrigger(seconds=5),
        id="social_publishing_worker",
        name="Check and publish due social media posts",
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    logger.info("[Scheduler] APScheduler Background Worker STARTED (Interval: 5s, Timezone: UTC).")


def shutdown_scheduler():
    """
    Gracefully shuts down the background scheduler.
    Called on FastAPI application shutdown.
    """
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] APScheduler Background Worker SHUTDOWN.")

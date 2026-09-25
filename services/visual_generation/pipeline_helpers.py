"""Helpers for integrating visual generation into the video pipeline."""

import os
from datetime import datetime
from typing import Callable, Optional

from services.visual_generation import VisualGenerationService, build_consistency_context
from services.visual_generation.base import VisualGenerationRequest, validate_generated_image


def init_visual_status(scenes: list) -> dict:
    """Initialize visual generation status tracker."""
    return {
        "total_scenes": len(scenes),
        "current_scene": 0,
        "provider": None,
        "fallback_used": False,
        "fallback_reason": None,
        "scenes": {
            str(s.get("scene_number", i + 1)): {
                "status": "pending",
                "scene_number": s.get("scene_number", i + 1),
            }
            for i, s in enumerate(scenes)
        },
        "updated_at": datetime.utcnow().isoformat(),
    }


def update_scene_status(status: dict, scene_number: int, state: str) -> dict:
    """Update a single scene's visual generation status."""
    key = str(scene_number)
    if key not in status["scenes"]:
        status["scenes"][key] = {"scene_number": scene_number}
    status["scenes"][key]["status"] = state
    if state == "generating":
        status["current_scene"] = scene_number
    status["updated_at"] = datetime.utcnow().isoformat()
    return status


def scene_image_path(base_dir: str, scene_number: int) -> str:
    return os.path.join(base_dir, f"scene_{scene_number:03d}.png")


def scene_image_url(video_id: int, scene_number: int) -> str:
    return f"/assets/video_{video_id}/scene_{scene_number:03d}.png"


def generate_scene_visuals(
    video_id: int,
    scenes: list,
    base_dir: str,
    visual_style: str,
    db_session,
    video_model,
    scene_asset_model,
    width: int = 1080,
    height: int = 1920,
    status_callback: Optional[Callable[[dict], None]] = None,
) -> tuple[list[str], list, dict]:
    """
    Generate images for all scenes, persist SceneAsset records, update plan.

    Returns (image_paths, updated_scenes, visual_status).
    """
    os.makedirs(base_dir, exist_ok=True)
    service = VisualGenerationService()
    visual_status = init_visual_status(scenes)
    visual_status["provider"] = service.provider.name

    image_paths = []
    updated_scenes = []

    for i, scene in enumerate(scenes):
        scene_num = scene.get("scene_number", i + 1)
        update_scene_status(visual_status, scene_num, "generating")

        if status_callback:
            status_callback(visual_status)

        # Upsert SceneAsset record
        asset = (
            db_session.query(scene_asset_model)
            .filter(
                scene_asset_model.video_id == video_id,
                scene_asset_model.scene_number == scene_num,
            )
            .first()
        )
        if not asset:
            asset = scene_asset_model(
                video_id=video_id,
                scene_number=scene_num,
                status="generating",
            )
            db_session.add(asset)

        asset.status = "generating"
        asset.visual_prompt = scene.get("visual_prompt") or scene.get("visual_description", "")
        asset.updated_at = datetime.utcnow()
        db_session.commit()

        output_path = scene_image_path(base_dir, scene_num)
        consistency = build_consistency_context(scenes, scene_num)
        style = scene.get("visual_style") or visual_style

        request = VisualGenerationRequest(
            scene_number=scene_num,
            visual_prompt=scene.get("visual_prompt") or scene.get("visual_description", ""),
            environment=scene.get("environment", ""),
            characters=scene.get("characters", ""),
            objects=scene.get("objects", ""),
            camera_style=scene.get("camera_style", ""),
            visual_style=style,
            consistency_context=consistency,
            width=width,
            height=height,
            output_path=output_path,
        )

        result = service.generate_scene(request)

        scene_copy = dict(scene)
        if result.success:
            scene_copy["image_path"] = output_path
            scene_copy["image_url"] = scene_image_url(video_id, scene_num)
            scene_copy["visual_status"] = "completed"
            scene_copy["is_mock_visual"] = result.is_mock
            image_paths.append(output_path)

            asset.status = "completed"
            asset.image_path = output_path
            asset.provider = result.provider_name
            asset.is_mock = result.is_mock
            asset.metadata_json = result.metadata
            asset.error_message = None
            update_scene_status(visual_status, scene_num, "completed")
        else:
            scene_copy["visual_status"] = "failed"
            asset.status = "failed"
            asset.error_message = result.error_message
            update_scene_status(visual_status, scene_num, "failed")
            raise RuntimeError(
                f"Visual generation failed for scene {scene_num}: {result.error_message}"
            )

        updated_scenes.append(scene_copy)
        db_session.commit()

        if status_callback:
            status_callback(visual_status)

    visual_status["fallback_used"] = service.fallback_used
    visual_status["fallback_reason"] = service.fallback_reason
    visual_status["updated_at"] = datetime.utcnow().isoformat()

    return image_paths, updated_scenes, visual_status


def regenerate_single_scene(
    video_id: int,
    scene_number: int,
    scene: dict,
    all_scenes: list,
    base_dir: str,
    visual_style: str,
    db_session,
    scene_asset_model,
    width: int = 1080,
    height: int = 1920,
) -> dict:
    """Regenerate visual for a single scene."""
    service = VisualGenerationService()
    output_path = scene_image_path(base_dir, scene_number)
    consistency = build_consistency_context(all_scenes, scene_number)
    style = scene.get("visual_style") or visual_style

    asset = (
        db_session.query(scene_asset_model)
        .filter(
            scene_asset_model.video_id == video_id,
            scene_asset_model.scene_number == scene_number,
        )
        .first()
    )
    if not asset:
        asset = scene_asset_model(
            video_id=video_id,
            scene_number=scene_number,
            status="generating",
        )
        db_session.add(asset)

    asset.status = "generating"
    asset.updated_at = datetime.utcnow()
    db_session.commit()

    request = VisualGenerationRequest(
        scene_number=scene_number,
        visual_prompt=scene.get("visual_prompt") or scene.get("visual_description", ""),
        environment=scene.get("environment", ""),
        characters=scene.get("characters", ""),
        objects=scene.get("objects", ""),
        camera_style=scene.get("camera_style", ""),
        visual_style=style,
        consistency_context=consistency,
        width=width,
        height=height,
        output_path=output_path,
    )

    result = service.generate_scene(request)
    if not result.success:
        asset.status = "failed"
        asset.error_message = result.error_message
        db_session.commit()
        raise RuntimeError(result.error_message)

    asset.status = "completed"
    asset.image_path = output_path
    asset.provider = result.provider_name
    asset.is_mock = result.is_mock
    asset.metadata_json = result.metadata
    asset.error_message = None
    db_session.commit()

    updated = dict(scene)
    updated["image_path"] = output_path
    updated["image_url"] = scene_image_url(video_id, scene_number)
    updated["visual_status"] = "completed"
    updated["is_mock_visual"] = result.is_mock
    return updated

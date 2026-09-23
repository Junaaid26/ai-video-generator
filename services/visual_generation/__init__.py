"""Modular visual generation service with replaceable providers."""

import os
from typing import Callable, List, Optional

from .base import VisualGenerationProvider, VisualGenerationRequest, VisualGenerationResult
from .huggingface_generator import HuggingFaceGenerator
from .replicate_generator import ReplicateGenerator
from .local_image_generator import LocalImageGenerator
from .mock_generator import MockVisualGenerator
from .prompt_builder import build_consistency_context, build_image_prompt

# Create instances for fallback chain
_huggingface = HuggingFaceGenerator()
_replicate = ReplicateGenerator()
_local = LocalImageGenerator()
_mock = MockVisualGenerator()

__all__ = [
    "VisualGenerationService",
    "VisualGenerationProvider",
    "VisualGenerationRequest",
    "VisualGenerationResult",
    "get_visual_provider",
    "build_image_prompt",
    "build_consistency_context",
]


def get_visual_provider(force: Optional[str] = None) -> VisualGenerationProvider:
    """
    Resolve the active visual generation provider.

    VISUAL_PROVIDER env:
      - auto (default): try huggingface, then replicate, then local, then mock
      - huggingface: require Hugging Face API (free tier available)
      - replicate: require Replicate API (paid)
      - local: require local model (requires GPU)
      - mock: development mock only
    """
    mode = (force or os.getenv("VISUAL_PROVIDER", "auto")).lower().strip()

    if mode == "mock":
        return _mock
    if mode == "huggingface":
        if not _huggingface.is_available:
            raise RuntimeError(
                f"Hugging Face provider unavailable: {_huggingface.availability_message()}"
            )
        return _huggingface
    if mode == "replicate":
        if not _replicate.is_available:
            raise RuntimeError(
                f"Replicate provider unavailable: {_replicate.availability_message()}"
            )
        return _replicate
    if mode == "local":
        if not _local.is_available:
            raise RuntimeError(
                f"Local visual provider unavailable: {_local.availability_message()}"
            )
        return _local

    # auto mode: try huggingface first (free), then replicate, then local, then mock
    if _huggingface.is_available:
        print(f"[VisualGen] Using Hugging Face provider (free tier): {_huggingface.name}")
        return _huggingface
    
    if _replicate.is_available:
        print(f"[VisualGen] Hugging Face unavailable, using Replicate provider: {_replicate.name}")
        return _replicate
    
    if _local.is_available:
        print(f"[VisualGen] Hugging Face and Replicate unavailable, using local provider: {_local.name}")
        return _local
    
    print(f"[VisualGen] All providers unavailable. Using mock provider.")
    return _mock


class VisualGenerationService:
    """Orchestrates scene image generation with status tracking and fallback."""

    def __init__(self, provider: Optional[VisualGenerationProvider] = None):
        self._provider = provider
        self._fallback_used = False
        self._fallback_reason: Optional[str] = None

    @property
    def provider(self) -> VisualGenerationProvider:
        if self._provider is None:
            self._provider = get_visual_provider()
        return self._provider

    @property
    def fallback_used(self) -> bool:
        return self._fallback_used

    @property
    def fallback_reason(self) -> Optional[str]:
        return self._fallback_reason

    def generate_scene(
        self,
        request: VisualGenerationRequest,
        on_status: Optional[Callable[[int, str], None]] = None,
    ) -> VisualGenerationResult:
        """Generate a single scene image, with auto-fallback chain."""
        if on_status:
            on_status(request.scene_number, "generating")

        result = self.provider.generate(request)

        # Fallback chain: Hugging Face -> Replicate -> Local -> Mock
        if not result.success and not isinstance(self.provider, MockVisualGenerator):
            mode = os.getenv("VISUAL_PROVIDER", "auto").lower()
            if mode == "auto":
                # Try next provider in chain
                if isinstance(self.provider, HuggingFaceGenerator):
                    self._fallback_used = True
                    self._fallback_reason = result.error_message
                    print(f"[VisualGen] Hugging Face failed for scene {request.scene_number}: {result.error_message}. Trying Replicate...")
                    if _replicate.is_available:
                        self._provider = _replicate
                        result = _replicate.generate(request)
                        if result.success:
                            result.metadata["fallback_from"] = "huggingface"
                            result.metadata["fallback_reason"] = self._fallback_reason
                        else:
                            # Try local
                            self._fallback_reason = f"Hugging Face and Replicate both failed: {result.error_message}"
                            print(f"[VisualGen] Replicate also failed. Trying local...")
                            if _local.is_available:
                                self._provider = _local
                                result = _local.generate(request)
                                if result.success:
                                    result.metadata["fallback_from"] = "replicate"
                                    result.metadata["fallback_reason"] = self._fallback_reason
                                else:
                                    # Fall through to mock
                                    self._fallback_reason = f"All providers failed: {result.error_message}"
                                    print(f"[VisualGen] Local also failed. Using mock.")
                                    self._provider = _mock
                                    result = self._provider.generate(request)
                                    result.metadata["fallback_from"] = "local"
                                    result.metadata["fallback_reason"] = self._fallback_reason
                            else:
                                print(f"[VisualGen] Local unavailable. Using mock.")
                                self._provider = _mock
                                result = self._provider.generate(request)
                                result.metadata["fallback_from"] = "replicate"
                                result.metadata["fallback_reason"] = self._fallback_reason
                    else:
                        print(f"[VisualGen] Replicate unavailable. Trying local...")
                        if _local.is_available:
                            self._provider = _local
                            result = _local.generate(request)
                            if result.success:
                                result.metadata["fallback_from"] = "huggingface"
                                result.metadata["fallback_reason"] = self._fallback_reason
                            else:
                                print(f"[VisualGen] Local also failed. Using mock.")
                                self._provider = _mock
                                result = self._provider.generate(request)
                                result.metadata["fallback_from"] = "local"
                                result.metadata["fallback_reason"] = self._fallback_reason
                        else:
                            print(f"[VisualGen] Local unavailable. Using mock.")
                            self._provider = _mock
                            result = self._provider.generate(request)
                            result.metadata["fallback_from"] = "huggingface"
                            result.metadata["fallback_reason"] = self._fallback_reason
                
                elif isinstance(self.provider, ReplicateGenerator):
                    self._fallback_used = True
                    self._fallback_reason = result.error_message
                    print(f"[VisualGen] Replicate failed for scene {request.scene_number}: {result.error_message}. Trying local...")
                    if _local.is_available:
                        self._provider = _local
                        result = _local.generate(request)
                        if result.success:
                            result.metadata["fallback_from"] = "replicate"
                            result.metadata["fallback_reason"] = self._fallback_reason
                        else:
                            print(f"[VisualGen] Local also failed. Using mock.")
                            self._provider = _mock
                            result = self._provider.generate(request)
                            result.metadata["fallback_from"] = "local"
                            result.metadata["fallback_reason"] = self._fallback_reason
                    else:
                        print(f"[VisualGen] Local unavailable. Using mock.")
                        self._provider = _mock
                        result = self._provider.generate(request)
                        result.metadata["fallback_from"] = "replicate"
                        result.metadata["fallback_reason"] = self._fallback_reason
                
                elif isinstance(self.provider, LocalImageGenerator):
                    self._fallback_used = True
                    self._fallback_reason = result.error_message
                    print(f"[VisualGen] Local generation failed for scene {request.scene_number}: {result.error_message}. Falling back to mock.")
                    self._provider = _mock
                    result = self.provider.generate(request)
                    result.metadata["fallback_from"] = "local"
                    result.metadata["fallback_reason"] = self._fallback_reason

        if on_status:
            on_status(request.scene_number, "completed" if result.success else "failed")

        return result

    def generate_all_scenes(
        self,
        scenes: list,
        output_dir: str,
        visual_style: str = "realistic",
        width: int = 1080,
        height: int = 1920,
        on_status: Optional[Callable[[int, str, int], None]] = None,
    ) -> List[VisualGenerationResult]:
        """
        Generate images for all scenes.

        on_status(scene_number, status, total_scenes) callback for progress tracking.
        """
        results = []
        total = len(scenes)

        for scene in scenes:
            scene_num = scene.get("scene_number", len(results) + 1)
            if on_status:
                on_status(scene_num, "generating", total)

            consistency = build_consistency_context(scenes, scene_num)
            style = scene.get("visual_style") or visual_style

            filename = f"scene_{scene_num:03d}.png"
            output_path = os.path.join(output_dir, filename)

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

            result = self.generate_scene(request)
            results.append(result)

            if on_status:
                status = "completed" if result.success else "failed"
                on_status(scene_num, status, total)

        return results

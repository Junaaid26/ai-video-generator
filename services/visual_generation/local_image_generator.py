"""Local open-source image generation using Hugging Face diffusers."""

import os
from typing import Optional
from dotenv import load_dotenv
from PIL import Image, ImageOps

from .base import VisualGenerationProvider, VisualGenerationRequest, VisualGenerationResult, validate_generated_image
from .prompt_builder import NEGATIVE_PROMPT, build_image_prompt

# Load environment variables
load_dotenv()

# Lazy-loaded pipeline singleton
_pipeline = None
_pipeline_error: Optional[str] = None


def _get_model_id() -> str:
    return os.getenv("VISUAL_MODEL", "stabilityai/sd-turbo").strip()


def _detect_device() -> tuple[str, str]:
    """Return (device, dtype_hint) based on available hardware."""
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda", "float16"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps", "float16"
    except Exception:
        pass
    return "cpu", "float32"


def _load_pipeline():
    """Load the diffusion pipeline once and cache it."""
    global _pipeline, _pipeline_error

    if _pipeline is not None:
        return _pipeline
    if _pipeline_error is not None:
        return None

    try:
        import torch
        from diffusers import AutoPipelineForText2Image

        model_id = _get_model_id()
        device, dtype_name = _detect_device()
        dtype = torch.float16 if dtype_name == "float16" else torch.float32

        print(f"[VisualGen] Loading {model_id} on {device} ({dtype_name})...")

        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=dtype,
            variant="fp16" if dtype_name == "float16" else None,
            local_files_only=False,  # Allow download if not cached
        )
        pipe = pipe.to(device)

        if device == "cpu":
            pipe.enable_attention_slicing()

        _pipeline = pipe
        print(f"[VisualGen] Model loaded successfully on {device}.")
        return _pipeline

    except Exception as exc:
        _pipeline_error = str(exc)
        print(f"[VisualGen] Failed to load local model: {_pipeline_error}")
        return None


class LocalImageGenerator(VisualGenerationProvider):
    """
    Free local image generation using Stable Diffusion via diffusers.

    Default model: stabilityai/sd-turbo (fast 1-4 step generation).
    Requires: torch, diffusers, transformers, accelerate.
    GPU recommended (~4GB VRAM for sd-turbo fp16); CPU fallback supported but slow.
    """

    @property
    def name(self) -> str:
        return f"local:{_get_model_id()}"

    @property
    def is_available(self) -> bool:
        if _pipeline is not None:
            return True
        if _pipeline_error is not None:
            return False
        try:
            import diffusers  # noqa: F401
            import torch  # noqa: F401
            return True
        except ImportError:
            return False

    def availability_message(self) -> str:
        if _pipeline is not None:
            device, _ = _detect_device()
            return f"Model {_get_model_id()} loaded on {device}"
        if _pipeline_error:
            return f"Model load failed: {_pipeline_error}"
        try:
            import diffusers  # noqa: F401
            import torch  # noqa: F401
        except ImportError as exc:
            return f"Missing dependencies: {exc}. Install diffusers, transformers, accelerate."
        device, dtype = _detect_device()
        return f"Ready to load {_get_model_id()} on {device} ({dtype})"

    def generate(self, request: VisualGenerationRequest) -> VisualGenerationResult:
        pipe = _load_pipeline()
        if pipe is None:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message=_pipeline_error or "Local model could not be loaded",
            )

        os.makedirs(os.path.dirname(request.output_path) or ".", exist_ok=True)

        prompt = build_image_prompt(
            visual_prompt=request.visual_prompt,
            environment=request.environment,
            characters=request.characters,
            objects=request.objects,
            camera_style=request.camera_style,
            visual_style=request.visual_style,
            consistency_context=request.consistency_context,
        )

        try:
            import torch

            device, _ = _detect_device()
            num_steps = 4 if "turbo" in _get_model_id().lower() else 25
            guidance = 0.0 if "turbo" in _get_model_id().lower() else 7.5

            generator = None
            if device != "cpu":
                generator = torch.Generator(device=device).manual_seed(
                    42 + request.scene_number
                )

            # Generate at 9:16 vertical resolution
            gen_width = 576
            gen_height = 1024

            result = pipe(
                prompt=prompt,
                negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=num_steps,
                guidance_scale=guidance,
                width=gen_width,
                height=gen_height,
                generator=generator,
            )

            image = result.images[0]

            if image.size != (request.width, request.height):
                image = ImageOps.fit(image, (request.width, request.height), method=Image.LANCZOS)

            image.save(request.output_path, format="PNG", optimize=True)

            is_valid, val_err = validate_generated_image(
                request.output_path, target_width=request.width, target_height=request.height
            )
            if not is_valid:
                return VisualGenerationResult(
                    success=False,
                    output_path=request.output_path,
                    provider_name=self.name,
                    is_mock=False,
                    error_message=f"Local image validation failed: {val_err}",
                )

            return VisualGenerationResult(
                success=True,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                metadata={
                    "prompt": prompt,
                    "model": _get_model_id(),
                    "device": device,
                    "steps": num_steps,
                    "aspect_ratio": "9:16",
                },
            )

        except Exception as exc:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message=str(exc),
            )

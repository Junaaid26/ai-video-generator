"""Replicate API provider for high-quality image generation."""

import os
from typing import Optional
import requests
from dotenv import load_dotenv
from PIL import Image, ImageOps
from io import BytesIO

from .base import VisualGenerationProvider, VisualGenerationRequest, VisualGenerationResult, validate_generated_image
from .prompt_builder import NEGATIVE_PROMPT, build_image_prompt

# Load environment variables
load_dotenv()


def _get_api_key() -> Optional[str]:
    """Get Replicate API key from environment."""
    return os.getenv("REPLICATE_API_KEY")


def _get_model_id() -> str:
    """Get the Replicate model to use."""
    return os.getenv("REPLICATE_MODEL", "black-forest-labs/flux-schnell")


class ReplicateGenerator(VisualGenerationProvider):
    """
    Replicate API provider for high-quality image generation.

    Uses Replicate's hosted models for professional-quality visuals.
    Requires REPLICATE_API_KEY environment variable.
    """

    @property
    def name(self) -> str:
        return f"replicate:{_get_model_id()}"

    @property
    def is_available(self) -> bool:
        api_key = _get_api_key()
        if not api_key:
            return False
        try:
            # Basic API key validation (at least 20 characters)
            return len(api_key) > 20
        except Exception:
            return False

    def availability_message(self) -> str:
        api_key = _get_api_key()
        if not api_key:
            return "Replicate API key not found. Set REPLICATE_API_KEY environment variable."
        return f"Replicate provider ready using model: {_get_model_id()}"

    def generate(self, request: VisualGenerationRequest) -> VisualGenerationResult:
        api_key = _get_api_key()
        if not api_key:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message="Replicate API key not configured"
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
            model_id = _get_model_id()
            url = f"https://api.replicate.com/v1/models/{model_id}/predictions"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            # Enforce native 9:16 vertical aspect ratio and resolution
            gen_width = 768
            gen_height = 1344

            steps = 4 if ("flux" in model_id.lower() or "schnell" in model_id.lower()) else 25

            payload = {
                "input": {
                    "prompt": prompt,
                    "aspect_ratio": "9:16",
                    "width": gen_width,
                    "height": gen_height,
                    "negative_prompt": NEGATIVE_PROMPT,
                    "num_outputs": 1,
                    "num_inference_steps": steps,
                    "guidance_scale": 3.5,
                }
            }

            # Start prediction
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            prediction_data = response.json()

            prediction_url = prediction_data.get("urls", {}).get("get")
            if not prediction_url:
                return VisualGenerationResult(
                    success=False,
                    output_path=request.output_path,
                    provider_name=self.name,
                    is_mock=False,
                    error_message="Failed to get prediction URL from Replicate"
                )

            # Poll until complete
            import time
            max_wait = 180  # 3 minutes max wait
            start_time = time.time()

            while time.time() - start_time < max_wait:
                status_response = requests.get(prediction_url, headers=headers, timeout=10)
                status_response.raise_for_status()
                status_data = status_response.json()

                status = status_data.get("status")
                if status == "succeeded":
                    # Download the image
                    output_url = status_data.get("output", [None])[0]
                    if output_url:
                        img_response = requests.get(output_url, timeout=30)
                        img_response.raise_for_status()

                        img = Image.open(BytesIO(img_response.content))

                        # Preserve 9:16 framing without squishing/stretching
                        if img.size != (request.width, request.height):
                            img = ImageOps.fit(img, (request.width, request.height), method=Image.LANCZOS)

                        img.save(request.output_path, format="PNG", optimize=True)

                        # Validate generated image quality and properties
                        is_valid, val_err = validate_generated_image(
                            request.output_path, target_width=request.width, target_height=request.height
                        )
                        if not is_valid:
                            return VisualGenerationResult(
                                success=False,
                                output_path=request.output_path,
                                provider_name=self.name,
                                is_mock=False,
                                error_message=f"Replicate image validation failed: {val_err}"
                            )

                        return VisualGenerationResult(
                            success=True,
                            output_path=request.output_path,
                            provider_name=self.name,
                            is_mock=False,
                            metadata={
                                "prompt": prompt,
                                "model": model_id,
                                "prediction_id": prediction_data.get("id"),
                                "aspect_ratio": "9:16",
                            }
                        )
                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    return VisualGenerationResult(
                        success=False,
                        output_path=request.output_path,
                        provider_name=self.name,
                        is_mock=False,
                        error_message=f"Replicate prediction failed: {error}"
                    )

                time.sleep(2)

            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message="Replicate prediction timed out"
            )

        except requests.exceptions.RequestException as e:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message=f"Replicate API request failed: {str(e)}"
            )
        except Exception as e:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message=f"Replicate generation error: {str(e)}"
            )
"""Hugging Face Inference API provider for free image generation."""

import os
from typing import Optional
import requests
from dotenv import load_dotenv

from .base import VisualGenerationProvider, VisualGenerationRequest, VisualGenerationResult
from .prompt_builder import build_image_prompt

# Load environment variables
load_dotenv()


def _get_api_key() -> Optional[str]:
    """Get Hugging Face API key from environment."""
    return os.getenv("HUGGINGFACE_API_KEY")


def _get_model_id() -> str:
    """Get the Hugging Face model to use."""
    return os.getenv("HUGGINGFACE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")


class HuggingFaceGenerator(VisualGenerationProvider):
    """
    Hugging Face Inference API provider for free image generation.
    
    Uses Hugging Face's free inference API tier for image generation.
    Requires HUGGINGFACE_API_KEY environment variable (free tier available).
    """

    @property
    def name(self) -> str:
        return f"huggingface:{_get_model_id()}"

    @property
    def is_available(self) -> bool:
        api_key = _get_api_key()
        if not api_key:
            return False
        try:
            # Basic API key validation
            return len(api_key) > 10
        except Exception:
            return False

    def availability_message(self) -> str:
        api_key = _get_api_key()
        if not api_key:
            return "Hugging Face API key not found. Set HUGGINGFACE_API_KEY environment variable (free tier available at huggingface.co/settings/tokens)."
        return f"Hugging Face provider ready using model: {_get_model_id()}"

    def generate(self, request: VisualGenerationRequest) -> VisualGenerationResult:
        api_key = _get_api_key()
        if not api_key:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message="Hugging Face API key not configured"
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
            # Hugging Face Inference API endpoint
            model_id = _get_model_id()
            api_url = f"https://api-inference.huggingface.co/models/{model_id}"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": "text, watermark, signature, logo, username, artist name, blurry, low quality",
                    "width": min(request.width, 1024),
                    "height": min(request.height, 1024),
                    "num_inference_steps": 25,
                    "guidance_scale": 7.5,
                }
            }
            
            # Generate image
            response = requests.post(api_url, headers=headers, json=payload, timeout=120)
            
            # Handle model loading
            if response.status_code == 503:
                # Model is loading, wait and retry
                import time
                retry_after = int(response.headers.get("Retry-After", 20))
                print(f"[VisualGen] Hugging Face model loading, waiting {retry_after}s...")
                time.sleep(retry_after)
                response = requests.post(api_url, headers=headers, json=payload, timeout=120)
            
            response.raise_for_status()
            
            # Save image
            if response.headers.get("content-type", "").startswith("image/"):
                with open(request.output_path, "wb") as f:
                    f.write(response.content)
                
                # Resize if needed
                from PIL import Image
                img = Image.open(request.output_path)
                if img.size != (request.width, request.height):
                    img = img.resize((request.width, request.height), Image.LANCZOS)
                    img.save(request.output_path, format="PNG", optimize=True)
                
                return VisualGenerationResult(
                    success=True,
                    output_path=request.output_path,
                    provider_name=self.name,
                    is_mock=False,
                    metadata={
                        "prompt": prompt,
                        "model": model_id,
                    }
                )
            else:
                # JSON error response
                error_data = response.json()
                error_msg = error_data.get("error", "Unknown error")
                return VisualGenerationResult(
                    success=False,
                    output_path=request.output_path,
                    provider_name=self.name,
                    is_mock=False,
                    error_message=f"Hugging Face generation failed: {error_msg}"
                )
            
        except requests.exceptions.RequestException as e:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message=f"Hugging Face API request failed: {str(e)}"
            )
        except Exception as e:
            return VisualGenerationResult(
                success=False,
                output_path=request.output_path,
                provider_name=self.name,
                is_mock=False,
                error_message=f"Hugging Face generation error: {str(e)}"
            )
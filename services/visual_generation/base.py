"""Abstract base for pluggable visual generation providers."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Tuple
from PIL import Image


@dataclass
class VisualGenerationRequest:
    """Input for generating a single scene image."""

    scene_number: int
    visual_prompt: str
    environment: str = ""
    characters: str = ""
    objects: str = ""
    camera_style: str = ""
    visual_style: str = "realistic"
    consistency_context: str = ""
    width: int = 1080
    height: int = 1920
    output_path: str = ""


@dataclass
class VisualGenerationResult:
    """Output from a visual generation provider."""

    success: bool
    output_path: str
    provider_name: str
    is_mock: bool = False
    error_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)


def validate_generated_image(
    image_path: str,
    target_width: int = 1080,
    target_height: int = 1920,
    min_bytes: int = 1024,
) -> Tuple[bool, Optional[str]]:
    """
    Validate visual image quality and properties.
    Checks file existence, file size, opening validity, 9:16 aspect ratio, and non-blank content.
    """
    if not os.path.exists(image_path):
        return False, f"Image file does not exist: {image_path}"

    file_size = os.path.getsize(image_path)
    if file_size < min_bytes:
        return False, f"Image file size too small ({file_size} bytes < {min_bytes} bytes)"

    try:
        with Image.open(image_path) as img:
            img.verify()
        with Image.open(image_path) as img:
            width, height = img.size
            if width < 300 or height < 400:
                return False, f"Image resolution too low ({width}x{height})"

            aspect_ratio = width / float(height)
            # 9:16 vertical ratio is ~0.5625. Allow tolerance range [0.45, 0.75]
            if not (0.40 <= aspect_ratio <= 0.75):
                return False, f"Invalid aspect ratio {aspect_ratio:.2f} (expected ~0.56 for 9:16 vertical composition)"

            extrema = img.getextrema()
            if extrema:
                if isinstance(extrema[0], tuple):
                    # Multi-channel image
                    all_flat = all(min_val == max_val for min_val, max_val in extrema)
                else:
                    all_flat = (extrema[0] == extrema[1])
                if all_flat:
                    return False, "Generated image is blank/solid color"
    except Exception as e:
        return False, f"Invalid or unreadable image file: {str(e)}"

    return True, None


class VisualGenerationProvider(ABC):
    """Replaceable provider interface for scene image generation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier."""

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether this provider can run in the current environment."""

    @abstractmethod
    def generate(self, request: VisualGenerationRequest) -> VisualGenerationResult:
        """Generate a scene image and write it to request.output_path."""

    def availability_message(self) -> str:
        """Explain why the provider is or is not available."""
        return "Available" if self.is_available else "Not available"

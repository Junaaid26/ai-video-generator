"""Abstract base for pluggable visual generation providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


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

"""Development mock provider — clearly labeled, not masquerading as AI output."""

import hashlib
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .base import VisualGenerationProvider, VisualGenerationRequest, VisualGenerationResult
from .prompt_builder import build_image_prompt


def _seed_from_prompt(text: str, scene_number: int) -> random.Random:
    digest = hashlib.md5(f"{text}:{scene_number}".encode()).hexdigest()
    return random.Random(int(digest[:8], 16))


def _draw_scene_composition(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
    rng: random.Random,
    environment: str,
    characters: str,
    objects: str,
) -> None:
    """Draw procedural scene-like shapes representing environment/characters/objects."""
    # Sky / background gradient bands
    horizon = int(height * 0.45)
    for y in range(horizon):
        t = y / max(horizon, 1)
        color = (
            int(30 + 80 * t + rng.randint(-10, 10)),
            int(60 + 100 * t + rng.randint(-10, 10)),
            int(120 + 80 * t + rng.randint(-10, 10)),
        )
        draw.line([(0, y), (width, y)], fill=color)

    # Ground / environment block
    ground_color = (
        rng.randint(40, 90),
        rng.randint(70, 130),
        rng.randint(50, 100),
    )
    draw.rectangle([0, horizon, width, height], fill=ground_color)

    # Window/light source if home/office environment
    env_lower = (environment or "").lower()
    if any(k in env_lower for k in ("office", "home", "desk", "room", "indoor")):
        win_x = int(width * 0.65)
        draw.rectangle(
            [win_x, int(height * 0.08), width - 40, horizon - 20],
            fill=(200, 220, 245),
            outline=(180, 200, 220),
            width=3,
        )
        for lx in range(win_x + 20, width - 60, 40):
            draw.line([(lx, int(height * 0.08)), (lx, horizon - 20)], fill=(180, 200, 220), width=2)

    # Desk / surface for business scenes
    if any(k in env_lower for k in ("desk", "office", "work", "business", "home")):
        desk_y = int(height * 0.62)
        draw.rectangle([60, desk_y, width - 60, desk_y + 18], fill=(100, 70, 45))
        # Laptop silhouette
        lx, ly = int(width * 0.35), desk_y - 80
        draw.rectangle([lx, ly, lx + 140, ly + 90], fill=(50, 55, 65), outline=(30, 30, 35))
        draw.rectangle([lx - 10, ly + 90, lx + 150, ly + 98], fill=(70, 75, 85))

    # Character silhouette
    if characters:
        cx = int(width * 0.28)
        cy = int(height * 0.52)
        # Head
        draw.ellipse([cx - 35, cy - 120, cx + 35, cy - 50], fill=(180, 150, 120))
        # Body
        draw.rectangle([cx - 45, cy - 50, cx + 45, cy + 80], fill=(60, 90, 140))
        # Arms
        draw.rectangle([cx - 80, cy - 30, cx - 45, cy + 20], fill=(60, 90, 140))
        draw.rectangle([cx + 45, cy - 30, cx + 80, cy + 20], fill=(60, 90, 140))

    # Object shapes
    if objects:
        ox = int(width * 0.62)
        oy = int(height * 0.58)
        for i in range(min(3, max(1, len(objects.split(","))))):
            bx = ox + i * 55
            draw.rectangle([bx, oy, bx + 40, oy + 50], fill=(200, 180, 140), outline=(150, 130, 100))


class MockVisualGenerator(VisualGenerationProvider):
    """
    Development-only mock provider.

    Generates procedural scene compositions with a visible DEV MOCK watermark.
    Never silently substitutes for real AI generation in production.
    """

    @property
    def name(self) -> str:
        return "mock:dev"

    @property
    def is_available(self) -> bool:
        return True

    def availability_message(self) -> str:
        return (
            "Development mock provider active. "
            "Procedural placeholder images — NOT real AI generation. "
            "Configure VISUAL_PROVIDER=huggingface (free tier) or VISUAL_PROVIDER=local (requires diffusers) for real images."
        )

    def generate(self, request: VisualGenerationRequest) -> VisualGenerationResult:
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

        rng = _seed_from_prompt(prompt, request.scene_number)

        img = Image.new("RGB", (request.width, request.height), (20, 25, 35))
        draw = ImageDraw.Draw(img)

        _draw_scene_composition(
            draw,
            request.width,
            request.height,
            rng,
            request.environment,
            request.characters,
            request.objects,
        )

        # Subtle blur for softer mock look
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        draw = ImageDraw.Draw(img)

        # DEV MOCK watermark — always visible
        banner_h = 56
        draw.rectangle([0, 0, request.width, banner_h], fill=(180, 50, 50, 200))
        try:
            font = ImageFont.truetype("arial.ttf", 22)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            font = ImageFont.load_default()
            small_font = font

        draw.text((16, 8), "DEV MOCK — NOT AI GENERATED", fill=(255, 255, 255), font=font)
        draw.text(
            (16, 34),
            f"Scene {request.scene_number} | Enable local provider for real visuals",
            fill=(255, 220, 220),
            font=small_font,
        )

        img.save(request.output_path, format="PNG", optimize=True)

        return VisualGenerationResult(
            success=True,
            output_path=request.output_path,
            provider_name=self.name,
            is_mock=True,
            metadata={
                "prompt": prompt,
                "warning": "Development mock image — not real AI generation",
            },
        )

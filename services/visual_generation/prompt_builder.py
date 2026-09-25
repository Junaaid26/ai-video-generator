"""Build image-generation prompts from structured scene data."""

import re

VISUAL_STYLE_SUFFIXES = {
    "realistic": "realistic photography, natural lighting, high detail, photorealistic",
    "cinematic": "cinematic film still, dramatic lighting, shallow depth of field, movie scene",
    "3d": "3D render, octane render, detailed textures, studio lighting",
    "illustration": "digital illustration, artistic composition, vibrant colors",
    "anime": "anime style, cel shaded, vibrant colors, animated look",
    "minimal": "minimalist composition, clean lines, simple palette, uncluttered",
}

NEGATIVE_PROMPT = (
    "text, typography, captions, subtitles, words, letters, numbers, logos, watermarks, "
    "UI elements, social media buttons, banners, posters, signs, labels, "
    "duplicated people, duplicate subjects, extra limbs, malformed hands, distorted faces, distorted bodies, "
    "split screen, collage, comic panels, borders, frames, black bars, artificial text overlays, blurry, low quality"
)

# Text patterns to strip from visual prompts (e.g., narration quotes, text overlays)
_TEXT_CLEAN_PATTERNS = [
    r'["\'].*?["\']',  # Any quoted text like "Follow for more"
    r'(?i)\btext\s+saying\s+.*',
    r'(?i)\btext\s+overlay.*',
    r'(?i)\btitle\s+card.*',
    r'(?i)\bsubtitles?.*',
    r'(?i)\bcaptions?.*',
    r'(?i)\bfollow\s+for\s+more.*',
    r'(?i)\blike\s+and\s+subscribe.*',
    r'(?i)\bwords?\s+saying.*',
    r'(?i)\bbanner\s+saying.*',
    r'(?i)\bno\s+text.*',  # remove old "no text" appended strings since negative prompt handles it
    r'(?i)\bvertical\s+9:16\s+composition.*',
]


def clean_visual_text(text: str) -> str:
    """Strip text overlays, quoted narration, and non-visual directives."""
    if not text:
        return ""
    cleaned = text
    for pat in _TEXT_CLEAN_PATTERNS:
        cleaned = re.sub(pat, "", cleaned)
    # Remove leftover trailing/leading punctuation or spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-:")
    return cleaned


def build_image_prompt(
    visual_prompt: str,
    environment: str = "",
    characters: str = "",
    objects: str = "",
    camera_style: str = "",
    visual_style: str = "realistic",
    consistency_context: str = "",
) -> str:
    """
    Assemble a structured, high-quality prompt for diffusion models.
    Formats explicit prompt sections: SUBJECT, ACTION, ENVIRONMENT, COMPOSITION, CAMERA, LIGHTING, VISUAL STYLE, COLOR/ATMOSPHERE.
    """
    style_key = (visual_style or "realistic").lower().strip()
    style_suffix = VISUAL_STYLE_SUFFIXES.get(style_key, VISUAL_STYLE_SUFFIXES["realistic"])

    c_visual = clean_visual_text(visual_prompt)
    c_env = clean_visual_text(environment)
    c_chars = clean_visual_text(characters)
    c_objs = clean_visual_text(objects)
    c_cam = clean_visual_text(camera_style)

    # 1. Subject
    subject = c_chars or "A primary subject"
    if consistency_context:
        c_ctx = clean_visual_text(consistency_context)
        if c_ctx:
            subject = f"{subject} ({c_ctx})"

    # 2. Action
    action = c_visual if c_visual else (f"Interacting naturally with {c_objs}" if c_objs else "Engaged in the scene")

    # 3. Environment
    env = c_env or "Clean, realistic indoor/outdoor setting matching the scene context"
    if c_objs and c_objs not in env:
        env = f"{env}, featuring {c_objs}"

    # 4. Composition (Strict 9:16 Vertical Safe Area)
    composition = (
        "One primary subject, centered in middle 9:16 vertical safe zone, "
        "three-quarter or medium portrait framing, clear subject-background separation, "
        "strong visual hierarchy designed specifically for 9:16 vertical format"
    )

    # 5. Camera
    camera = c_cam or "Eye-level medium shot, sharp subject focus"

    # 6. Lighting
    lighting = "Natural soft daylight, professional balanced lighting"
    if "cinematic" in style_key:
        lighting = "Dramatic cinematic lighting, subtle lens flare, shallow depth of field"
    elif "3d" in style_key:
        lighting = "Studio octane render lighting, volumetric glow"

    # 7. Atmosphere / Color
    atmosphere = "Clean, vibrant, high-contrast, professional social media production quality"

    structured_prompt = (
        f"SUBJECT: {subject}\n"
        f"ACTION: {action}\n"
        f"ENVIRONMENT: {env}\n"
        f"COMPOSITION: {composition}\n"
        f"CAMERA: {camera}\n"
        f"LIGHTING: {lighting}\n"
        f"VISUAL STYLE: {style_suffix}\n"
        f"COLOR/ATMOSPHERE: {atmosphere}"
    )

    return structured_prompt


def build_consistency_context(scenes: list, up_to_scene: int) -> str:
    """
    Build prompt-based consistency context from prior scenes.
    Reuses character appearance, clothing, and environment cues.
    """
    if up_to_scene <= 1 or not scenes:
        return ""

    prior = scenes[: up_to_scene - 1]
    characters = []
    environments = []
    styles = []

    for scene in prior:
        chars = clean_visual_text(scene.get("characters") or "")
        env = clean_visual_text(scene.get("environment") or "")
        style = scene.get("visual_style") or ""
        if chars:
            characters.append(chars)
        if env:
            environments.append(env)
        if style:
            styles.append(style.strip())

    parts = []
    if characters:
        unique_chars = list(dict.fromkeys(characters))
        parts.append(f"Maintain consistent character appearance: {'; '.join(unique_chars[:2])}")
    if environments:
        unique_envs = list(dict.fromkeys(environments))
        parts.append(f"Consistent setting style: {unique_envs[-1]}")
    if styles:
        parts.append(f"Visual style: {styles[-1]}")

    return ". ".join(parts)

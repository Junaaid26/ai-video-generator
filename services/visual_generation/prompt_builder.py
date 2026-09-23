"""Build image-generation prompts from structured scene data."""

VISUAL_STYLE_SUFFIXES = {
    "realistic": "realistic photography, natural lighting, high detail, photorealistic",
    "cinematic": "cinematic film still, dramatic lighting, shallow depth of field, movie scene",
    "3d": "3D render, octane render, detailed textures, studio lighting",
    "illustration": "digital illustration, artistic composition, vibrant colors",
    "anime": "anime style, cel shaded, vibrant colors, animated look",
    "minimal": "minimalist composition, clean lines, simple palette, uncluttered",
}

NEGATIVE_PROMPT = (
    "text, words, letters, watermark, logo, caption, subtitle, typography, "
    "banner, title card, meme text, blurry, low quality, distorted faces"
)


def build_image_prompt(
    visual_prompt: str,
    environment: str = "",
    characters: str = "",
    objects: str = "",
    camera_style: str = "",
    visual_style: str = "realistic",
    consistency_context: str = "",
) -> str:
    """Assemble a full diffusion prompt from structured scene fields."""
    style_key = (visual_style or "realistic").lower().strip()
    style_suffix = VISUAL_STYLE_SUFFIXES.get(style_key, VISUAL_STYLE_SUFFIXES["realistic"])

    parts = []
    if consistency_context:
        parts.append(consistency_context.strip())

    if visual_prompt:
        parts.append(visual_prompt.strip())
    else:
        scene_bits = [b for b in [environment, characters, objects] if b]
        parts.append(", ".join(scene_bits) if scene_bits else "detailed scene")

    if environment and environment not in visual_prompt:
        parts.append(f"Environment: {environment.strip()}")
    if characters and characters not in visual_prompt:
        parts.append(f"Characters: {characters.strip()}")
    if objects and objects not in visual_prompt:
        parts.append(f"Objects: {objects.strip()}")
    if camera_style:
        parts.append(f"Camera: {camera_style.strip()}")

    parts.append(style_suffix)
    parts.append("vertical composition 9:16 portrait, no text on image")

    return ", ".join(p for p in parts if p)


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
        chars = scene.get("characters") or ""
        env = scene.get("environment") or ""
        style = scene.get("visual_style") or ""
        if chars:
            characters.append(chars.strip())
        if env:
            environments.append(env.strip())
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

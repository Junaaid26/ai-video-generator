"""Build image-generation prompts from structured scene data with topic-locking and validation."""

import re
from typing import Tuple, Optional, List

VISUAL_STYLE_SUFFIXES = {
    "realistic": "realistic photography, natural lighting, high detail, photorealistic",
    "cinematic": "cinematic film still, dramatic lighting, shallow depth of field, movie scene",
    "3d": "3D render, octane render, detailed textures, studio lighting",
    "illustration": "digital illustration, artistic composition, vibrant colors",
    "anime": "anime style, cel shaded, vibrant colors, animated look",
    "minimal": "minimalist composition, clean lines, simple palette, uncluttered",
}

BASE_NEGATIVE_PROMPT = (
    "text, typography, captions, subtitles, words, letters, numbers, logos, watermarks, "
    "UI elements, social media buttons, banners, posters, signs, labels, "
    "duplicated people, duplicate subjects, extra limbs, malformed hands, distorted faces, distorted bodies, "
    "split screen, collage, comic panels, borders, frames, black bars, artificial text overlays, blurry, low quality"
)

NEGATIVE_PROMPT = BASE_NEGATIVE_PROMPT

# Keywords that indicate tech / AI / computing domain
TECH_TOPIC_KEYWORDS = {
    "ai", "artificial intelligence", "machine learning", "neural network", "deep learning",
    "transformer", "llm", "chatgpt", "gpt", "algorithm", "software", "code", "coding",
    "programming", "python", "javascript", "computer", "computing", "database", "sql",
    "cyber", "hardware", "microchip", "semiconductor", "server", "cloud computing"
}

# Generic / tech fallback keywords that MUST NOT appear in non-tech visual prompts
BANNED_NONTECH_FALLBACKS = [
    "technical schematic", "throughput calibration", "boundary constraint", "interface hub",
    "data conduit", "server room", "circuit board", "diagnostic monitor", "generic ai background",
    "futuristic interface", "silicon chip", "neural network lattice", "token arrays",
    "glowing glyphs", "holographic document", "statistical weight", "probability trees",
    "memory bus", "streamline air currents", "downwash deflection", "robotic masthead"
]

GENERIC_PLACEHOLDER_VISUALS = [
    "person at laptop", "sitting at desk", "generic ai background", "smiling at camera",
    "cinematic educational technology scene", "modern technology scene", "digital interface",
    "futuristic technology", "ai visualization", "generic stock", "concept illustration"
]

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
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-:")
    return cleaned


def is_tech_domain(topic: str, claim: str = "") -> bool:
    """Detect if the topic or claim is genuinely within the tech / computing / AI domain."""
    combined = f"{topic} {claim}".lower()
    for kw in TECH_TOPIC_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', combined):
            return True
    return False


def build_dynamic_negative_prompt(
    topic: str = "",
    claim: str = "",
    visual_style: str = "realistic"
) -> str:
    """
    Build a dynamic negative prompt that suppresses domain-irrelevant imagery.
    Suppresses AI, computers, digital screens, and robots for non-tech subjects.
    """
    neg_parts = [BASE_NEGATIVE_PROMPT]

    # If the topic is NOT tech/AI, suppress futuristic technology and digital screens
    if not is_tech_domain(topic, claim):
        neg_parts.append(
            "artificial intelligence, robots, computers, futuristic interfaces, "
            "server rooms, circuit boards, digital screens, sci-fi technology, "
            "generic corporate technology, holographic HUD, wireframe, digital data lines, matrix code, cyber"
        )

    # Style-specific suppressions
    style_key = (visual_style or "realistic").lower().strip()
    if style_key == "realistic":
        neg_parts.append("cartoon, anime, 3d render, CGI, drawing, sketch, illustration, painting, render")

    # History-specific suppressions
    hist_keywords = ["ancient", "history", "historical", "archaeology", "egypt", "rome", "greece", "medieval", "wwii", "world war", "century", "dynasty"]
    if any(re.search(r'\b' + re.escape(kw) + r'\b', f"{topic} {claim}".lower()) for kw in hist_keywords):
        neg_parts.append("modern buildings, smartphones, modern cars, modern clothing, modern electronics, electricity cables, airplanes")

    return ", ".join(neg_parts)


def validate_visual_prompt_grounding(
    topic: str,
    claim: str,
    narration: str,
    visual_prompt: str,
) -> Tuple[bool, Optional[str]]:
    """
    Validates that a visual prompt is strictly grounded in the topic and claim.
    Returns (is_valid, failure_reason).
    """
    if not visual_prompt or len(visual_prompt.strip()) < 20:
        return False, "Visual prompt is too brief or empty"

    vp_lower = visual_prompt.lower()

    # 1. Check for generic placeholder prompts
    for placeholder in GENERIC_PLACEHOLDER_VISUALS:
        if placeholder in vp_lower:
            return False, f"Visual prompt contains generic placeholder: '{placeholder}'"

    # 2. Check for banned tech fallbacks when topic is non-technical
    if not is_tech_domain(topic, claim):
        for fallback in BANNED_NONTECH_FALLBACKS:
            if fallback in vp_lower:
                return False, f"Non-tech topic contains banned technology fallback: '{fallback}'"

    return True, None


def regenerate_grounded_visual_prompt(
    topic: str,
    claim: str,
    narration: str = "",
    visual_style: str = "realistic",
) -> str:
    """
    Regenerates a topic-locked, factually grounded visual prompt from the topic, claim, and narration.
    Guarantees no generic tech buzzwords.
    """
    clean_topic = clean_visual_text(topic)
    clean_claim = clean_visual_text(claim)
    clean_narr = clean_visual_text(narration)

    # Extract subject essence
    subject_core = clean_claim or clean_narr[:80] or clean_topic
    style_suffix = VISUAL_STYLE_SUFFIXES.get(visual_style.lower(), VISUAL_STYLE_SUFFIXES["realistic"])

    # Build grounded documentary prompt
    prompt = (
        f"Photorealistic documentary view of {subject_core}, "
        f"showing authentic real-world details of {clean_topic}, "
        f"natural lighting, rich atmospheric depth, highly detailed, {style_suffix}, vertical 9:16 composition"
    )
    return prompt


def build_image_prompt(
    visual_prompt: str,
    environment: str = "",
    characters: str = "",
    objects: str = "",
    camera_style: str = "",
    visual_style: str = "realistic",
    consistency_context: str = "",
    topic: str = "",
    claim: str = "",
    narration: str = "",
) -> str:
    """
    Assemble a structured, high-quality prompt for diffusion models.
    Applies topic-lock and ensures no generic tech leakage into non-tech scenes.
    """
    style_key = (visual_style or "realistic").lower().strip()
    style_suffix = VISUAL_STYLE_SUFFIXES.get(style_key, VISUAL_STYLE_SUFFIXES["realistic"])

    # Grounding check & auto-repair if visual_prompt is generic or polluted
    is_valid, _ = validate_visual_prompt_grounding(topic, claim, narration, visual_prompt)
    if not is_valid:
        visual_prompt = regenerate_grounded_visual_prompt(topic, claim, narration, visual_style)

    c_visual = clean_visual_text(visual_prompt)
    c_env = clean_visual_text(environment)
    c_chars = clean_visual_text(characters)
    c_objs = clean_visual_text(objects)
    c_cam = clean_visual_text(camera_style)
    clean_claim = clean_visual_text(claim)

    # Clean generic fallback characters/environments
    if c_chars in ["Primary subject of study", "A primary subject", "System structural blueprint and telemetry monitors", "Adaptive calibration feedback loop", "Automated boundary safeguard system", "Synchronized interface connectors", "Advanced evolutionary architecture model"]:
        c_chars = clean_claim or topic or ""

    if c_env in ["Architectural schematic analysis chamber", "High-precision engineering testing facility", "System safety control and monitoring room", "Universal integration hub and protocol terminal", "Technology progression and optimization laboratory", "Clean technical educational setting"]:
        c_env = f"Authentic natural setting illustrating {topic or claim}"

    # 1. Subject
    subject = c_chars or (clean_claim or topic or "The featured subject")
    if consistency_context:
        c_ctx = clean_visual_text(consistency_context)
        if c_ctx:
            subject = f"{subject} ({c_ctx})"

    # 2. Action
    action = c_visual if c_visual else (f"Detailed view of {c_objs}" if c_objs else f"Authentic demonstration of {subject}")

    # 3. Environment
    env = c_env or f"Natural realistic environment suited to {topic or subject}"
    if c_objs and c_objs not in env and not any(gen in c_objs.lower() for gen in ["diagnostic tools", "interface ports", "threshold monitors"]):
        env = f"{env}, featuring {c_objs}"

    # 4. Composition (Strict 9:16 Vertical Safe Area)
    composition = (
        "One primary subject, centered in middle 9:16 vertical safe zone, "
        "clear subject-background separation, strong visual hierarchy designed for 9:16 vertical format"
    )

    # 5. Camera
    camera = c_cam or "Eye-level medium shot, sharp focus, natural perspective"

    # 6. Lighting
    lighting = "Natural soft daylight, professional balanced lighting"
    if "cinematic" in style_key:
        lighting = "Dramatic cinematic lighting, subtle atmospheric depth, shallow depth of field"
    elif "3d" in style_key:
        lighting = "Studio render lighting, volumetric glow"

    # 7. Atmosphere / Color
    atmosphere = "Vibrant, high-contrast, professional documentary production quality"

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
        if chars and chars not in ["Primary subject of study", "A primary subject"]:
            characters.append(chars)
        if env and not env.startswith("Architectural"):
            environments.append(env)
        if style:
            styles.append(style.strip())

    parts = []
    if characters:
        unique_chars = list(dict.fromkeys(characters))
        parts.append(f"Maintain consistent subject appearance: {'; '.join(unique_chars[:2])}")
    if environments:
        unique_envs = list(dict.fromkeys(environments))
        parts.append(f"Consistent setting style: {unique_envs[-1]}")
    if styles:
        parts.append(f"Visual style: {styles[-1]}")

    return ". ".join(parts)

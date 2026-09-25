import os
import json
import re
import time
from typing import Optional
from dotenv import load_dotenv
from api.schemas import VideoPlan, Scene

load_dotenv()

SCENE_JSON_SCHEMA = """
{
  "title": "Short catchy title",
  "short_description": "1-2 sentence description",
  "complete_narration": "Full text narration combining all scenes",
  "scenes": [
    {
      "scene_number": 1,
      "duration": 6,
      "scene_duration": "6s",
      "narration": "Narration for this specific scene",
      "visual_prompt": "Detailed description of what appears ON SCREEN — environment, people, objects, action. NO text overlays.",
      "environment": "Specific location/setting e.g. small home office with window light",
      "characters": "Who appears e.g. young entrepreneur, mid-20s, casual sweater",
      "objects": "Key props e.g. laptop, notebook, product packages on desk",
      "camera_style": "e.g. medium shot, eye level, natural window lighting",
      "visual_style": "realistic"
    }
  ],
  "suggested_background_music": "e.g. upbeat lofi beats",
  "caption": "Social media caption with call to action",
  "hashtags": ["#tag1", "#tag2"]
}
"""

SCENE_PLANNER_INSTRUCTIONS = """
You are an expert social media video producer and visual scene planner.

CRITICAL RULES FOR SCENES:
1. Each scene MUST describe a DISTINCT, SPECIFIC VISUAL SCENE — subject, action, environment, and camera angle.
2. visual_prompt MUST describe strictly what the camera captures. NEVER include text overlays, titles, captions, or quotes like "Follow for more".
3. NEVER include plain colored backgrounds, logos, words, or title cards in visual_prompt.
4. Ensure scene diversity: across 5 scenes, use different camera angles (wide shot, medium shot, close-up), actions, and lighting.
5. For 30-second videos, create AT LEAST 5 scenes. For 15-second videos, at least 3 scenes.
6. Maintain character visual consistency across scenes (hair, age, clothing style).
7. duration is in seconds (integer). scene_duration is the same as a string like "6s".
"""


def _normalize_scene(raw: dict, default_style: str = "realistic") -> Scene:
    """Normalize LLM output to consistent Scene schema."""
    scene_num = raw.get("scene_number", 1)
    duration = raw.get("duration")
    scene_dur = raw.get("scene_duration")

    if duration is None and scene_dur:
        match = re.search(r"\d+", str(scene_dur))
        duration = int(match.group()) if match else 5
    elif duration is None:
        duration = 5
        scene_dur = f"{duration}s"
    elif not scene_dur:
        scene_dur = f"{duration}s"

    visual_prompt = raw.get("visual_prompt") or raw.get("visual_description") or ""
    environment = raw.get("environment", "")
    characters = raw.get("characters", "")
    objects = raw.get("objects", "")
    camera_style = raw.get("camera_style", "medium shot, eye level")
    visual_style = raw.get("visual_style") or default_style

    return Scene(
        scene_number=scene_num,
        duration=int(duration),
        scene_duration=scene_dur,
        narration=raw.get("narration", ""),
        visual_prompt=visual_prompt,
        environment=environment,
        characters=characters,
        objects=objects,
        camera_style=camera_style,
        visual_style=visual_style,
        visual_description=visual_prompt,
    )


def generate_video_plan_groq(
    prompt: str, duration: str, language: str, style: str,
    target_platform: str, groq_api_key: str, visual_style: str = "realistic"
) -> Optional[VideoPlan]:
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_api_key
        )

        system_prompt = f"""{SCENE_PLANNER_INSTRUCTIONS}

Create an engaging video script and DETAILED visual scene breakdown strictly as JSON matching this schema:
{SCENE_JSON_SCHEMA}

Parameters:
Target Duration: {duration}
Language: {language}
Style/Tone: {style}
Target Platform: {target_platform}
Default Visual Style: {visual_style}
Return ONLY valid JSON.
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a structured video plan with rich visual scenes for: {prompt}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        content = response.choices[0].message.content
        if content:
            data = json.loads(content)
            scenes = [_normalize_scene(s, visual_style) for s in data.get("scenes", [])]
            data["scenes"] = [s.model_dump() for s in scenes]
            return VideoPlan.model_validate(data)
    except Exception as e:
        print(f"[Groq LLM Warning] {e}")
        return None
    return None


def generate_video_plan_gemini(
    prompt: str, duration: str, language: str, style: str,
    target_platform: str, gemini_api_key: str, visual_style: str = "realistic"
) -> Optional[VideoPlan]:
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_api_key)
        system_prompt = f"""{SCENE_PLANNER_INSTRUCTIONS}

Target Duration: {duration}
Language: {language}
Style/Tone: {style}
Target Platform: {target_platform}
Default Visual Style: {visual_style}
Output strictly a JSON object matching the requested schema with rich visual_prompt fields.
"""
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"{system_prompt}\n\nUser Request: {prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VideoPlan,
            ),
        )
        if response and getattr(response, "text", None):
            data = json.loads(response.text)
            scenes = [_normalize_scene(s, visual_style) for s in data.get("scenes", [])]
            data["scenes"] = [s.model_dump() for s in scenes]
            return VideoPlan.model_validate(data)
    except Exception as e:
        print(f"[Gemini LLM Warning] {e}")
        return None
    return None


def generate_video_plan_fallback(
    prompt: str, duration: str, language: str, style: str,
    target_platform: str, visual_style: str = "realistic"
) -> VideoPlan:
    """
    Guaranteed fallback with rich visual scene descriptions for image generation.
    """
    cleaned_prompt = prompt.strip().rstrip(".")
    words = cleaned_prompt.split()
    short_title = " ".join(words[:8]).title() if len(words) > 1 else f"{cleaned_prompt.title()} Video"

    if "15" in duration:
        num_scenes = 3
        per_scene_sec = 5
    elif "30" in duration or "60" in duration:
        num_scenes = 5
        per_scene_sec = 6
    elif "3" in duration:
        num_scenes = 6
        per_scene_sec = 10
    else:
        num_scenes = 5
        per_scene_sec = 5

    # Detect topic themes for richer visuals
    topic_lower = cleaned_prompt.lower()
    is_business = any(k in topic_lower for k in ("business", "entrepreneur", "startup", "home", "side hustle", "small business"))
    is_tech = any(k in topic_lower for k in ("software", "code", "tech", "programming", "engineer"))
    is_health = any(k in topic_lower for k in ("health", "fitness", "workout", "diet", "wellness"))

    character_desc = "young professional, mid-20s, smart casual clothing, friendly expression"
    if is_business:
        character_desc = "young entrepreneur, mid-20s, casual sweater and jeans, focused expression"
    elif is_tech:
        character_desc = "software developer, late 20s, hoodie and glasses, confident posture"
    elif is_health:
        character_desc = "fit wellness coach, early 30s, athletic wear, energetic demeanor"

    scenes = []
    narrations = []

    if is_business:
        scene_specs = [
            {
                "narration": f"Starting a small business from home is more achievable than ever. Here is how to begin.",
                "visual_prompt": f"A {character_desc} working at a desk inside a small home office, laptop open, notebook and product packages on the desk, shelves in the background, natural window lighting, realistic photography, vertical composition, no text",
                "environment": "cozy home office with desk, shelves, and window",
                "characters": character_desc,
                "objects": "laptop, notebook, pen, small product boxes, coffee mug",
                "camera_style": "medium shot, eye level, warm natural window light",
            },
            {
                "narration": "First, identify a problem you can solve and validate your idea with real people.",
                "visual_prompt": f"The same {character_desc} on a video call at the home desk, sticky notes on the wall with ideas, smartphone showing messages, engaged expression, realistic photography, no text",
                "environment": "same home office, sticky notes on wall",
                "characters": character_desc,
                "objects": "laptop, smartphone, sticky notes, whiteboard markers",
                "camera_style": "over-the-shoulder shot showing laptop screen glow",
            },
            {
                "narration": "Set up a dedicated workspace and organize your tools for productivity.",
                "visual_prompt": f"Close-up of organized desk setup: laptop, label printer, shipping supplies, product samples neatly arranged, hands arranging packages, soft daylight, realistic photography, no text",
                "environment": "organized home workspace corner",
                "characters": f"hands of {character_desc}",
                "objects": "shipping boxes, tape, product samples, calendar planner",
                "camera_style": "close-up, shallow depth of field",
            },
            {
                "narration": "Build your online presence and start reaching customers on social media.",
                "visual_prompt": f"The same {character_desc} filming content with a ring light and smartphone on a tripod in the home office, product displayed on desk, social media aesthetic setup, realistic photography, no text",
                "environment": "home office content creation corner with ring light",
                "characters": character_desc,
                "objects": "smartphone on tripod, ring light, product samples",
                "camera_style": "wide medium shot, bright even lighting",
            },
            {
                "narration": f"Take action today — your home business journey starts with one small step. Follow for more tips!",
                "visual_prompt": f"The same {character_desc} smiling while sealing a shipping package at the desk, completed orders stacked nearby, golden hour light through window, hopeful mood, realistic photography, no text",
                "environment": "same home office, golden hour lighting",
                "characters": character_desc,
                "objects": "shipping packages, tape, thank-you cards",
                "camera_style": "medium close-up, warm golden hour light",
            },
        ]
    else:
        scene_specs = [
            {
                "narration": f"Did you know about {cleaned_prompt}? Here is what you need to know.",
                "visual_prompt": f"{character_desc} in a modern setting related to {cleaned_prompt}, engaging with relevant objects, cinematic lighting, realistic photography, vertical composition, no text",
                "environment": f"modern setting related to {cleaned_prompt}",
                "characters": character_desc,
                "objects": "relevant props for the topic",
                "camera_style": "medium shot, eye level",
            },
            {
                "narration": f"Let us explore the key concepts behind {cleaned_prompt}.",
                "visual_prompt": f"Same {character_desc} demonstrating or interacting with topic-related items, detailed environment, natural lighting, realistic photography, no text",
                "environment": "detailed environment matching the topic",
                "characters": character_desc,
                "objects": "topic-related tools and materials",
                "camera_style": "medium wide shot",
            },
            {
                "narration": "Here is a practical approach you can apply immediately.",
                "visual_prompt": f"Close-up of hands working with topic-related objects, {character_desc} partially visible, shallow depth of field, realistic photography, no text",
                "environment": "workspace related to the topic",
                "characters": f"hands of {character_desc}",
                "objects": "practical tools for the topic",
                "camera_style": "close-up, shallow depth of field",
            },
            {
                "narration": "Most people overlook this important detail.",
                "visual_prompt": f"{character_desc} showing surprise or insight while examining something related to {cleaned_prompt}, dramatic side lighting, realistic photography, no text",
                "environment": "same setting with moodier lighting",
                "characters": character_desc,
                "objects": "key prop highlighting the insight",
                "camera_style": "medium close-up, dramatic side light",
            },
            {
                "narration": f"Follow for more expert insights on {cleaned_prompt} and share your thoughts below!",
                "visual_prompt": f"{character_desc} smiling confidently in the same environment, completed work visible, warm inviting lighting, realistic photography, no text",
                "environment": "same consistent environment, warm lighting",
                "characters": character_desc,
                "objects": "completed project or results",
                "camera_style": "medium shot, warm inviting light",
            },
        ]

    for i, spec in enumerate(scene_specs[:num_scenes]):
        scene_num = i + 1
        scenes.append(Scene(
            scene_number=scene_num,
            duration=per_scene_sec,
            scene_duration=f"{per_scene_sec}s",
            narration=spec["narration"],
            visual_prompt=spec["visual_prompt"],
            environment=spec["environment"],
            characters=spec["characters"],
            objects=spec["objects"],
            camera_style=spec["camera_style"],
            visual_style=visual_style,
            visual_description=spec["visual_prompt"],
        ))
        narrations.append(spec["narration"])

    complete_narration = " ".join(narrations)

    hashtags = [
        f"#{word.lower().replace('#', '').replace(',', '')}"
        for word in words if len(word) > 3 and word.isalnum()
    ][:4]
    if not hashtags:
        hashtags = ["#video", "#viral", "#educational", "#trending"]
    else:
        hashtags.extend(["#trending", "#viral"])
        hashtags = list(dict.fromkeys(hashtags))[:5]

    return VideoPlan(
        title=short_title,
        short_description=f"An engaging {style.lower()} video explaining {cleaned_prompt} formatted for {target_platform}.",
        complete_narration=complete_narration,
        scenes=scenes,
        suggested_background_music="Upbeat modern ambient electronic background track",
        caption=f"Learn everything you need to know about {cleaned_prompt}! Drop your thoughts in the comments.",
        hashtags=hashtags
    )


def generate_video_plan(
    prompt: str,
    duration: str = "30-60 seconds",
    language: str = "English",
    style: str = "Standard",
    target_platform: str = "TikTok",
    visual_style: str = "realistic",
) -> VideoPlan:
    """
    Primary video plan generator with rich visual scene planning.
    Waterfall: Groq -> Gemini -> Intelligent fallback.
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key and groq_key != "your_groq_api_key_here":
        plan = generate_video_plan_groq(
            prompt, duration, language, style, target_platform, groq_key, visual_style
        )
        if plan:
            return plan

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        plan = generate_video_plan_gemini(
            prompt, duration, language, style, target_platform, gemini_key, visual_style
        )
        if plan:
            return plan

    return generate_video_plan_fallback(
        prompt, duration, language, style, target_platform, visual_style
    )

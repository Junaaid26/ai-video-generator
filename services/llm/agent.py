import os
import json
import re
import time
from typing import Optional
from dotenv import load_dotenv
from api.schemas import VideoPlan, Scene

load_dotenv()

def generate_video_plan_groq(prompt: str, duration: str, language: str, style: str, target_platform: str, groq_api_key: str) -> Optional[VideoPlan]:
    """
    Attempts to generate a structured VideoPlan using Groq's OpenAI-compatible API.
    """
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_api_key
        )
        
        system_prompt = f"""You are an expert social media video producer.
Create an engaging video script and scene breakdown strictly as JSON matching this schema:
{{
  "title": "Short catchy title",
  "short_description": "1-2 sentence description",
  "complete_narration": "Full text narration combining all scenes",
  "scenes": [
    {{
      "scene_number": 1,
      "scene_duration": "5s",
      "narration": "Narration for this specific scene",
      "visual_description": "Visual scene description"
    }}
  ],
  "suggested_background_music": "e.g. upbeat lofi beats",
  "caption": "Social media caption with call to action",
  "hashtags": ["#tag1", "#tag2"]
}}

Parameters:
Target Duration: {duration}
Language: {language}
Style/Tone: {style}
Target Platform: {target_platform}
Return ONLY valid JSON.
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create a structured video plan for: {prompt}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        content = response.choices[0].message.content
        if content:
            return VideoPlan.model_validate_json(content)
    except Exception as e:
        print(f"[Groq LLM Warning] {e}")
        return None
    return None


def generate_video_plan_gemini(prompt: str, duration: str, language: str, style: str, target_platform: str, gemini_api_key: str) -> Optional[VideoPlan]:
    """
    Attempts to generate a structured VideoPlan using Google GenAI (Gemini).
    """
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_api_key)
        system_prompt = f"""You are an expert social media video producer.
Target Duration: {duration}
Language: {language}
Style/Tone: {style}
Target Platform: {target_platform}
Output strictly a JSON object matching the requested schema.
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
            return VideoPlan.model_validate_json(response.text)
    except Exception as e:
        print(f"[Gemini LLM Warning] {e}")
        return None
    return None


def generate_video_plan_fallback(prompt: str, duration: str, language: str, style: str, target_platform: str) -> VideoPlan:
    """
    Guaranteed fallback that generates a realistic, high-quality structured video plan
    tailored to the user prompt and options when external API quotas are exhausted.
    """
    # Clean up topic words for title
    cleaned_prompt = prompt.strip().rstrip(".")
    words = cleaned_prompt.split()
    short_title = " ".join(words[:6]).title() if len(words) > 1 else f"{cleaned_prompt.title()} Video"
    
    # Parse requested duration to determine scene count
    scene_dur = 4
    if "15" in duration:
        total_seconds = 15
        num_scenes = 3
    elif "30" in duration or "60" in duration:
        total_seconds = 30
        num_scenes = 4
    elif "3" in duration:
        total_seconds = 60
        num_scenes = 5
    else:
        total_seconds = 20
        num_scenes = 4

    per_scene_sec = max(3, total_seconds // num_scenes)

    scenes = []
    narrations = []

    # Scene 1: Hook
    hook_narration = f"Did you know about {cleaned_prompt}? Here is what you need to know."
    scenes.append(Scene(
        scene_number=1,
        scene_duration=f"{per_scene_sec}s",
        narration=hook_narration,
        visual_description=f"Dramatic hook showcasing {cleaned_prompt} with bold dynamic title text"
    ))
    narrations.append(hook_narration)

    # Middle scenes: Key points
    key_points = [
        ("First key insight", f"Exploring core elements and practical applications of {cleaned_prompt}"),
        ("Actionable strategy", f"Demonstrating proven steps and immediate daily benefits"),
        ("Surprising perspective", f"Revealing crucial facts that most people overlook"),
        ("Key takeaway", f"Summarizing the high-impact summary and real results")
    ]

    for i in range(2, num_scenes):
        idx = (i - 2) % len(key_points)
        title_pt, desc_pt = key_points[idx]
        pt_narration = f"Point {i - 1}: {desc_pt}."
        scenes.append(Scene(
            scene_number=i,
            scene_duration=f"{per_scene_sec}s",
            narration=pt_narration,
            visual_description=f"Clean animated graphic illustrating {title_pt} and {desc_pt}"
        ))
        narrations.append(pt_narration)

    # Final scene: Call to action
    cta_narration = f"Follow for more expert insights on {cleaned_prompt} and share your thoughts below!"
    scenes.append(Scene(
        scene_number=num_scenes,
        scene_duration=f"{per_scene_sec}s",
        narration=cta_narration,
        visual_description=f"Engaging outro card with subscribe, like, and comment call to action"
    ))
    narrations.append(cta_narration)

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
        caption=f"Learn everything you need to know about {cleaned_prompt}! 🔥 Drop your thoughts in the comments.",
        hashtags=hashtags
    )


def generate_video_plan(prompt: str, duration: str = "30-60 seconds", language: str = "English", style: str = "Standard", target_platform: str = "TikTok") -> VideoPlan:
    """
    Primary video plan generator.
    Waterfall strategy:
    1. Groq API (fast, high free-tier allowance) if GROQ_API_KEY is available.
    2. Gemini API if GEMINI_API_KEY is available and active.
    3. Intelligent structured fallback generator (guarantees pipeline continuity).
    """
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    if groq_key and groq_key != "your_groq_api_key_here":
        plan = generate_video_plan_groq(prompt, duration, language, style, target_platform, groq_key)
        if plan:
            return plan

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        plan = generate_video_plan_gemini(prompt, duration, language, style, target_platform, gemini_key)
        if plan:
            return plan

    # Robust fallback
    return generate_video_plan_fallback(prompt, duration, language, style, target_platform)

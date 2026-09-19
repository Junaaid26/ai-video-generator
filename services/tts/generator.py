import asyncio
import edge_tts
import os

async def _generate_audio(text: str, output_path: str, voice: str = "en-US-ChristopherNeural") -> str:
    """Async inner function to generate TTS."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path

def generate_voiceover(text: str, output_path: str, voice: str = "en-US-ChristopherNeural") -> str:
    """
    Generates a voiceover from text using edge-tts and saves it to output_path.
    Runs the asyncio loop synchronously for easier integration.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    asyncio.run(_generate_audio(text, output_path, voice))
    return output_path

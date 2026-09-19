import asyncio
import os
import threading

import edge_tts


async def _generate_audio(text: str, output_path: str, voice: str = "en-US-ChristopherNeural") -> str:
    """Async inner function to generate TTS."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


def generate_voiceover(text: str, output_path: str, voice: str = "en-US-ChristopherNeural") -> str:
    """
    Generates a voiceover from text using edge-tts and saves it to output_path.
    Works both from normal sync code and from async/FastAPI contexts.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_generate_audio(text, output_path, voice))
        return output_path

    result = {}

    def _runner():
        result["path"] = asyncio.run(_generate_audio(text, output_path, voice))

    thread = threading.Thread(target=_runner, daemon=True)
    thread.start()
    thread.join()
    return result.get("path", output_path)

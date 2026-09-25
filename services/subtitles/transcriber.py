import os
import shutil
import textwrap
import whisper
from whisper.utils import get_writer
import imageio_ffmpeg


def _ensure_ffmpeg_in_path():
    """Ensure ffmpeg executable from imageio_ffmpeg is in PATH for whisper."""
    try:
        exe_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(exe_path)
        target = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
        if not os.path.exists(target):
            shutil.copyfile(exe_path, target)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    except Exception as e:
        print(f"[FFmpeg PATH Warning]: {e}")


def _wrap_text_lines(text: str, max_width: int = 32, max_lines: int = 2) -> str:
    """Wrap text to max 32 characters per line, max 2 lines for clean subtitle blocks."""
    lines = textwrap.wrap(text, width=max_width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    return "\n".join(lines)


def _create_fallback_srt(audio_path: str, srt_path: str, fallback_text: str = "Audio narration"):
    """Creates a basic SRT file if Whisper transcription fails."""
    try:
        from moviepy.editor import AudioFileClip
        audio = AudioFileClip(audio_path)
        duration = int(audio.duration) + 1
    except Exception:
        duration = 10

    m, s = divmod(duration, 60)
    h, m = divmod(m, 60)
    end_time_str = f"{h:02d}:{m:02d}:{s:02d},000"

    wrapped_text = _wrap_text_lines(fallback_text, max_width=32, max_lines=2)
    srt_content = f"1\n00:00:00,000 --> {end_time_str}\n{wrapped_text}\n"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)


def generate_subtitles(audio_path: str, output_dir: str, filename_no_ext: str, fallback_text: str = "") -> str:
    """
    Transcribes audio using OpenAI Whisper and generates an SRT file.
    Falls back gracefully to timing-based SRT if Whisper fails.
    Returns the path to the SRT file.
    """
    os.makedirs(output_dir, exist_ok=True)
    final_srt_path = os.path.join(output_dir, f"{filename_no_ext}.srt")

    _ensure_ffmpeg_in_path()

    try:
        model = whisper.load_model("base")
        result = model.transcribe(audio_path, word_timestamps=True)
        
        # Write SRT with strict 32-char line width and max 2 lines
        srt_writer = get_writer("srt", output_dir)
        srt_writer(result, audio_path, {"max_line_width": 32, "max_line_count": 2, "highlight_words": False})
        
        audio_basename = os.path.basename(audio_path)
        expected_srt_path = os.path.join(output_dir, audio_basename + ".srt")
        
        if os.path.exists(expected_srt_path):
            if expected_srt_path != final_srt_path:
                if os.path.exists(final_srt_path):
                    os.remove(final_srt_path)
                os.rename(expected_srt_path, final_srt_path)
            return final_srt_path
        
        for f in os.listdir(output_dir):
            if f.endswith('.srt') and filename_no_ext in f:
                return os.path.join(output_dir, f)
    except Exception as e:
        print(f"[Whisper Warning] Transcription fallback triggered: {e}")
        _create_fallback_srt(audio_path, final_srt_path, fallback_text or "Video Narration")
        return final_srt_path

    if not os.path.exists(final_srt_path):
        _create_fallback_srt(audio_path, final_srt_path, fallback_text or "Video Narration")
        
    return final_srt_path

import os
import subprocess
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip


def _get_ffmpeg_bin() -> str:
    """
    Returns the best available FFmpeg binary path.
    Prefers the imageio_ffmpeg bundled binary (which has libass/subtitles support)
    over the system FFmpeg (which may lack libass).
    Falls back to 'ffmpeg' on PATH if imageio_ffmpeg is not available.
    """
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def parse_duration(dur_str: str) -> float:
    try:
        # Extract digits from strings like "3 seconds" or "5-7"
        import re
        # Handle range like "5-7" -> take the first number
        match = re.search(r'\d+\.?\d*', str(dur_str))
        return float(match.group()) if match else 3.0
    except Exception:
        return 3.0


def compose_video(
    image_paths: list,
    durations: list,
    audio_path: str,
    srt_path: str,
    output_path: str
) -> str:
    """
    Combines scene images according to their durations, adds voiceover,
    and burns subtitles into the final MP4 using the imageio_ffmpeg binary
    (which includes libass support).

    Returns the output_path on success.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temp_no_subs = os.path.join(os.path.dirname(output_path), "temp_no_subs.mp4")

    # ------------------------------------------------------------------ #
    # Step 1: Build the video slideshow + audio using MoviePy
    # ------------------------------------------------------------------ #
    clips = []
    for img_path, duration in zip(image_paths, durations):
        dur = parse_duration(str(duration))
        clip = ImageClip(img_path).set_duration(dur)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_path)

    # Extend the last scene if the voiceover is longer than the sum of scenes
    if audio.duration > final_clip.duration:
        diff = audio.duration - final_clip.duration
        clips[-1] = clips[-1].set_duration(clips[-1].duration + diff)
        final_clip = concatenate_videoclips(clips, method="compose")

    final_clip = final_clip.set_audio(audio)

    # Write the intermediate file (video + audio, no subtitles yet)
    final_clip.write_videofile(
        temp_no_subs,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )

    # ------------------------------------------------------------------ #
    # Step 2: Burn subtitles using the imageio_ffmpeg binary (has libass)
    # ------------------------------------------------------------------ #
    ffmpeg_bin = _get_ffmpeg_bin()

    # On macOS, the subtitles filter needs a properly-escaped absolute path.
    # Use absolute paths to avoid working-directory ambiguity.
    abs_srt = os.path.abspath(srt_path)
    abs_temp = os.path.abspath(temp_no_subs)
    abs_output = os.path.abspath(output_path)

    # Escape colons and backslashes in the SRT path for the filter string.
    # On macOS/Linux paths normally don't have colons except drive letters on Windows.
    srt_escaped = abs_srt.replace("\\", "/").replace(":", "\\:")

    subtitle_filter = (
        f"subtitles='{srt_escaped}'"
        ":force_style='FontSize=28,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,MarginV=60'"
    )

    ffmpeg_cmd = [
        ffmpeg_bin, "-y",
        "-i", abs_temp,
        "-vf", subtitle_filter,
        "-c:a", "copy",
        "-movflags", "+faststart",
        abs_output
    ]

    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(
            f"FFmpeg subtitle burn failed:\n"
            f"STDOUT: {result.stdout[-2000:]}\n"
            f"STDERR: {result.stderr[-2000:]}"
        )

    # Cleanup temp file
    if os.path.exists(temp_no_subs):
        os.remove(temp_no_subs)

    return output_path

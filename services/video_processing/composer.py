import os
import shutil
import subprocess
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip


def _get_ffmpeg_bin() -> str:
    """
    Returns the best available FFmpeg binary path.
    Prefers the imageio_ffmpeg bundled binary.
    """
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def parse_duration(dur_str: str) -> float:
    try:
        import re
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
    and burns subtitles into the final MP4 using MoviePy 2.x and FFmpeg.

    Returns the output_path on success.
    """
    abs_output = os.path.abspath(output_path)
    work_dir = os.path.dirname(abs_output)
    os.makedirs(work_dir, exist_ok=True)
    
    temp_no_subs = os.path.join(work_dir, "temp_no_subs.mp4")

    # ------------------------------------------------------------------ #
    # Step 1: Build the video slideshow + audio using MoviePy 2.x
    # ------------------------------------------------------------------ #
    clips = []
    for img_path, duration in zip(image_paths, durations):
        dur = parse_duration(str(duration))
        # MoviePy 2.x uses with_duration
        clip = ImageClip(img_path).with_duration(dur)
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_path)

    # Extend the last scene if the voiceover is longer than the sum of scenes
    if audio.duration > final_clip.duration:
        diff = audio.duration - final_clip.duration
        last_clip = clips[-1].with_duration(clips[-1].duration + diff)
        clips[-1] = last_clip
        final_clip = concatenate_videoclips(clips, method="compose")

    final_clip = final_clip.with_audio(audio)

    # Write the intermediate file (video + audio, 1080x1920)
    final_clip.write_videofile(
        temp_no_subs,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    
    # Close clips to release file handles
    try:
        audio.close()
        final_clip.close()
        for c in clips:
            c.close()
    except Exception:
        pass

    # ------------------------------------------------------------------ #
    # Step 2: Burn subtitles using FFmpeg if srt_path exists
    # ------------------------------------------------------------------ #
    if srt_path and os.path.exists(srt_path):
        ffmpeg_bin = _get_ffmpeg_bin()
        local_srt_name = "subtitles.srt"
        local_srt_path = os.path.join(work_dir, local_srt_name)
        if os.path.abspath(srt_path) != os.path.abspath(local_srt_path):
            shutil.copyfile(srt_path, local_srt_path)

        temp_name = os.path.basename(temp_no_subs)
        output_name = os.path.basename(abs_output)

        subtitle_filter = f"subtitles={local_srt_name}:force_style='FontSize=26,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,MarginV=60'"

        ffmpeg_cmd = [
            ffmpeg_bin, "-y",
            "-i", temp_name,
            "-vf", subtitle_filter,
            "-c:a", "copy",
            "-movflags", "+faststart",
            output_name
        ]

        result = subprocess.run(ffmpeg_cmd, cwd=work_dir, capture_output=True, text=True)

        if result.returncode != 0 or not os.path.exists(abs_output) or os.path.getsize(abs_output) == 0:
            print(f"[FFmpeg Warning] Subtitle burning skipped or failed, using clean MP4")
            if os.path.exists(temp_no_subs):
                if os.path.exists(abs_output):
                    os.remove(abs_output)
                shutil.copyfile(temp_no_subs, abs_output)
    else:
        # No subtitle file provided, copy temp to output
        if os.path.exists(temp_no_subs):
            if os.path.exists(abs_output):
                os.remove(abs_output)
            shutil.copyfile(temp_no_subs, abs_output)
    
    # Cleanup temp video
    if os.path.exists(temp_no_subs):
        try:
            os.remove(temp_no_subs)
        except Exception:
            pass

    return abs_output

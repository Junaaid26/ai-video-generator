import os
import shutil
import subprocess
import tempfile


def _get_ffmpeg_bin() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def parse_duration(dur_str) -> float:
    try:
        import re
        if isinstance(dur_str, (int, float)):
            return float(dur_str)
        match = re.search(r"\d+\.?\d*", str(dur_str))
        return float(match.group()) if match else 5.0
    except Exception:
        return 5.0


def _animate_scene_image(
    ffmpeg_bin: str,
    image_path: str,
    duration: float,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
    fps: int = 24,
    animation_style: str = "zoom_pan",
) -> bool:
    """
    Apply Ken Burns-style animation to a still image using FFmpeg zoompan.
    Creates slow zoom + slight pan so stills feel like video scenes.
    """
    total_frames = max(int(duration * fps), 1)
    fade_dur = min(0.4, duration * 0.08)

    # Alternate zoom direction per scene for variety
    scene_idx = 0
    try:
        import re
        m = re.search(r"scene_(\d+)", os.path.basename(image_path))
        if m:
            scene_idx = int(m.group(1))
    except Exception:
        pass

    if scene_idx % 3 == 0:
        zoom_expr = f"'1+0.12*on/{total_frames}'"
        x_expr = f"'(iw-iw/zoom)*on/{total_frames}*0.3'"
    elif scene_idx % 3 == 1:
        zoom_expr = f"'1.12-0.08*on/{total_frames}'"
        x_expr = f"'(iw-iw/zoom)*(1-on/{total_frames})*0.2'"
    else:
        zoom_expr = f"'1+0.08*on/{total_frames}'"
        x_expr = "'iw/2-(iw/zoom/2)'"

    y_expr = f"'ih/2-(ih/zoom/2)+10*sin(on/{total_frames}*3.14)'"

    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"zoompan=z={zoom_expr}:x={x_expr}:y={y_expr}:"
        f"d={total_frames}:s={width}x{height}:fps={fps},"
        f"fade=t=in:st=0:d={fade_dur},"
        f"fade=t=out:st={max(duration - fade_dur, 0):.3f}:d={fade_dur}"
    )

    cmd = [
        ffmpeg_bin, "-y",
        "-loop", "1",
        "-i", image_path,
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and os.path.exists(output_path)


def _concat_videos(ffmpeg_bin: str, clip_paths: list, output_path: str) -> bool:
    """Concatenate animated scene clips."""
    if len(clip_paths) == 1:
        shutil.copyfile(clip_paths[0], output_path)
        return True

    list_file = output_path + ".concat.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            safe = p.replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe}'\n")

    cmd = [
        ffmpeg_bin, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        os.remove(list_file)
    except Exception:
        pass
    return result.returncode == 0 and os.path.exists(output_path)


def _add_audio(ffmpeg_bin: str, video_path: str, audio_path: str, output_path: str) -> bool:
    cmd = [
        ffmpeg_bin, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and os.path.exists(output_path)


def _burn_subtitles(
    ffmpeg_bin: str,
    video_path: str,
    srt_path: str,
    output_path: str,
    work_dir: str,
    width: int = 1080,
    height: int = 1920,
) -> bool:
    """
    Burn subtitles with improved styling:
    - Readable font size (scaled relative to actual video resolution)
    - Semi-transparent background box
    - Bottom placement (single line, not covering faces)
    - White text with dark outline
    """
    local_srt_name = "subtitles.srt"
    local_srt_path = os.path.join(work_dir, local_srt_name)
    if os.path.abspath(srt_path) != os.path.abspath(local_srt_path):
        shutil.copyfile(srt_path, local_srt_path)

    # Without an explicit script resolution, libass falls back to a default
    # PlayResX/PlayResY (384x288) and scales FontSize up relative to that,
    # which makes the text cover almost the entire frame on HD/vertical
    # videos. Scale the font size to the real video height instead, and use
    # a small bottom margin so subtitles sit in a single line near the
    # bottom of the frame.
    # Scale font size, vertical margin, and horizontal margins relative to target resolution
    font_size = max(18, round(height * 0.029))  # 56px for 1920h
    margin_v = max(60, round(height * 0.135))   # 260px for 1920h (~13.5% above bottom edge)
    margin_h = max(30, round(width * 0.083))    # 90px for 1080w (safe left/right margins)

    # Explicit PlayResX and PlayResY tell libass the exact pixel canvas resolution
    subtitle_style = (
        f"PlayResX={width},"
        f"PlayResY={height},"
        "FontName=Arial,"
        f"FontSize={font_size},"
        "PrimaryColour=&H00FFFFFF,"   # White text
        "OutlineColour=&H00000000,"   # Black outline
        "BackColour=&H60000000,"      # Subtle dark backing
        "BorderStyle=1,"              # Outline + shadow
        "Outline=3,"                  # 3px crisp black outline/stroke
        "Shadow=1,"                   # Subtle shadow for legibility over bright backgrounds
        f"MarginV={margin_v},"        # ~13.5% above bottom edge
        f"MarginL={margin_h},"        # Safe left margin
        f"MarginR={margin_h},"        # Safe right margin
        "Alignment=2,"                # Centered horizontally
        "Bold=1"                      # Bold sans-serif font
    )

    subtitle_filter = (
        f"subtitles={local_srt_name}:force_style='{subtitle_style}'"
    )

    video_name = os.path.basename(video_path)
    output_name = os.path.basename(output_path)

    cmd = [
        ffmpeg_bin, "-y",
        "-i", video_name,
        "-vf", subtitle_filter,
        "-c:a", "copy",
        "-movflags", "+faststart",
        output_name,
    ]

    result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
    return result.returncode == 0 and os.path.exists(output_path)


def compose_video(
    image_paths: list,
    durations: list,
    audio_path: str,
    srt_path: str,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
) -> str:
    """
    Full composition pipeline:
    1. Animate each scene image (Ken Burns zoom/pan + fade transitions)
    2. Concatenate animated clips
    3. Add voiceover audio
    4. Burn styled subtitles as overlay

    Returns output_path on success.
    """
    abs_output = os.path.abspath(output_path)
    work_dir = os.path.dirname(abs_output)
    os.makedirs(work_dir, exist_ok=True)

    ffmpeg_bin = _get_ffmpeg_bin()
    temp_clips = []
    temp_with_audio = os.path.join(work_dir, "temp_with_audio.mp4")
    temp_concat = os.path.join(work_dir, "temp_concat.mp4")

    try:
        # Step 1: Animate each scene image
        for i, (img_path, duration) in enumerate(zip(image_paths, durations)):
            dur = parse_duration(duration)
            clip_path = os.path.join(work_dir, f"anim_scene_{i:03d}.mp4")
            success = _animate_scene_image(
                ffmpeg_bin, img_path, dur, clip_path, width, height
            )
            if not success:
                raise RuntimeError(f"Failed to animate scene {i + 1}: {img_path}")
            temp_clips.append(clip_path)

        # Step 2: Concatenate with crossfade-like fades (fade in/out on each clip)
        if not _concat_videos(ffmpeg_bin, temp_clips, temp_concat):
            raise RuntimeError("Failed to concatenate animated scene clips")

        # Step 3: Add voiceover audio
        if audio_path and os.path.exists(audio_path):
            if not _add_audio(ffmpeg_bin, temp_concat, audio_path, temp_with_audio):
                shutil.copyfile(temp_concat, temp_with_audio)
        else:
            shutil.copyfile(temp_concat, temp_with_audio)

        # Step 4: Burn subtitles
        if srt_path and os.path.exists(srt_path):
            if not _burn_subtitles(ffmpeg_bin, temp_with_audio, srt_path, abs_output, work_dir, width, height):
                print("[FFmpeg Warning] Subtitle burning failed, using video without subs")
                shutil.copyfile(temp_with_audio, abs_output)
        else:
            shutil.copyfile(temp_with_audio, abs_output)

    finally:
        for p in temp_clips + [temp_concat, temp_with_audio]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    return abs_output

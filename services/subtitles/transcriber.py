import os
import whisper
from whisper.utils import get_writer

def generate_subtitles(audio_path: str, output_dir: str, filename_no_ext: str) -> str:
    """
    Transcribes audio using OpenAI Whisper and generates an SRT file.
    Returns the path to the SRT file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load base model (requires download on first run)
    model = whisper.load_model("base")
    
    # Transcribe with word-level timestamps if possible
    result = model.transcribe(audio_path, word_timestamps=True)
    
    # Write SRT
    srt_writer = get_writer("srt", output_dir)
    srt_writer(result, audio_path, {"max_line_width": 40, "max_line_count": 2, "highlight_words": False})
    
    # Whisper creates the file with the same name as the input audio + .srt
    # The writer might name it based on the audio_path.
    audio_basename = os.path.basename(audio_path)
    expected_srt_path = os.path.join(output_dir, audio_basename + ".srt")
    
    # Sometimes whisper drops the extension, so let's rename it properly if needed
    final_srt_path = os.path.join(output_dir, f"{filename_no_ext}.srt")
    
    if os.path.exists(expected_srt_path):
        os.rename(expected_srt_path, final_srt_path)
        return final_srt_path
    
    # Fallback search if writer named it differently
    for f in os.listdir(output_dir):
        if f.endswith('.srt') and filename_no_ext in f:
            return os.path.join(output_dir, f)
            
    # If we couldn't find the exact file name, just return what we expect and hope the composer finds it
    return final_srt_path

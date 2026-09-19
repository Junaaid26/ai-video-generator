import os
import random
from PIL import Image, ImageDraw, ImageFont

def generate_mock_scene_image(scene_text: str, output_path: str, width: int = 1080, height: int = 1920) -> str:
    """
    Generates a placeholder image for a scene with a random background color and centered text.
    Suitable for 9:16 vertical video format.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate random vibrant background color
    r = random.randint(50, 200)
    g = random.randint(50, 200)
    b = random.randint(50, 200)
    
    img = Image.new('RGB', (width, height), color=(r, g, b))
    draw = ImageDraw.Draw(img)
    
    # Try to load a default font, fallback if unavailable
    try:
        # Default truetype font on mac/linux might vary, let's use default load
        font = ImageFont.load_default()
        # Scale it up conceptually by drawing it bigger or we just use default which is small
    except Exception:
        font = None
        
    # Draw text with word wrap
    margin = 100
    offset = height // 2 - 200
    
    # Simple word wrap
    words = scene_text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        # Approximate width check (very rough if font is default)
        if len(" ".join(current_line)) > 30:
            lines.append(" ".join(current_line))
            current_line = []
    if current_line:
        lines.append(" ".join(current_line))
        
    for line in lines:
        if font:
            # Get text bounding box
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
        else:
            w = len(line) * 6
            h = 10
            
        draw.text(((width - w) / 2, offset), line, font=font, fill=(255, 255, 255))
        offset += h + 20
        
    img.save(output_path)
    return output_path

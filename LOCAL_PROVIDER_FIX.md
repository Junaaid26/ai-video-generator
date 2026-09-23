# Local Provider Setup Guide (100% Free)

## Problem

The local Stable Diffusion provider is completely free but currently has dependency installation issues on Windows due to pip file locking problems.

## Solution: Clean Virtual Environment Installation

### Step 1: Create a New Virtual Environment

```bash
# Navigate to project directory
cd C:\Users\hp\Downloads\ai-video-generator

# Create a clean virtual environment
python -m venv venv_clean

# Activate the virtual environment
venv_clean\Scripts\activate
```

### Step 2: Upgrade pip First

```bash
# Upgrade pip to avoid file locking issues
python -m pip install --upgrade pip
```

### Step 3: Install Dependencies One by One

```bash
# Install PyTorch first (this might take 5-10 minutes)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip install pillow
pip install requests
pip install diffusers
pip install transformers
pip install accelerate
pip install safetensors
```

### Step 4: Install Other Project Dependencies

```bash
pip install fastapi uvicorn streamlit sqlalchemy pydantic python-dotenv alembic
pip install google-genai moviepy openai-whisper edge-tts imageio_ffmpeg httpx
```

### Step 5: Configure Local Provider

Add to your `.env` file:
```bash
VISUAL_PROVIDER=local
VISUAL_MODEL=stabilityai/sd-turbo
```

### Step 6: Test the Provider

```bash
python -c "from services.visual_generation import get_visual_provider; p = get_visual_provider(); print(p.name, p.is_available, p.availability_message())"
```

## Alternative: Use CPU-Only PyTorch

If GPU installation fails, use CPU-only PyTorch (slower but works):

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

Then the model will run on CPU (expect 30-60 seconds per image instead of 5-10 seconds).

## Alternative: Use Hugging Face Free Tier (Easier)

If local installation is too difficult, use Hugging Face's free inference API:

1. Get free API key: https://huggingface.co/settings/tokens
2. Add to `.env`:
   ```bash
   VISUAL_PROVIDER=huggingface
   HUGGINGFACE_API_KEY=hf_your_key_here
   ```
3. No GPU or heavy dependencies required!

## Troubleshooting

### "Cannot find specified file" during pip install
- This is a Windows file locking issue
- Solution: Use a fresh virtual environment (Step 1)
- Close any running Python processes first

### "Out of memory" during model loading
- The model requires ~4GB RAM minimum
- Solution: Close other applications or use CPU-only mode

### "CUDA not available" but you have NVIDIA GPU
- Install CUDA toolkit from NVIDIA website
- Or use CPU-only PyTorch (slower but works)

### Model download is very slow
- The first download is ~2-3GB
- It's cached locally after first use
- Use a stable internet connection

## Advantages of Local Provider

✅ **100% Free**: No API costs ever
✅ **Privacy**: All generation happens locally
✅ **No Rate Limits**: Generate as many images as you want
✅ **Customizable**: Can use any open-source model
✅ **Offline**: Works without internet after initial download

## Current Status

The local provider code is fully implemented and ready to use. The only blocker is the dependency installation issue on Windows. Once diffusers is installed successfully, it will work automatically as a fallback when cloud providers are unavailable.
# Cloud Provider Setup Guide

## Overview

The AI video generator supports multiple cloud providers for high-quality AI imagery. The system prioritizes **free options first**, then paid options for maximum quality.

## Provider Priority Chain

The system automatically falls back through providers in this order:

1. **Hugging Face** (Primary - FREE) - Free inference API tier
2. **Replicate** (Secondary - Paid) - High-quality cloud-based generation
3. **Local** (Tertiary - FREE) - Local Stable Diffusion if available
4. **Mock** (Last resort) - Development placeholder with watermarks

## Setup Instructions

### Option 1: Hugging Face (FREE - Recommended)

1. **Get Hugging Face API Key** (FREE):
   - Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - Sign up or log in (free account)
   - Click "New token"
   - Select "Read" permissions
   - Copy your API key (starts with `hf_`)

2. **Configure Environment Variables**:
   ```bash
   # Use Hugging Face as primary provider (FREE)
   VISUAL_PROVIDER=auto

   # Your Hugging Face API key (FREE)
   HUGGINGFACE_API_KEY=hf_your_actual_api_key_here

   # Optional: Choose a specific model
   HUGGINGFACE_MODEL=stabilityai/stable-diffusion-xl-base-1.0
   ```

3. **Free Tier Limits**:
   - Limited daily requests on free tier
   - Perfect for testing and development
   - No credit card required

### Option 2: Replicate (Paid - Optional)

1. **Get Replicate API Key**:
   - Go to [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens)
   - Sign up or log in
   - Click "Create API Token"
   - Copy your API key (starts with `r8_`)

2. **Configure Environment Variables**:
   ```bash
   # Use Replicate as secondary provider
   VISUAL_PROVIDER=auto

   # Your Replicate API key
   REPLICATE_API_KEY=r8_your_actual_api_key_here

   # Optional: Choose a specific model
   REPLICATE_MODEL=black-forest-labs/flux-schnell
   ```

3. **Cost Considerations**:
   - **Flux Schnell**: ~$0.003 per image (very affordable)
   - **SDXL**: ~$0.005 per image
   - For a 5-scene video: ~$0.015 - $0.15 total

### Recommended Models

**Hugging Face (FREE):**
- `stabilityai/stable-diffusion-xl-base-1.0` - Excellent quality (recommended)
- `runwayml/stable-diffusion-v1-5` - Good quality, faster

**Replicate (Paid):**
- `black-forest-labs/flux-schnell` - Fast, high quality
- `stability-ai/sdxl` - Excellent quality

### Testing the Setup

After configuring your API key, test the provider:

```bash
curl http://localhost:8000/visual/provider-status
```

Expected response for Hugging Face:
```json
{
  "provider": "huggingface:stabilityai/stable-diffusion-xl-base-1.0",
  "is_available": true,
  "message": "Hugging Face provider ready using model: stabilityai/stable-diffusion-xl-base-1.0",
  "model": "stabilityai/stable-diffusion-xl-base-1.0",
  "requires_gpu": false,
  "recommended_vram_gb": 0,
  "recommended_ram_gb": 4
}
```

## Manual Provider Selection

You can force a specific provider by setting `VISUAL_PROVIDER`:

```bash
# Force Hugging Face only (FREE, requires API key)
VISUAL_PROVIDER=huggingface

# Force Replicate only (paid, requires API key)
VISUAL_PROVIDER=replicate

# Force local only (completely free, requires GPU and diffusers)
VISUAL_PROVIDER=local

# Force mock only (development/testing)
VISUAL_PROVIDER=mock

# Auto mode (default: tries Hugging Face, then Replicate, then local, then mock)
VISUAL_PROVIDER=auto
```

## Fallback Behavior

When `VISUAL_PROVIDER=auto` (default):

1. **Hugging Face fails** → Tries Replicate → Tries local → Uses mock
2. **Replicate fails** → Tries local → Uses mock
3. **Local fails** → Uses mock
4. **All unavailable** → Uses mock with warning

The dashboard will show which provider was used and any fallback reasons.

## Troubleshooting

### Hugging Face Issues

**"Hugging Face API key not found"**
- Ensure `HUGGINGFACE_API_KEY` is set in your `.env` file
- Restart the API server after changing environment variables

**"Hugging Face generation failed"**
- Check your API key is valid
- Verify you have free tier credits available
- Model might be loading (wait and retry)

**"Model is loading"**
- This is normal for first use
- The system automatically waits and retries
- Subsequent requests will be faster

### Replicate Issues

**"Replicate API key not found"**
- Ensure `REPLICATE_API_KEY` is set in your `.env` file
- Restart the API server after changing environment variables

**"Replicate prediction failed"**
- Check your API key is valid
- Verify you have sufficient credits in your Replicate account
- Check the specific error message in the dashboard

**"Replicate prediction timed out"**
- Increase timeout in `replicate_generator.py` (default: 3 minutes)
- Try a faster model like `flux-schnell`

### Local Provider Issues

**"Missing dependencies"**
- Install diffusers: see `LOCAL_PROVIDER_FIX.md`
- Create a clean virtual environment
- Install dependencies one by one

**"CUDA not available"**
- Install CUDA toolkit from NVIDIA website
- Or use CPU-only PyTorch (slower but works)

## Advantages Comparison

### Hugging Face (FREE)
✅ **Completely Free**: No API costs on free tier
✅ **No GPU Required**: Cloud-based generation
✅ **Easy Setup**: Just get API key
✅ **Good Quality**: SDXL model
⚠️ **Rate Limits**: Limited daily requests on free tier

### Replicate (Paid)
✅ **Highest Quality**: State-of-the-art models like Flux
✅ **No GPU Required**: Cloud-based generation
✅ **No Rate Limits**: Pay as you go
✅ **Fast**: Optimized infrastructure
❌ **Cost**: Small per-image fees

### Local (FREE)
✅ **100% Free**: No API costs ever
✅ **Privacy**: All generation happens locally
✅ **No Rate Limits**: Generate as many images as you want
✅ **Customizable**: Can use any open-source model
⚠️ **Hardware**: Requires GPU for good performance
⚠️ **Setup**: More complex installation

## Current Status

Without API keys configured, the system will automatically fall back to the mock provider with a visible watermark. To enable high-quality visuals:

1. **Recommended (FREE)**: Add Hugging Face API key to `.env`
2. **Alternative (FREE)**: Fix local provider installation (see `LOCAL_PROVIDER_FIX.md`)
3. **Optional (Paid)**: Add Replicate API key for maximum quality
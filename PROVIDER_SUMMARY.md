# Visual Generation Provider Summary

## Overview

The AI video generator now supports **4 visual generation providers** with automatic fallback, prioritizing **free options first**:

1. **Hugging Face** (FREE) - Primary choice
2. **Replicate** (Paid) - High-quality option
3. **Local** (FREE) - Completely free, requires GPU
4. **Mock** (FREE) - Development placeholder

## Quick Setup Guide

### Option 1: Hugging Face (FREE - Recommended)

**Best for:** Testing, development, cost-conscious users

**Setup (5 minutes):**
1. Get free API key: https://huggingface.co/settings/tokens
2. Add to `.env`:
   ```bash
   VISUAL_PROVIDER=auto
   HUGGINGFACE_API_KEY=hf_your_key_here
   ```
3. Restart API server

**Cost:** FREE (limited daily requests on free tier)
**Quality:** Excellent (SDXL model)
**Hardware:** No GPU required

### Option 2: Local Provider (FREE - No API Costs)

**Best for:** Privacy, unlimited generation, users with GPU

**Setup (15-30 minutes):**
1. See `LOCAL_PROVIDER_FIX.md` for detailed instructions
2. Install dependencies in clean virtual environment
3. Add to `.env`:
   ```bash
   VISUAL_PROVIDER=local
   VISUAL_MODEL=stabilityai/sd-turbo
   ```

**Cost:** FREE (no API costs ever)
**Quality:** Good (Stable Diffusion Turbo)
**Hardware:** GPU recommended (4GB VRAM), CPU works but slow

### Option 3: Replicate (Paid - Optional)

**Best for:** Maximum quality, production use

**Setup (5 minutes):**
1. Get API key: https://replicate.com/account/api-tokens
2. Add to `.env`:
   ```bash
   VISUAL_PROVIDER=auto
   REPLICATE_API_KEY=r8_your_key_here
   ```

**Cost:** ~$0.003-0.03 per image
**Quality:** Excellent (Flux, SDXL)
**Hardware:** No GPU required

## Provider Comparison

| Provider | Cost | Quality | Hardware | Setup Difficulty | Rate Limits |
|----------|------|---------|----------|------------------|-------------|
| Hugging Face | FREE | Excellent | None | Easy | Limited (free tier) |
| Local | FREE | Good | GPU recommended | Medium | None |
| Replicate | Paid | Excellent | None | Easy | None |
| Mock | FREE | Poor | None | N/A | None |

## Automatic Fallback Chain

When `VISUAL_PROVIDER=auto` (default):

```
Hugging Face (FREE)
    ↓ (if fails)
Replicate (Paid)
    ↓ (if fails)
Local (FREE)
    ↓ (if fails)
Mock (Dev placeholder)
```

The system automatically tries each provider and falls back to the next if one fails.

## Current Status

Right now, without any API keys or local installation:
- **Active Provider**: `mock:dev`
- **Status**: Generating watermarked placeholder images
- **To Fix**: Add Hugging Face API key (recommended) or install local provider

## Testing Your Setup

Check provider status:
```bash
curl http://localhost:8000/visual/provider-status
```

Expected output with Hugging Face configured:
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

## Configuration Examples

### Use Only Hugging Face (FREE)
```bash
VISUAL_PROVIDER=huggingface
HUGGINGFACE_API_KEY=hf_your_key_here
```

### Use Only Local (FREE)
```bash
VISUAL_PROVIDER=local
VISUAL_MODEL=stabilityai/sd-turbo
```

### Use Only Replicate (Paid)
```bash
VISUAL_PROVIDER=replicate
REPLICATE_API_KEY=r8_your_key_here
```

### Auto Mode (Recommended)
```bash
VISUAL_PROVIDER=auto
HUGGINGFACE_API_KEY=hf_your_key_here  # Optional, enables free tier
REPLICATE_API_KEY=r8_your_key_here    # Optional, enables paid fallback
```

## Troubleshooting

### "All providers unavailable"
- Add Hugging Face API key (easiest fix)
- Or install local provider (see `LOCAL_PROVIDER_FIX.md`)

### "Hugging Face generation failed"
- Check API key is valid
- Wait if model is loading (first use)
- Check free tier credits

### "Local provider unavailable"
- Install diffusers: `pip install diffusers transformers accelerate`
- See `LOCAL_PROVIDER_FIX.md` for detailed guide

### "Replicate prediction failed"
- Check API key and credits
- Try a different model

## Documentation Files

- `REPLICATE_SETUP.md` - Cloud provider setup guide
- `LOCAL_PROVIDER_FIX.md` - Local provider installation guide
- `.env.example` - Configuration template

## Recommendation

**For immediate free usage:**
→ Add Hugging Face API key (5 minutes setup)

**For long-term free usage:**
→ Fix local provider installation (15-30 minutes setup)

**For maximum quality:**
→ Add Replicate API key (5 minutes setup, small cost)
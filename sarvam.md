# Sarvam AI Voice API Reference (STT + Auto Lang Detect + Translate + TTS)
*Updated: March 2026 | Source: Official docs  [docs.sarvam](https://docs.sarvam.ai/api-reference-docs/speech-to-text/transcribe)*

## 1. Speech-to-Text (STT) with Auto Language Detection & Translation to English

**Primary Endpoint**: `POST https://api.sarvam.ai/speech-to-text` [docs.sarvam](https://docs.sarvam.ai/api-reference-docs/speech-to-text/transcribe)

**Key Features**:
- **Auto language detection**: Supports 22+ Indian languages (Hindi, Kannada, Tamil, Telugu, etc.) + code-mixing + English.
- **Translation mode**: Set `mode="translate"` → auto-detects input lang → transcribes → translates directly to English.
- **Model**: `saaras:v3` (recommended, state-of-the-art).

### Request (Multipart Form)
```
curl -X POST https://api.sarvam.ai/speech-to-text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@audio.webm" \
  -F "model=saaras:v3" \
  -F "mode=translate"
```

**Parameters**:
| Param              | Type    | Required | Description |
|--------------------|---------|----------|-------------|
| `file`             | file    | ✅ Yes  | Audio file (WebM, WAV, MP3, Opus, etc. 16kHz optimal). |
| `model`            | enum    | ❌ No   | `saaras:v3` (default: `saarika:v2.5`). |
| `mode`             | enum    | ❌ No   | `translate` → auto lang detect + English translation.<br>Others: `transcribe`, `verbatim`, `translit`, `codemix`. |
| `language_code`    | enum    | ❌ No   | BCP-47 (e.g., `hi-IN`, `kn-IN`). Omit/``unknown`` → auto-detect. |
| `input_audio_codec`| enum    | ❌ No   | For PCM files only (16kHz). |

**Full language list** (saaras:v3):
- `hi-IN` (Hindi), `kn-IN` (Kannada), `ta-IN` (Tamil), `te-IN` (Telugu), `ml-IN` (Malayalam), `mr-IN` (Marathi), `gu-IN` (Gujarati), `bn-IN` (Bengali), `pa-IN` (Punjabi), `od-IN` (Odia), `en-IN` (English), +13 more (Assamese, Urdu, etc.).

### Response (JSON)
```json
{
  "request_id": "uuid",
  "transcript": "My phone number is 9840950950",  // English translation
  "language_code": "hi-IN",                      // Auto-detected
  "language_probability": 0.95,
  "timestamps": {...}                            // Optional
}
```

**Errors**: 400, 403, 422, 429 (rate limit), 500, 503.

**Rate Limits** (Starter): 60 req/min. [docs.sarvam](https://docs.sarvam.ai/api-reference-docs/ratelimits)

***

## 2. Text Translation API (English → Indic or vice-versa)

**Endpoint**: `POST https://api.sarvam.ai/translate` [docs.sarvam](https://docs.sarvam.ai/api-reference-docs/text/translate-text)

**Model**: `sarvam-translate` (supports 22 Indic ↔ English).

### Request (JSON)
```
curl -X POST https://api.sarvam.ai/translate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "sarvam-translate",
    "prompt": "मेरा फोन नंबर है 9840950950",
    "target_language": "en"
  }'
```

**Response**:
```json
{
  "choices": [{
    "message": {
      "content": "My phone number is 9840950950"
    }
  }]
}
```

***

## 3. Text-to-Speech (TTS)

**Endpoint**: `POST https://api.sarvam.ai/text-to-speech` [sarvam](https://www.sarvam.ai/apis/text-to-speech)

**Model**: `bulbul-v2` series (India-focused voices).

### Request (JSON)
```
curl -X POST https://api.sarvam.ai/text-to-speech \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "bulbul-hindi-v2",
    "text": "Hello, how are you feeling today?"
  }'
```

**Voice Options** (examples):
- `bulbul-hindi-v2` (Hindi male/female)
- `bulbul-tamil-v2`, `bulbul-kannada-v2`, `bulbul-telugu-v2`
- Full list: Check `/voices` endpoint or docs.

**Response**: Audio bytes (`audio/mpeg` or `audio/wav`).

### Parameters
| Param   | Type   | Description |
|---------|--------|-------------|
| `model` | string | e.g., `bulbul-hindi-v2` |
| `text`  | string | Up to 10k chars. |

***

## Integration Example (FastAPI + React → Kalpana)

```python
# fastapi_voice.py
import aiohttp
from fastapi import FastAPI, UploadFile, File

app = FastAPI()
SARVAM_KEY = "your_key"

@app.post("/voice/pipeline")
async def pipeline(audio: UploadFile = File(...)):
    # 1. STT + Auto Translate
    data = aiohttp.FormData()
    data.add_field("file", await audio.read(), filename="audio.webm")
    data.add_field("model", "saaras:v3")
    data.add_field("mode", "translate")
    
    async with aiohttp.ClientSession() as session:
        stt_resp = await session.post(
            "https://api.sarvam.ai/speech-to-text",
            data=data,
            headers={"Authorization": f"Bearer {SARVAM_KEY}"}
        )
        transcript = (await stt_resp.json())["transcript"]
    
    # 2. Your Ollama agents...
    # 3. TTS
    tts_resp = await session.post(
        "https://api.sarvam.ai/text-to-speech",
        json={"model": "bulbul-hindi-v2", "text": "Empathy response here"},
        headers={"Authorization": f"Bearer {SARVAM_KEY}"}
    )
    audio_bytes = await tts_resp.read()
    
    return {"transcript": transcript, "audio": audio_bytes}

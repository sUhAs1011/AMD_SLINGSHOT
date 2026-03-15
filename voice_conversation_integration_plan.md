# Voice Conversation Integration Plan (Final)

## Objective
Integrate legacy `app1.py` voice capabilities into the active React + FastAPI architecture so the experience feels like an actual voice conversation (non-realtime), while preserving all existing text chat, safety routing, matchmaking, and scheduling behavior.

## Final Product Behavior
1. User can type or send a voice note.
2. In `Auto` mode:
   - Text input -> text response.
   - Voice input -> voice response (with text still visible).
3. Optional override: `Reply Mode = Auto | Text Only | Voice Preferred`.
4. When user sends voice:
   - Sarvam STT auto-detects spoken language.
   - Backend gets English transcript for existing `/api/chat` flow.
   - Assistant final text is translated back to user language.
   - Sarvam TTS generates assistant voice in that same language.
5. If any voice service fails, conversation continues in text without breaking chat.

---

## Non-Negotiable Constraints
1. `/api/chat` contract remains unchanged (SSE chunks + metadata).
2. Listener/Mapper/matchmaker logic remains unchanged.
3. Crisis intercept and PeerMatchModal behavior remain unchanged.
4. Existing text chat UX remains fully intact.
5. Voice integration is additive and isolated.

---

## Language Continuity Strategy (User Voice -> Same-Language Voice Reply)

### STT (User Voice In)
Use Sarvam STT endpoint (`POST /speech-to-text`) with:
- `model = saaras:v3`
- `mode = translate` (returns English transcript suitable for current backend)
- `language_code = unknown` (auto language detection)

Use response fields:
- `transcript` -> treated as `transcript_en` for `/api/chat`
- `language_code` -> detected user spoken language (e.g., `hi-IN`)
- `language_probability` -> confidence score

### Session Language Memory
Maintain per-session field:
- `preferred_voice_language` (default `en-IN`)

Update rule:
- If voice turn detected language confidence is strong (recommended threshold `>= 0.70`), update `preferred_voice_language`.
- If confidence is weak, keep previous `preferred_voice_language`.

### Assistant Reply Out (Translate -> TTS)
For turns where TTS is enabled by reply mode:
1. Take final assistant text (English from existing `/api/chat` generation).
2. Translate to target language (`target_language_code`) using Sarvam translation endpoint/helper.
3. Send translated text to Sarvam TTS.
4. Return playable audio + spoken text metadata to frontend.

Fallback order:
1. Translation fails -> send original English text to TTS.
2. TTS fails -> keep text response only.

---

## Backend Changes (Additive Only)

### 1) New Utility: `backend/utils/sarvam_api.py`
Functions:
- `transcribe_audio(file_bytes, filename, content_type, ...)`
- `translate_text(text, source_lang, target_lang, ...)`
- `synthesize_speech(text, language_code, ...)`

Requirements:
- Timeout + retry (single retry max for minimal complexity).
- Normalized error objects.
- Env-only secrets/config (`SARVAM_API_KEY` etc.).

### 2) Extend Session State in `backend/api.py`
In `get_or_create_session(...)`, add:
- `preferred_voice_language: "en-IN"`

### 3) New Endpoint: `POST /api/transcribe`
Input:
- multipart form audio file (`audio`)
- optional `session_id`

Flow:
1. Call Sarvam STT (`saaras:v3`, `mode=translate`, `language_code=unknown`).
2. Update `preferred_voice_language` if confidence threshold met.

Output JSON:
- `status`
- `transcript_en`
- `detected_language_code`
- `language_probability`
- `effective_voice_language` (post-threshold session value)
- `message` on error

### 4) New Endpoint: `POST /api/tts`
Input JSON:
- `text` (assistant final text)
- `session_id` (optional but recommended)
- `target_language_code` (optional turn-level override)

Flow:
1. Resolve target language:
   - request override if provided
   - else session `preferred_voice_language`
   - else `en-IN`
2. Translate text to target language.
3. Generate TTS audio from translated text.

Output JSON:
- `status`
- `audio_base64`
- `mime_type`
- `spoken_text`
- `spoken_language_code`
- `message` on error

---

## Frontend Changes (Minimal and Backward-Compatible)

### 1) `ChatInput.jsx`
Keep current UI and recorder behavior.
Additive change:
- Pass raw audio blob to parent handler along with `audioUrl`.

### 2) `App.jsx` Voice Pipeline
Add state:
- `replyMode` = `auto | text_only | voice_preferred` (default `auto`)
- `isVoiceProcessing`
- `isKalpanaRecordingVoice`
- `lastDetectedLanguageCode` (optional)

User voice flow:
1. Upload audio blob to `/api/transcribe`.
2. On success:
   - show user audio message as today
   - send `transcript_en` to `/api/chat`
   - cache `detected_language_code` for turn-level TTS target
3. On failure:
   - fallback to existing text-safe behavior
   - non-blocking user notice

Assistant voice flow:
1. Stream `/api/chat` response exactly as today.
2. After stream complete, apply reply mode policy:
   - `auto`: TTS only if this turn was voice input.
   - `text_only`: skip TTS.
   - `voice_preferred`: always attempt TTS.
3. If TTS enabled:
   - show "Kalpana is recording a voice note..."
   - call `/api/tts` with final assistant text and best target language
   - attach returned audio to the last assistant message
4. On TTS failure:
   - keep text response visible
   - subtle notice only

### 3) Reply Mode UX
- Do not ask mandatory preference at start.
- Add small in-UI control: `Auto | Text Only | Voice Preferred`.
- Default to `Auto` for lowest friction.

---

## Error Handling and Fallbacks
1. STT failure -> do not block chat; fallback to text path.
2. STT low confidence -> keep prior session language.
3. Translation failure -> TTS with original English text.
4. TTS failure -> text response only.
5. No voice failure can break `/api/chat` flow.

---

## Compatibility Guarantees
1. Existing text-only conversations behave exactly the same.
2. Crisis modal priority remains unchanged.
3. Peer matching/scheduling remain unchanged.
4. Existing message rendering remains compatible (audio is optional field).
5. `/api/chat` payload and SSE format remain untouched.

---

## Implementation Sequence (Final)
1. Add `backend/utils/sarvam_api.py` with STT/Translate/TTS wrappers.
2. Add `preferred_voice_language` session field in `backend/api.py`.
3. Add `POST /api/transcribe` endpoint.
4. Add `POST /api/tts` endpoint.
5. Update `ChatInput.jsx` to pass audio blob upward.
6. Update `App.jsx` for transcribe -> chat -> translate+tts pipeline.
7. Add reply mode selector (`Auto | Text Only | Voice Preferred`).
8. Add assistant "recording voice note" UI state.
9. Verify regressions and language-loop behavior.

---

## Verification Checklist
1. Text turn in `Auto` -> text response only.
2. Voice turn in `Auto` -> voice response in same detected language.
3. `Text Only` -> never calls `/api/tts`.
4. `Voice Preferred` -> attempts TTS for all assistant turns.
5. Low-confidence language detection does not cause language flipping.
6. STT/Translation/TTS failure cases all degrade gracefully.
7. Crisis intercept still overrides peer modal.
8. Peer scheduling still works unchanged.

---

## Out of Scope (This Phase)
1. Realtime duplex voice.
2. Live call/WebRTC.
3. Advanced multilingual prompt rewriting for Listener.
4. Voice enhancement/noise suppression.

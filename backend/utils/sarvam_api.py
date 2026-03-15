import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai").rstrip("/")
SARVAM_TIMEOUT_SECONDS = float(os.getenv("SARVAM_TIMEOUT_SECONDS", "25"))
SARVAM_MAX_ATTEMPTS = int(os.getenv("SARVAM_MAX_ATTEMPTS", "2"))

STT_ENDPOINT = f"{SARVAM_BASE_URL}/speech-to-text"
TRANSLATE_ENDPOINT = f"{SARVAM_BASE_URL}/translate"
TTS_ENDPOINT = f"{SARVAM_BASE_URL}/text-to-speech"

DEFAULT_TTS_MODEL = os.getenv("SARVAM_TTS_DEFAULT_MODEL", "bulbul-hindi-v2")

# Known language-to-model mappings from Sarvam voice docs.
TTS_MODEL_MAP = {
    "en": "bulbul-english-v2",
    "hi": "bulbul-hindi-v2",
    "kn": "bulbul-kannada-v2",
    "ta": "bulbul-tamil-v2",
    "te": "bulbul-telugu-v2",
}


def _require_api_key() -> str:
    if not SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is missing. Add it in your .env file.")
    return SARVAM_API_KEY


def _headers(content_type_json: bool = False) -> dict[str, str]:
    key = _require_api_key()
    headers = {
        # Support both schemes seen in Sarvam docs variants.
        "Authorization": f"Bearer {key}",
        "api-subscription-key": key,
    }
    if content_type_json:
        headers["Content-Type"] = "application/json"
    return headers


def _to_lang_prefix(language_code: str | None) -> str:
    if not language_code:
        return "en"
    return language_code.split("-")[0].strip().lower() or "en"


def _translation_lang(language_code: str | None) -> str:
    return _to_lang_prefix(language_code)


def _model_candidates(language_code: str | None) -> list[str]:
    lang = _to_lang_prefix(language_code)
    candidates = []
    mapped_model = TTS_MODEL_MAP.get(lang)
    if mapped_model:
        candidates.append(mapped_model)
    candidates.append(DEFAULT_TTS_MODEL)
    # Preserve order while removing duplicates.
    seen = set()
    deduped = []
    for model in candidates:
        if model and model not in seen:
            seen.add(model)
            deduped.append(model)
    return deduped


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    max_attempts = max(1, SARVAM_MAX_ATTEMPTS)
    last_error: Exception | None = None

    for _ in range(max_attempts):
        try:
            response = requests.request(method, url, timeout=SARVAM_TIMEOUT_SECONDS, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc

    if last_error is not None:
        raise RuntimeError(f"Sarvam API request failed: {last_error}") from last_error
    raise RuntimeError("Sarvam API request failed with unknown error.")


def transcribe_audio(
    audio_bytes: bytes,
    filename: str = "voice_note.webm",
    content_type: str = "audio/webm",
) -> dict[str, Any]:
    files = {"file": (filename, audio_bytes, content_type or "application/octet-stream")}
    data = {
        "model": "saaras:v3",
        "mode": "translate",
        "language_code": "unknown",
    }

    response = _request_with_retry(
        "post",
        STT_ENDPOINT,
        headers=_headers(content_type_json=False),
        files=files,
        data=data,
    )
    payload = response.json()

    transcript = (payload.get("transcript") or "").strip()
    if not transcript:
        raise RuntimeError("Sarvam STT returned an empty transcript.")

    raw_probability = payload.get("language_probability")
    try:
        language_probability = float(raw_probability) if raw_probability is not None else 0.0
    except (TypeError, ValueError):
        language_probability = 0.0

    return {
        "request_id": payload.get("request_id"),
        "transcript_en": transcript,
        "detected_language_code": payload.get("language_code") or "en-IN",
        "language_probability": language_probability,
    }


def translate_text(text: str, target_language_code: str | None) -> str:
    clean_text = (text or "").strip()
    if not clean_text:
        return ""

    target_lang = _translation_lang(target_language_code)
    if target_lang == "en":
        return clean_text

    body = {
        "model": "sarvam-translate",
        "prompt": clean_text,
        "target_language": target_lang,
    }

    response = _request_with_retry(
        "post",
        TRANSLATE_ENDPOINT,
        headers=_headers(content_type_json=True),
        json=body,
    )
    payload = response.json()

    translated = ""
    try:
        translated = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        translated = payload.get("translated_text", "")

    translated = (translated or "").strip()
    if not translated:
        raise RuntimeError("Sarvam translation returned empty content.")
    return translated


def synthesize_speech(text: str, language_code: str | None) -> dict[str, Any]:
    clean_text = (text or "").strip()
    if not clean_text:
        raise RuntimeError("Cannot synthesize empty text.")

    last_error: Exception | None = None
    for model in _model_candidates(language_code):
        try:
            response = _request_with_retry(
                "post",
                TTS_ENDPOINT,
                headers=_headers(content_type_json=True),
                json={"model": model, "text": clean_text},
            )
            audio_bytes = response.content
            if not audio_bytes:
                raise RuntimeError("Sarvam TTS returned empty audio.")
            return {
                "audio_bytes": audio_bytes,
                "mime_type": response.headers.get("Content-Type", "audio/mpeg"),
                "tts_model": model,
            }
        except Exception as exc:  # Fallback to next candidate model.
            last_error = exc

    if last_error is not None:
        raise RuntimeError(f"Sarvam TTS failed for all model candidates: {last_error}") from last_error
    raise RuntimeError("Sarvam TTS failed with unknown error.")

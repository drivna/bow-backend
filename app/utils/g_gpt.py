import json
import re
import time
from typing import Any, Dict, List, Tuple

# pip install google-generativeai
import google.generativeai as genai
from google.generativeai import types as gem_types
from loguru import logger
from google.generativeai.types import GenerationConfig

from app.utils.jwt_utils import create_token
from app.utils.ws_util import send_to_room

# Configure your Gemini API key (set GEMINI_API_KEY in your env or assign directly)
# Example:
# import os
# genai.configure(api_key=os.environ["GEMINI_API_KEY"])
genai.configure(api_key="")

# Choose a Gemini model; "gemini-1.5-pro" is strong, "gemini-1.5-flash" is faster/cheaper.
_GEMINI_MODEL_NAME = "gemini-2.5-pro"


def _normalize_openai_messages_to_gemini(
    message_for_model: List[Dict[str, Any]]
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Convert OpenAI-style messages into Gemini's (system_instruction, contents) format.
    """
    system_instruction = None
    contents: List[Dict[str, Any]] = []

    def _content_to_text(c):
        if isinstance(c, str):
            return c
        if isinstance(c, list):
            parts = []
            for p in c:
                if isinstance(p, dict):
                    if "text" in p:
                        parts.append(p["text"])
                    elif p.get("type") == "text" and "text" in p:
                        parts.append(p["text"])
            return "\n".join(parts).strip()
        return str(c)

    for m in message_for_model:
        role = m.get("role", "user")
        text = _content_to_text(m.get("content", "")) or ""

        if role == "system":
            if not system_instruction:
                system_instruction = text
            else:
                system_instruction += ("\n" if system_instruction else "") + text
            continue

        gem_role = "user" if role == "user" else "model"

        contents.append({
            "role": gem_role,
            "parts": [{"text": text}]
        })

    return system_instruction, contents


def fetch_and_stream_response_from_model(message_for_model, user_id: str):
    try:
        system_instruction, contents = _normalize_openai_messages_to_gemini(message_for_model)

        model = genai.GenerativeModel(
            model_name=_GEMINI_MODEL_NAME,
            system_instruction=system_instruction if system_instruction else None,
        )

        generation_config = gem_types.GenerationConfig(
            temperature=0.3,
        )

        # Start streaming
        resp = model.generate_content(
            contents,
            generation_config=generation_config,
            stream=True,
        )

        buf, buf_chars = [], 0
        FLUSH_CHARS, FLUSH_SECS = 800, 0.5
        last = time.time()

        def flush():
            nonlocal buf, buf_chars, last
            if buf:
                send_to_room(user_id, "".join(buf), "message")
                buf, buf_chars, last = [], 0, time.time()

        for chunk in resp:
            # Each chunk has .text for incremental text
            piece = getattr(chunk, "text", None)
            if piece:
                buf.append(piece)
                buf_chars += len(piece)

            # Preserve your original flushing heuristics
            if buf_chars >= FLUSH_CHARS or (time.time() - last) >= FLUSH_SECS or (piece and "\n" in piece):
                flush()

        # Ensure the stream is fully resolved (captures any trailing tokens)
        try:
            resp.resolve()
        except Exception:
            # Some SDK versions already resolve during iteration; safe to ignore
            pass

        flush()
        send_to_room(user_id, "", "done")

    except Exception as e:
        send_to_room(user_id, f"Error: {e}", "error")


def fetch_response_from_model(message_for_model: List[Dict[str, Any]]):
    try:
        # Convert OpenAI-style messages → Gemini format
        system_instruction, contents = _normalize_openai_messages_to_gemini(message_for_model)

        logger.info(f"SYSTEM: {system_instruction}")
        logger.info(f"CONTENTS: {json.dumps(contents, indent=2)}")

        model = genai.GenerativeModel(
            model_name=_GEMINI_MODEL_NAME,
            system_instruction=system_instruction if system_instruction else None,
        )

        generation_config = GenerationConfig(
            temperature=0.3,
        )

        response = model.generate_content(
            contents,
            generation_config=generation_config,
            stream=False,
        )
        logger.info(f"Raw Gemini response: {response}")

        # --- Extract text ---
        content = response.text or ""

        if not content and response.candidates:
            # fallback: pull text from parts
            parts = response.candidates[0].content.parts
            if parts:
                for part in parts:
                    if hasattr(part, "text"):
                        content += part.text

        if not content:
            raise ValueError("Gemini returned no text content")

        # --- Handle code fences ---
        if content.startswith("```"):
            content = re.sub(
                r"^```(?:json)?\n|```$",
                "",
                content.strip(),
                flags=re.IGNORECASE | re.MULTILINE,
            ).strip()

        # --- Try parsing as JSON ---
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Gemini response is not valid JSON, returning raw text")
            return content

    except Exception as e:
        logger.error(f"Error occurred while fetching Gemini response: {e}", exc_info=True)
        return None
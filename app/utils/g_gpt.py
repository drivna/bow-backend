import json
import re
import time
from typing import Any, Dict, List, Tuple

import google.generativeai as genai
from google.generativeai import types as gem_types
from loguru import logger
from google.generativeai.types import GenerationConfig

from app.config import GEMINI_API_KEY
from app.utils.jwt_utils import create_token
from app.utils.ws_util import send_to_room


genai.configure(api_key=GEMINI_API_KEY)


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

        contents.append({"role": gem_role, "parts": [{"text": text}]})

    return system_instruction, contents


def fetch_and_stream_response_from_model(message_for_model, user_id: str):
    try:
        # Normalize the message for the Gemini model
        system_instruction, contents = _normalize_openai_messages_to_gemini(message_for_model)

        # 🚨 Early validation: Ensure contents are not too short or empty
        if (
            not contents or len(contents) < 5 or all(c in " \t\n" for c in contents)
        ):  # Ensure content isn't too short or empty
            msg = "[Error: Content too short or invalid]"
            print(msg)
            send_to_room(user_id, msg, "error")
            return

        # Debugging: Check the contents
        print(f"Contents being sent to the model: {repr(contents)}")

        # Initialize the model
        model = genai.GenerativeModel(
            model_name=_GEMINI_MODEL_NAME,
            system_instruction=system_instruction if system_instruction else None,
        )

        # Configuration for generation
        generation_config = genai.types.GenerationConfig(
            temperature=0.5,  # Adjusted for more stable outputs
            top_p=0.9,  # Increased for more diverse content
            top_k=40,
            max_output_tokens=1024,  # Increased max tokens to avoid truncation
            candidate_count=1,
        )

        # Debug info
        print("=== DEBUG INFO ===")
        print(f"System instruction: {repr(system_instruction)}")
        print(f"Contents: {repr(contents)}")
        print(f"Model name: {_GEMINI_MODEL_NAME}")
        print("==================")

        # Try streaming
        try:
            resp = model.generate_content(
                contents=contents,
                generation_config=generation_config,
                stream=True,
            )
            print("Streaming response object created")
        except Exception as e:
            print("Streaming creation failed:", repr(e))
            send_to_room(user_id, f"[Streaming creation failed: {repr(e)}]", "error")
            return

        buf, buf_chars, got_text = [], 0, False
        FLUSH_CHARS, FLUSH_SECS = 800, 0.5
        last = time.time()
        finish_reason = None

        def flush():
            nonlocal buf, buf_chars, last
            if buf:
                send_to_room(user_id, "".join(buf), "message")
                buf, buf_chars, last = [], 0, time.time()

        # Streaming response processing
        try:
            for chunk in resp:
                piece = None

                # Extract finish reason
                if hasattr(chunk, "candidates") and chunk.candidates:
                    candidate = chunk.candidates[0]
                    finish_reason = getattr(candidate, "finish_reason", None)

                # Extract text safely
                if hasattr(chunk, "parts") and chunk.parts:
                    for part in chunk.parts:
                        if getattr(part, "text", None):
                            piece = part.text
                            got_text = True
                            buf.append(piece)
                            buf_chars += len(piece)
                            break

                if not piece:
                    print(f"Non-text chunk: {repr(chunk)}")

                # Flush conditions
                if (
                    buf_chars >= FLUSH_CHARS
                    or (time.time() - last) >= FLUSH_SECS
                    or (piece and "\n" in piece)
                ):
                    flush()

        except Exception as e:
            print("Error during streaming iteration:", repr(e))
            import traceback

            traceback.print_exc()
            send_to_room(user_id, f"[Streaming error: {repr(e)}]", "error")

        # Final flush
        flush()

        # Handle case where no text was produced
        if not got_text:
            msg = "[No response generated]"
            if finish_reason == 1:
                msg = (
                    "[Response completed but no text generated - possibly due to content filtering]"
                )
            elif finish_reason == 2:
                msg = "[Response truncated due to max tokens limit]"
            elif finish_reason == 3:
                msg = "[Response blocked due to safety filters]"
            elif finish_reason == 4:
                msg = "[Response blocked due to recitation concerns]"
            elif finish_reason == 5:
                msg = "[Response generation stopped for other reasons]"

            send_to_room(user_id, msg, "message")

        send_to_room(user_id, "", "done")

    except Exception as e:
        import traceback

        print("Exception in fetch_and_stream_response_from_model:", repr(e))
        traceback.print_exc()
        send_to_room(user_id, f"Error: {repr(e)} ({type(e).__name__})", "error")


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

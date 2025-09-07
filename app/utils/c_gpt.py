import json
import re
import time
from typing import Any, Dict, List
import openai

from app.config import OPEN_AI_API_KEY
from app.utils.jwt_utils import create_token
from app.utils.ws_util import send_to_room

openai.api_key = OPEN_AI_API_KEY


def fetch_and_stream_response_from_model(
    message_for_model, user_id: str, type_key: str = "stream_message"
):
    message_streamed: str = ""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=message_for_model,
            temperature=0.3,
            stream=True,
        )
        buf, buf_chars = [], 0
        FLUSH_CHARS, FLUSH_SECS = 800, 0.5
        last = time.time()

        def flush():
            nonlocal buf, buf_chars, last, message_streamed
            if buf:
                message_streamed += "".join(buf)
                message_streamed += " "
                send_to_room(user_id, "".join(buf), "message", type_key)
                buf, buf_chars, last = [], 0, time.time()

        for chunk in resp:
            if "choices" not in chunk:
                continue
            ch = chunk["choices"][0]
            piece = ch.get("delta", {}).get("content")
            if piece:
                buf.append(piece)
                buf_chars += len(piece)
            if (
                buf_chars >= FLUSH_CHARS
                or (time.time() - last) >= FLUSH_SECS
                or (piece and "\n" in piece)
            ):
                flush()
            if ch.get("finish_reason"):
                break

        flush()
        send_to_room(user_id, "", "done", type_key)
        return message_streamed
    except Exception as e:
        send_to_room(user_id, f"Error: {e}", "error")
    return message_streamed


def fetch_response_from_model(message_for_model: List[Dict[str, Any]]):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=message_for_model,
            temperature=0.3,
        )

        content: str = response["choices"][0]["message"]["content"]
        if content.startswith("```"):
            content = re.sub(
                r"^```(?:json)?\n|```$", "", content.strip(), flags=re.IGNORECASE | re.MULTILINE
            ).strip()

        return json.loads(content)

    except Exception as e:
        print(f"Error occurred: {e}")

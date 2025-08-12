import json
import re
from typing import Any, Dict, List
import openai


from app.utils.jwt_utils import create_token
from app.utils.ws_util import send_to_socket

openai.api_key = "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"

def featch_and_stream_response_from_model(message_for_model: List[Dict[str, Any]], user_id: str):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=message_for_model,
            temperature=0.3,
            stream=True,
        )
        token = create_token(user_id=user_id)

        buffer = ""
        for chunk in response:
            if "choices" in chunk:
                delta = chunk["choices"][0].get("delta", {})
                content_piece = delta.get("content", "")
                if content_piece:
                    buffer += content_piece  # concatenate directly, no spaces
                    if len(buffer) >= 50:  # send after N characters
                        send_to_socket(message=buffer, user_id=user_id, token=token)
                        buffer = ""  # reset buffer

        if buffer:  # send any leftover text
            send_to_socket(message=buffer, user_id=user_id, token=token)

    except Exception as e:
        print(f"Error occurred: {e}")


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

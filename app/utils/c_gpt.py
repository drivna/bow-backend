import json
import re
from typing import Any, Dict, List
import openai


from app.utils.jwt_utils import create_token
from app.utils.ws_util import send_to_socket

openai.api_key = ''



def featch_and_stream_response_from_model(message_for_model: List[Dict[str, Any]], user_id: str):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=message_for_model,
            temperature=0.3,
            stream=True,
        )
        token = create_token(user_id=user_id)

        message_chunk_array = []
        for chunk in response:
            if "choices" in chunk:
                message = chunk["choices"][0].get("delta", {}).get("content")
                if message:
                    if len(message_chunk_array) == 10:
                        send_to_socket(
                            message=" ".join(message_chunk_array), user_id=user_id, token=token
                        )
                        message_chunk_array = []
                        message_chunk_array.append(message)
                    else:
                        message_chunk_array.append(message)
        if message_chunk_array:
            send_to_socket(message=" ".join(message_chunk_array), user_id=user_id, token=token)
            message_chunk_array = []

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

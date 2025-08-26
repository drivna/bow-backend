from app.constants import ChatGptMessagePayload, ChatGptPrompts
from app.utils.g_gpt import fetch_and_stream_response_from_model


def send_reply_to_user(user_message:str, file_content:str, user_id:str):
    prompt: str = ChatGptPrompts.get_chat_prompt(user_message=user_message, file_content=file_content)
    message_payload: str = ChatGptMessagePayload.get_message_payload(user_message=user_message, prompt=prompt)

    fetch_and_stream_response_from_model(
            message_for_model=message_payload, user_id=user_id
        )
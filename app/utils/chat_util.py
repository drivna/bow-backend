from typing import Optional

from loguru import logger
from app.constants import ChatGptMessagePayload, ChatGptPrompts
from app.database.models.chats import ChatModel
from app.database.models.file_chats import FileChatModel
from app.database.object_repository import ObjectRepository
from app.utils.c_gpt import fetch_and_stream_response_from_model


def send_reply_to_user(user_message: str, file_content: str, user_id: str, file_id: str):
    prompt: str = ChatGptPrompts.get_chat_prompt(
        user_message=user_message, file_content=file_content
    )
    message_payload: str = ChatGptMessagePayload.get_message_payload(
        user_message=user_message, prompt=prompt
    )

    reply_for_user: str = fetch_and_stream_response_from_model(
        message_for_model=message_payload, user_id=user_id, type_key="chat"
    )

    new_chat = ChatModel(user_id=user_id, message=reply_for_user, is_from_system=True)
    ObjectRepository.insert_single_object(new_chat)

    file_chat_entry = FileChatModel(user_id=user_id, chat_id=new_chat.id, file_id=file_id)
    ObjectRepository.insert_single_object(file_chat_entry)
    logger.info(f"Upsert fone for filechat: {file_chat_entry.id}")

    return

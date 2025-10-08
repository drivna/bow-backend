from typing import List, Optional, Tuple
from flask import request
from flask_restx import Namespace, Resource
from flask_restx.reqparse import RequestParser
from sqlalchemy.exc import SQLAlchemyError
from app.config import CUSTOM_USER_ID
from app.database import query_manager
from app.database.models.chats import ChatModel
from app.database.models.file import FileModel
from app.database.models.file_chats import FileChatModel
from app.database.models.file_topics import FileTopicModel
from app.database.object_repository import ObjectRepository
from app.middleware.auth import authenticate_user
from sqlalchemy.orm import aliased

from app.utils.chat_util import send_reply_to_user

chat_api_ns = Namespace("chats", description="APIs for Chats")


@chat_api_ns.route("/message")
class ChatRoute(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("message", help="Message content", required=True)
    parser.add_argument("fileId", help="File ID", required=False)

    @chat_api_ns.expect(parser)
    @authenticate_user
    def post(self):
        """
        Create a new chat message and optionally associate a file.
        """
        args = self.parser.parse_args()
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        message = args.get("message")
        file_id = args.get("fileId")

        new_chat = ChatModel(user_id=user_id, message=message, is_from_system=False)
        chat_entry = ObjectRepository.insert_single_object(new_chat)

        if file_id:
            file_entry = ObjectRepository.get_object_by_id(model=FileModel, object_id=file_id)
            if not file_entry:
                return {
                    "error": "FILE_NOT_FOUND",
                    "message": "The provided file ID does not exist.",
                    "data": None,
                }, 404

            file_chat_entry = FileChatModel(user_id=user_id, chat_id=chat_entry.id, file_id=file_id)

            ObjectRepository.insert_single_object(file_chat_entry)

        file: FileModel = ObjectRepository.get_object_by_id(model=FileModel, object_id=file_id)

        send_reply_to_user(
            user_message=message,
            user_id=user_id,
            file_id=file_id,
        )

        return {
            "error": None,
            "message": "Chat created successfully",
            "data": {
                "chatId": chat_entry.id,
                "message": chat_entry.message,
                "userId": chat_entry.user_id,
                "fileId": file_id if file_id else None,
                "is_from_system": chat_entry.is_from_system,
            },
        }, 201


@chat_api_ns.route("/")
class FileChatRoute(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="File ID", required=False)
    parser.add_argument("page", help="Page number", required=False, type=int, default=1)
    parser.add_argument(
        "per_page", help="Number of chats per page", required=False, type=int, default=100
    )

    @chat_api_ns.expect(parser)
    @authenticate_user
    def get(self):
        """
        Fetch chats for a user, paginated, and optionally filtered by file_id.
        """
        args = self.parser.parse_args()
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID
        file_id = args.get("fileId")
        page = args.get("page")
        per_page = args.get("per_page")

        filters = ChatModel.user_id == user_id

        if file_id:
            filters = (FileChatModel.file_id == file_id) & filters
            join = (FileChatModel, ChatModel.id == FileChatModel.chat_id)
        else:
            join = (FileChatModel, ChatModel.id == FileChatModel.chat_id)

        order_by = [ChatModel.updated_at.desc()]
        limit = per_page
        offset = (page - 1) * per_page

        chats: List[Tuple[ChatModel, FileChatModel]] = query_manager.query_with_join_and_filter(
            model=(ChatModel, FileChatModel),
            join=join,
            isouter=True,
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )
        total_count = query_manager.query_count_with_join_filter(
            model=(ChatModel, FileChatModel),
            join=join,
            isouter=True,
            filters=filters,
        )

        if page is not None and per_page is not None:
            hasNext: bool = page * per_page < total_count
        else:
            hasNext = False

        response = []
        for row in chats:
            chat: ChatModel = row[0]
            file_chat: Optional[FileChatModel] = row[1]
            res = {
                "id": chat.id,
                "message": chat.message,
                "uploaded_at": chat.updated_at.isoformat(),
                "file_id": file_chat.file_id if file_chat else None,
                "is_from_system": chat.is_from_system,
            }
            response.append(res)

        return {
            "error": None,
            "message": "Chats fetched successfully",
            "data": {"messages": response, "hasNext": hasNext, "countTotalChats": total_count},
        }, 200

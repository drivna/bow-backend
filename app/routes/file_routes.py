from datetime import datetime
from typing import Any, Dict, List
from flask_restx import Namespace, Resource
from flask import request
from werkzeug.datastructures import FileStorage
import os
import threading
from flask_restx.reqparse import ParseResult, RequestParser

from app.config import CUSTOM_USER_ID
from app.constants import QUEUE_MODE_ON
from app.database import query_manager
from app.database.models.file import FileModel
from app.database.models.file_topics import FileTopicModel
from app.database.object_repository import ObjectRepository
from app.middleware.auth import authenticate_user
from app.queue.redis_queue import enqueue_job
from app.utils.activity_util import create_activity_for_file_read
from app.utils.file_util import (
    fetch_and_store_embeddings_for_pdf,
    process_and_create_action_items_for_file_in_bg,
    process_and_create_action_items_for_file_in_fg,
)
from app.utils.pdf_util import get_file_hash, read_pdf_text
from app.utils.quiz_util import generate_quiz_for_file
from app.utils.storage_util import get_signed_url, upload_pdf_bytes
from app.utils.topic_utils import generate_topics_for_file_and_update_knowledge_map
from app.utils.ws_util import send_to_room

file_api_ns = Namespace("files", description="APIs for file upload and parsing")

UPLOAD_FOLDER = "uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@file_api_ns.route("/pdf/parse")
class FileParsingRoutes(Resource):
    @file_api_ns.expect(
        file_api_ns.parser().add_argument(
            "file", location="files", type=FileStorage, required=True, help="File to be uploaded"
        )
    )
    @authenticate_user
    def post(self):
        uploaded_file = request.files.get("file")
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        if not uploaded_file:
            return {
                "error": "No file provided",
                "message": "Please attach a file in the request",
            }, 400

        is_new_created_file: bool = True
        text_pages_of_file = []
        try:
            file_bytes = uploaded_file.read()
            filename = f"{uploaded_file.filename}_{datetime.now().timestamp()}"  # NOTE: FIX THIS

            file_content = read_pdf_text(file_bytes)
            text_pages_of_file = file_content
            file_content = [text.replace("\x00", "") for text in file_content]
            file_hash = get_file_hash(file_content=file_content)
            file_object = FileModel(
                uploaded_by=user_id,
                file_name=filename,
                file_hash=file_hash,
                file_content=file_content,
                file_type="pdf",
            )
            try:
                file_exists = ObjectRepository.get_object_by_id(
                    model=FileModel, object_id=file_object.id
                )
                if file_exists:
                    is_new_created_file = False
            except Exception:
                pass

            saved_file: FileModel = ObjectRepository.insert_single_object(
                object_to_be_inserted=file_object
            )

        except Exception as e:
            return {"error": str(e), "message": "Failed to save the file"}, 500

        if is_new_created_file is True:
            # Uploading to bucket
            upload_pdf_bytes(file_bytes=file_bytes, destination_blob_name=saved_file.file_name)

            print("Going for async tasks")
            fetch_and_store_embeddings_for_pdf(file_content=text_pages_of_file, user_id=user_id)
            if not QUEUE_MODE_ON:
                thread = threading.Thread(
                    target=process_and_create_action_items_for_file_in_fg,
                    kwargs={"file_id": saved_file.id, "user_id": user_id},
                )
                thread.start()
            else:
                print("Sending to queue")
                process_and_create_action_items_for_file_in_bg.apply_async(
                    kwargs={"file_id": saved_file.id, "user_id": user_id}
                )

        create_activity_for_file_read(
            file_id=saved_file.id, file_name=uploaded_file.filename, user_id=user_id
        )

        send_to_room(user_id=user_id, message="Hello! Welcome to Bow", key="chat")
        signed_url = get_signed_url(blob_name=saved_file.file_name, expiration_days=1)

        return {
            "error": None,
            "message": "File uploaded, saved and parsed successfully",
            "data": {
                "file_name": saved_file.file_name,
                "content": file_content,
                "file_id": saved_file.id,
                'signed_url': signed_url
            },
        }, 201


@file_api_ns.route("")
class FileParsingRoutes(Resource):
    @authenticate_user
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        files_of_user: List[FileModel] = query_manager.query_with_filter(
            model=FileModel,
            filters=(FileModel.uploaded_by == user_id),
            order_by=FileModel.updated_at.desc(),
        )

        response: List[Dict[str, Any]] = []
        for file in files_of_user:
            topics_and_pages_of_file: List[FileTopicModel] = query_manager.query_with_filter(
                model=FileTopicModel, filters=(FileTopicModel.file_id == file.id)
            )

            topics_response_for_file: List[Dict[str, Any]] = []
            for topic in topics_and_pages_of_file:
                topic_res = {
                    "id": topic.id,
                    "page": topic.page_number,
                    "topicName": topic.topic_name,
                    "topicDescription": topic.topic_description,
                }
                topics_response_for_file.append(topic_res)

            res = {
                "id": file.id,
                "name": file.file_name,
                "file_type": file.file_type,
                "uploaded_at": file.updated_at.isoformat(),
                "topics": topics_response_for_file,
            }

            response.append(res)

        return {
            "error": None,
            "message": "File uploaded, saved and parsed successfully",
            "data": response,
        }, 201


@file_api_ns.route("/signed_url")
class FileParsingRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="File Id", required=True)

    @file_api_ns.expect(parser)
    @authenticate_user
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")

        file: FileModel = ObjectRepository.get_object_by_id(model=FileModel, object_id=file_id)
        if not file:
            return {
                "error": "NO_FILE_FOUND",
                "message": "No file found",
                "data": {},
            }, 400

        signed_url = get_signed_url(blob_name=file.file_name, expiration_days=1)

        return {
            "error": None,
            "message": "File uploaded, saved and parsed successfully",
            "data": {"url": signed_url},
        }, 201


@file_api_ns.route("/topic_detail")
class FileTopicRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("topicName", help="Topic Name", required=True)

    @file_api_ns.expect(parser)
    # @authenticate_user
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        args: ParseResult = self.parser.parse_args()
        topic_name: str = args.get("topicName")

        if not topic_name:
            return {
                "error": "INVALID/MISSING_TOPIC_NAME",
                "message": "No Topic name provided",
                "data": [],
            }, 200

        topic_from_db: List[FileTopicModel] = query_manager.query_with_filter(
            model=FileTopicModel,
            filters=FileTopicModel.topic_name.like(f"%{topic_name}%"),
            order_by=FileTopicModel.updated_at.desc(),
        )

        if not topic_from_db:
            return {
                "error": "TOPIC_NOT_FOUND",
                "message": f"No records found for topic: {topic_name}",
                "data": [],
            }, 200

        file_ids = list({topic.file_id for topic in topic_from_db})

        return {
            "error": None,
            "message": "Topic details fetched successfully",
            "data": {
                "fileIds": file_ids,
                "topicDescription": topic_from_db[0].topic_description,
            },
        }, 200

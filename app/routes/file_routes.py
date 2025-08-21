from datetime import datetime
from typing import Any, Dict, List
from flask_restx import Namespace, Resource
from flask import request
from werkzeug.datastructures import FileStorage
import os
import threading

from app.database import query_manager
from app.database.models.file import FileModel
from app.database.models.file_topics import FileTopicModel
from app.database.object_repository import ObjectRepository
from app.middleware.auth import authenticate_user
from app.utils.file_util import process_and_create_action_items_for_file
from app.utils.pdf_util import get_file_hash, read_pdf_text
from app.utils.quiz_util import generate_quiz_for_file
from app.utils.topic_utils import generate_topics_for_file_and_update_knowledge_map

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
        user_id = request.user_id

        if not uploaded_file:
            return {
                "error": "No file provided",
                "message": "Please attach a file in the request",
            }, 400

        is_new_created_file: bool = True

        try:
            file_bytes = uploaded_file.read()
            filename = f"{uploaded_file.filename}_{datetime.now().timestamp()}"  # NOTE: FIX THIS

            file_content = read_pdf_text(file_bytes)
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
            thread = threading.Thread(
                target=process_and_create_action_items_for_file,
                kwargs={"file_object": file_object, "user_id": user_id},
            )
            thread.start()

        return {
            "error": None,
            "message": "File uploaded, saved and parsed successfully",
            "data": {
                "file_name": saved_file.file_name,
                "content": file_content,
                "file_id": saved_file.id,
            },
        }, 201


@file_api_ns.route("")
class FileParsingRoutes(Resource):
    @authenticate_user
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = 'user_17ae337cff'


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

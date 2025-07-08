from datetime import datetime
from flask_restx import Namespace, Resource
from flask import request
from werkzeug.datastructures import FileStorage
import os

from app.database.models.file import FileModel
from app.database.object_repository import ObjectRepository
from app.middleware.auth import authenticate_user
from app.utils.pdf_util import get_file_hash, read_pdf_text

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
            saved_file: FileModel = ObjectRepository.insert_single_object(
                object_to_be_inserted=file_object
            )

        except Exception as e:
            return {"error": str(e), "message": "Failed to save the file"}, 500

        return {
            "error": None,
            "message": "File uploaded, saved and parsed successfully",
            "data": {
                "file_name": saved_file.file_name,
                "content": file_content,
                "file_id": saved_file.id,
            },
        }, 201

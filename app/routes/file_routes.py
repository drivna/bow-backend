from flask_restx import Namespace, Resource
from flask import request
from werkzeug.datastructures import FileStorage
import os

from app.utils.pdf_util import read_pdf_text

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
    def post(self):
        uploaded_file = request.files.get("file")

        if not uploaded_file:
            return {
                "error": "No file provided",
                "message": "Please attach a file in the request",
            }, 400

        # Parsing file
        try:
            file_bytes = uploaded_file.read()

            # Parse text from PDF
            file_content = read_pdf_text(file_bytes)

            filename = f"{uploaded_file.filename}"
            save_path = os.path.join(UPLOAD_FOLDER, filename)

            uploaded_file.save(save_path)
        except Exception as e:
            return {"error": str(e), "message": "Failed to save the file"}, 500

        return {
            "error": None,
            "message": "File uploaded, saved and parsed successfully",
            "data": {"file_name": uploaded_file.filename, "content": file_content},
        }, 201

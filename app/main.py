import os
from typing import List
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api
from loguru import logger
import socketio

from requests import Response

from app.config import OPEN_AI_API_KEY
from app.exceptions.forbidden_error import ForbiddenError
from app.exceptions.invalid_argument_exception import InvalidArgumentException

from .database import query_manager  # noqa: F401
from app.routes.user_routes import user_api_ns
from app.routes.file_routes import file_api_ns
from app.routes.action_routes import action_api_ns
from app.routes.flashcard_routes import flashcard_api_ns
from app.routes.quiz_route import quiz_api_ns
from app.routes.chat_routes import chat_api_ns
from app.routes.internal_routes import internal_api_ns
from app.routes.notification_routes import notification_api_ns

environment = os.getenv("ENVIRONMENT")
app = Flask(__name__)
print(OPEN_AI_API_KEY)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size


app.config["PROPAGATE_EXCEPTIONS"] = True

app.app_context()

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

api = Api(app)
api.add_namespace(user_api_ns)
api.add_namespace(file_api_ns)
api.add_namespace(action_api_ns)
api.add_namespace(flashcard_api_ns)
api.add_namespace(quiz_api_ns)
api.add_namespace(chat_api_ns)
api.add_namespace(internal_api_ns)
api.add_namespace(notification_api_ns)


@app.errorhandler(InvalidArgumentException)
def handle_invalid_argument_exception(error):
    response = jsonify({"error": "INVALID_ARGUMENT", "message": error.args[0]})
    response.status_code = 400  # Bad Request
    return response


@app.errorhandler(RuntimeError)
def handle_runtime_exception(error):
    logger.error(error, exc_info=True)
    if hasattr(error, "args") and len(error.args) > 0:
        response = jsonify({"error": "RUNTIME_ERROR", "message": error.args[0], "data": None})
    elif hasattr(error, "message"):
        response = jsonify({"error": "RUNTIME_ERROR", "message": error.message, "data": None})
    else:
        response = jsonify({"error": "RUNTIME_ERROR", "message": str(error), "data": None})
    response.status_code = 500  # Internal Server Error

    return response


@app.errorhandler(ValueError)
def handle_value_error(error) -> Response:
    response: Response = jsonify({"error": "VALUE_ERROR", "message": error.args[0], "data": None})
    response.status_code = 400  # Bad Request
    return response


# Custom 404 error handler
@app.errorhandler(404)
def page_not_found(error):
    return {
        "error": "PATH_NOT_FOUND",
        "message": f"error = {str(error)} | url = {request.url}",
        "data": None,
    }, 404


# Custom 403 error handler
@app.errorhandler(ForbiddenError)
def forbidden_request(error):
    return {
        "error": "INVALID_USER_TOKEN",
        "message": error.args[0],
        "data": None,
    }, 403


@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(error, exc_info=True)
    if hasattr(error, "args") and len(error.args) > 0:
        response = jsonify({"error": error.args[0]})
    elif hasattr(error, "message"):
        response = jsonify({"error": error.message})
    else:
        response = jsonify({"error": str(error)})
    response.status_code = 500  # Internal Server Error

    return response


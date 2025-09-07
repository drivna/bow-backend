import os
from typing import List
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api
import socketio

from requests import Response

from app.config import OPEN_AI_API_KEY

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

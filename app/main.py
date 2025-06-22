import os
from typing import List
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api
import socketio

from requests import Response

from .database import query_manager  # noqa: F401
from app.routes.user_routes import user_api_ns
from app.routes.file_routes import file_api_ns
from app.routes.action_routes import action_api_ns

environment = os.getenv("ENVIRONMENT")
app = Flask(__name__)
socket_client = socketio.Client()
socket_client.connect("http://localhost:4001")

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size


app.config["PROPAGATE_EXCEPTIONS"] = True

app.app_context()

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

api = Api(app)
api.add_namespace(user_api_ns)
api.add_namespace(file_api_ns)
api.add_namespace(action_api_ns)

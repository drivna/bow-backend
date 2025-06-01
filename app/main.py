import os
from typing import List
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_restx import Api

from requests import Response


environment = os.getenv("ENVIRONMENT")
app = Flask(__name__)


app.config["PROPAGATE_EXCEPTIONS"] = True

app.app_context()

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

api = Api(app)


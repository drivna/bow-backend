from flask_cors import CORS

from app.config import APP_PORT
from app.main import app

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT, debug=True)

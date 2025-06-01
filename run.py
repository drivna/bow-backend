from flask_cors import CORS

from app.main import app

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

if __name__ == "__main__":
    app.run(debug=True, port=4000)

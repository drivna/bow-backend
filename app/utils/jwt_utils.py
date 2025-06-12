import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError
from typing import Dict, Union, Optional

from app.exceptions.forbidden_error import ForbiddenError

load_dotenv()

SECRET = os.getenv("JWT_SECRET", "766263142092493fa742bdfc424140d6")


def create_token(user_id: Optional[str] = None) -> str:
    payload: Dict[str, Union[str, datetime]] = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30),
    }
    encoded_jwt: str = jwt.encode(payload, SECRET, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> Dict:
    try:
        decoded_jwt = jwt.decode(token, SECRET, algorithms=["HS256"])
        return decoded_jwt
    except ExpiredSignatureError:
        return {"error": "Token expired"}
    except InvalidSignatureError:
        raise ForbiddenError("Token is invalid. Login to get access.")
    except Exception:
        raise ForbiddenError("Token is invalid. Login to get access.")


def get_attribute_from_token(token: str, attr_name: str) -> str:
    decoded_jwt_dict = decode_token(token=token)

    if attr_name not in decoded_jwt_dict:
        raise RuntimeError(f"{attr_name} not present in JWT")

    return decoded_jwt_dict[attr_name]

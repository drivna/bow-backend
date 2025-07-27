from functools import wraps
from flask import request, Response

from app.exceptions.forbidden_error import ForbiddenError
from app.utils.jwt_utils import get_attribute_from_token, create_token


def add_token_to_cookies(response: Response, registered_user_id: str):
    if response.status_code >= 300 or response.status_code < 200:
        return response
    expiry_days: int = 30

    access_token: str = create_token(user_id=registered_user_id)
    expires: int = expiry_days * 24 * 60 * 60

    response.set_cookie(
        "token",
        access_token,
        httponly=True,
        max_age=expires,
        samesite="Lax",  # ✅ Lax works fine for most cases on same-origin requests
        secure=False,  # ✅ Must be False for HTTP (localhost)
    )

    return response


def authenticate_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token: str = request.cookies.get("token")
        print(1, request.cookies)
        if token is None:
            raise ForbiddenError("User is not logged in. Please sign-in to continue")
        try:
            request.user_id: str = get_attribute_from_token(token=token, attr_name="user_id")
        except Exception:
            raise ForbiddenError("Token is invalid. Login to get access.")
        return func(*args, **kwargs)

    return wrapper

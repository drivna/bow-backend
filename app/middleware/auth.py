from functools import wraps
from flask import request, Response

from app.database.models.user import UserModel
from app.database.object_repository import ObjectRepository
from app.exceptions.forbidden_error import ForbiddenError
from app.utils.jwt_utils import get_attribute_from_token, create_token


def check_user_account_is_active(user_id: str):
    try:
        user: UserModel = ObjectRepository.get_object_by_id(model=UserModel, object_id=user_id)
        if user.is_active is True:
            return True
        else:
            return False
    except Exception:
        return False


def add_token_to_cookies(response: Response, registered_user_id: str):
    if response.status_code >= 300 or response.status_code < 200:
        return response

    if not check_user_account_is_active(user_id=registered_user_id):
        return response

    expiry_days: int = 30

    access_token: str = create_token(user_id=registered_user_id)
    expires: int = expiry_days * 24 * 60 * 60

    response.set_cookie(
        "token",
        access_token,
        httponly=True,
        max_age=expires,
        samesite="none",  # must be string, not None
        secure=True,  # required for cross-site cookies
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
            user_id: str = get_attribute_from_token(token=token, attr_name="user_id")
            if check_user_account_is_active(user_id=user_id):
                request.user_id: str = user_id
            else:
                raise ForbiddenError("Token is invalid. Login to get access.")
        except Exception:
            raise ForbiddenError("Token is invalid. Login to get access.")
        return func(*args, **kwargs)

    return wrapper

from flask_restx import Namespace, fields, Model
from typing import Any, Dict, Tuple, List
from flask_restx import Namespace, Resource
from flask import Response, after_this_request, request
from loguru import logger
from sqlalchemy import and_

from app.config import CUSTOM_USER_ID
from app.database import query_manager
from app.database.models.activity import ActivityModel
from app.database.models.user import UserModel
from app.database.object_repository import ObjectRepository
from app.middleware.auth import add_token_to_cookies, authenticate_user
from app.utils.activity_util import (
    get_user_files_count,
    get_user_flashcard_count,
    get_user_quiz_count,
)
from app.utils.jwt_utils import create_token, get_attribute_from_token
from app.utils.password_utils import are_passwords_matching, hash_password
from flask_restx.reqparse import ParseResult, RequestParser

user_api_ns = Namespace("users", description="APIs for users")


def get_login_api_request_model(namespace):
    request_model = namespace.model(
        "LoginUserApiRequestModel",
        {
            "email": fields.String(
                required=True,
                description="Email of the user",
                help="Email of user is required",
            ),
            "password": fields.String(
                required=True,
                description="Password of the user",
                help="Password of user is required",
            ),
        },
    )
    return request_model


@user_api_ns.route("/register")
class UserRegistrationRoutes(Resource):
    def post(self) -> Tuple[Dict[str, Any], int]:
        @after_this_request
        def add_token(response: Response):
            try:
                if response.status_code >= 300 or response.status_code < 200:
                    return response
                return add_token_to_cookies(response=response, registered_user_id=user_id)
            except Exception as e:
                logger.error(e.args, exc_info=True)
                return response

        request_data: Dict[str, List[Dict[str, Any]]] = request.json  # type: ignore
        user_name: str = request_data.get("user_name")
        email: str = request_data.get("email")
        password: str = request_data.get("password")

        user: UserModel = UserModel(
            user_name=user_name,
            email=email,
            password=hash_password(password),
        )

        ObjectRepository.insert_single_object(object_to_be_inserted=user)
        user_id = user.id
        access_token: str = create_token(user_id=user_id)
        return {
            "error": None,
            "message": "user created successfully",
            "data": {"id": user_id, "access_token": access_token},
        }, 201


@user_api_ns.route("/login")
class UserLoginRoutes(Resource):
    @user_api_ns.expect(get_login_api_request_model(namespace=user_api_ns), validate=True)
    def post(self) -> Tuple[Dict[str, Any], int]:
        @after_this_request
        def add_token(response: Response):
            try:
                if response.status_code >= 300 or response.status_code < 200:
                    return response
                return add_token_to_cookies(response=response, registered_user_id=user_id)
            except Exception as e:
                logger.error(e.args, exc_info=True)
                return response

        request_data: Dict[str, List[Dict[str, Any]]] = request.json  # type: ignore
        email: str = request_data.get("email")
        password: str = request_data.get("password")

        exisitng_user: List[UserModel] = query_manager.query_with_filter(
            model=UserModel, filters=and_(UserModel.email == email)
        )
        if len(exisitng_user) > 1:
            raise ValueError("More than 1 users found for the email, please contact admin")
        elif len(exisitng_user) == 0:
            raise ValueError("No user found for the email")

        user = exisitng_user[0]

        are_passwords_same = are_passwords_matching(
            password_to_check=password, hashed_password=user.password
        )
        if not are_passwords_same:
            raise ValueError("Incorrect email or password provided")

        user_id = user.id
        access_token: str = create_token(user_id=user_id)

        return {
            "error": None,
            "message": "user logged in successfully",
            "data": {"id": user_id, "access_token": access_token},
        }, 201


@user_api_ns.route("/socket/auth")
class UserSocketAuthRoute(Resource):
    def get(self) -> Tuple[Dict[str, Any], int]:
        user_token: str = request.headers.get("Authorization")
        user_id: str = get_attribute_from_token(token=user_token, attr_name="user_id")
        return {
            "error": None,
            "message": "user authenticated successfully",
            "data": {"id": user_id},
        }, 201


@user_api_ns.route("/activity")
class UserActivityRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("page", help="Page Number", type=int, required=False)
    parser.add_argument("perPage", help="Count per page", type=int, required=False)

    @user_api_ns.expect(parser)
    @authenticate_user
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        args: ParseResult = self.parser.parse_args()

        page: int = args.get("page", 1)
        per_page: int = args.get("perPage", 10)

        activities_of_user: List[ActivityModel] = query_manager.query_with_filter(
            model=ActivityModel,
            filters=(ActivityModel.user_id == user_id),
            order_by=ActivityModel.created_at.desc(),
            limit=per_page,
            offset=(page - 1) * per_page,
        )

        count_of_activities = query_manager.query_count_with_filter(
            model=ActivityModel,
            filters=(ActivityModel.user_id == user_id),
        )

        has_next: bool = page * per_page < count_of_activities

        response: List[Dict[str, Any]] = []
        for activity in activities_of_user:
            res = {
                "id": activity.id,
                "user_id": activity.user_id,
                "activity_type": activity.activity_type,
                "activity_item_id": activity.activity_item_id,
                "activity_description": activity.activity_description,
                "created_at_date": str(activity.created_at.date()),
                "created_at": str(activity.created_at),
            }
            response.append(res)

        return {
            "error": None,
            "message": "User activities fetched successfully",
            "data": {
                "activities": response,
                "countTotalActivites": count_of_activities,
                "hasNextPage": has_next,
            },
        }, 200


@user_api_ns.route("/profile")
class UserProfileRoutes(Resource):
    @authenticate_user
    def get(self):
        try:
            user_id = request.user_id
        except Exception:
            user_id = CUSTOM_USER_ID

        user: UserModel = ObjectRepository.get_object_by_id(model=UserModel, object_id=user_id)

        return {
            "error": None,
            "message": "User activities fetched successfully",
            "data": {
                "name": user.user_name,
                "email": user.email,
                "registration_date": str(user.created_at.date()),
                "quiz_count": get_user_quiz_count(user_id=user_id),
                "flashcards_count": get_user_flashcard_count(user_id=user_id),
                "files_count": get_user_files_count(user_id=user_id),
            },
        }, 200

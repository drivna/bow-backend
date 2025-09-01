from flask import request
from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser
from loguru import logger
from sqlalchemy.orm import joinedload

from app.constants import ChatGptPrompts, ChatGptMessagePayload
from app.database import query_manager
from app.database.models.file import FileModel
from app.database.models.file_topics import FileTopicModel
from app.database.models.flashcard_qna import FlashCardQnAModel
from app.database.models.flashcards import FlashCardModel
from app.database.models.quiz import QuizModel
from app.database.object_repository import ObjectRepository
from app.middleware.auth import authenticate_user
from app.utils.activity_util import create_activity_for_flashcard
from app.utils.flashcard_util import generate_flashcard_for_file
from app.utils.g_gpt import fetch_and_stream_response_from_model, fetch_response_from_model
from typing import List, Dict, Any, Optional

from app.utils.knwoledge_map_util import (
    get_knowledge_map_for_user,
    update_full_knowledge_map_for_file,
)
from app.utils.qna_util import insert_flashcard_qna_in_db
from app.utils.quiz_util import (
    create_new_quiz_in_db,
    generate_quiz_for_difficulty,
    generate_quiz_for_file,
    get_all_questions_generated_for_file,
)
from app.utils.topic_utils import generate_topics_for_file_and_update_knowledge_map

action_api_ns = Namespace("action", description="APIs for actions")


@action_api_ns.route("/summarise")
class ActionSummaryRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=True)
    parser.add_argument("userSelectedContent", help="custom_content", required=False)

    @action_api_ns.expect(parser)
    def post(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        custom_content: str = args.get("userSelectedContent", None)
        file_object: FileModel = ObjectRepository.get_object_by_id(
            model=FileModel, object_id=file_id
        )

        if custom_content is None:
            system_prompt_for_summary_agent: str = ChatGptPrompts.get_pdf_summary_prompt()
            message_for_model: List[
                Dict[str, Any]
            ] = ChatGptMessagePayload.get_mesasage_payload_for_entire_pdf_summary(
                prompt=system_prompt_for_summary_agent, pdf_text=file_object.file_content
            )
        else:
            system_prompt_for_summary_agent = (
                ChatGptPrompts.get_pdf_selected_content_summary_prompt()
            )
            message_for_model = (
                ChatGptMessagePayload.get_mesasage_payload_for_selected_content_in_pdf_summary(
                    prompt=system_prompt_for_summary_agent,
                    pdf_content=file_object.file_content,
                    selected_content=custom_content,
                )
            )

        fetch_and_stream_response_from_model(
            message_for_model=message_for_model, user_id=request.user_id
        )

        return {}


@action_api_ns.route("/flashcard")
class ActionFlashCardRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=True)

    @action_api_ns.expect(parser)
    def post(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        try:
            user_id: str = request.user_id
        except Exception:
            user_id = "user_17ae337cff"
        file_object: FileModel = ObjectRepository.get_object_by_id(
            model=FileModel, object_id=file_id
        )
        response, total_flashcard_count = generate_flashcard_for_file(file_id=file_id, user_id=user_id)

        create_activity_for_flashcard(
            file_id=file_id,
            user_id=user_id,
            file_name=file_object.file_name,
            flashcards_count=total_flashcard_count,
        )

        return {
            "error": None,
            "message": "flashcards generated successfully",
            "data": response,
        }, 201


@action_api_ns.route("/quiz")
class ActionQuizRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=True)
    parser.add_argument("topic", help="TopicId", required=False)

    @action_api_ns.expect(parser)
    @authenticate_user
    def post(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        user_id: str = request.user_id

        topic: str = args.get("topic", "")
        topics_list = topic.split(",")

        topics_for_quiz: List[str] = []

        for topic_id in topics_list:
            topic_model: FileTopicModel = ObjectRepository.get_object_by_id(
                model=FileTopicModel, object_id=topic_id
            )
            topics_for_quiz.append(topic_model.topic_description)

        generate_quiz_for_file(file_id=file_id, user_id=user_id)

        return {
            "error": None,
            "message": "Quiz generated successfully",
            "data": [],
        }, 201


@action_api_ns.route("/knowledgeMap")
class ActionKnowledgeMapRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=False)

    @action_api_ns.expect(parser)
    @authenticate_user
    def get(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        try:
            user_id: str = request.user_id
        except Exception:
            user_id = "user_17ae337cff"

        data = get_knowledge_map_for_user(user_id=user_id, file_id=file_id)

        return {"error": None, "message": "Knowledge map fetched successfully", "data": data}, 200

    post_parser = RequestParser()
    post_parser.add_argument("fileId", help="FileId", required=True)

    @action_api_ns.expect(post_parser)
    @authenticate_user
    def post(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        try:
            user_id: str = request.user_id
        except Exception:
            user_id = "user_17ae337cff"

        file: FileModel = ObjectRepository.get_object_by_id(model=FileModel, object_id=file_id)
        if not file:
            return {
                "error": "INVALID_FILE_ID",
                "message": "File not found",
                "data": [],
            }, 201

        topics_of_file: List[FileTopicModel] = query_manager.query_with_filter(
            model=FileTopicModel, filters=(FileTopicModel.file_id == file.id)
        )
        if not topics_of_file:
            generate_topics_for_file_and_update_knowledge_map(
                file_content=file.file_content, file_id=file_id, user_id=user_id
            )
        else:
            page_wise_topics = {}

            for topic_for_file in topics_of_file:
                page_number = topic_for_file.page_number
                if page_number in page_wise_topics:
                    page_wise_topics[page_number].append(topic_for_file.topic_name)
                else:
                    page_wise_topics[page_number] = [topic_for_file.topic_name]

            for page in page_wise_topics:
                km_result = update_full_knowledge_map_for_file(
                    user_id=user_id,
                    file_id=file_id,
                    topics_list=page_wise_topics[page],
                    page_number=page_number,
                )
                logger.info(f"Knowledge map updated for file={file_id}, result={km_result}")

        return {
            "error": None,
            "message": "Update knowledge map for user",
            "data": [],
        }, 201

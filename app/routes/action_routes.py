from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser
from loguru import logger
from sqlalchemy.orm import joinedload

from app.constants import ChatGptPrompts, ChatGptMessagePayload
from app.database import query_manager
from app.database.models.file import FileModel
from app.database.models.flashcard_qna import FlashCardQnAModel
from app.database.models.flashcards import FlashCardModel
from app.database.models.qna import QNAModel, QuestionSource
from app.database.models.quiz import QuizModel
from app.database.object_repository import ObjectRepository
from app.utils.c_gpt import featch_and_stream_response_from_model, fetch_response_from_model
from typing import List, Dict, Any

from app.utils.qna_util import insert_flashcard_qna_in_db
from app.utils.quiz_util import create_new_quiz_in_db, generate_quiz_for_difficulty

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

        featch_and_stream_response_from_model(
            message_for_model=message_for_model, user_id="user_17ae337cff"
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
        user_id: str = "user_17ae337cff"

        file_object: FileModel = ObjectRepository.get_object_by_id(
            model=FileModel, object_id=file_id
        )
        existing_flashcards_for_file: List[FlashCardModel] = query_manager.query_with_filter(
            model=FlashCardModel, filters=(FlashCardModel.file_id == file_id)
        )
        previous_questions: List[str] = []
        for existing_flashcard in existing_flashcards_for_file:
            qna_for_existing_flashcards: List[FlashCardQnAModel] = query_manager.query_with_filter(
                model=FlashCardQnAModel,
                filters=(FlashCardQnAModel.flashcard_id == existing_flashcard.id),
                options=[joinedload(FlashCardQnAModel.qna)],
            )
            previous_questions.extend([fqna.qna.question for fqna in qna_for_existing_flashcards])

        system_prompt_for_flashcard_agent = ChatGptPrompts.get_flashcard_generation_prompt(
            previous_questions=previous_questions
        )
        message_for_model = ChatGptMessagePayload.get_message_payload_for_pdf_questions(
            prompt=system_prompt_for_flashcard_agent,
            pdf_content=file_object.file_content,
        )
        response = fetch_response_from_model(message_for_model=message_for_model)

        flashcard: FlashCardModel = FlashCardModel(user_id=user_id, file_id=file_id)

        inserted_flashcard = ObjectRepository.insert_single_object(object_to_be_inserted=flashcard)

        for res in response.get("questions", []):
            question: str = res.get("value")
            answer: str = res.get("answer")
            insert_flashcard_qna_in_db(
                question=question, answer=answer, flashcard_id=inserted_flashcard.id
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

    @action_api_ns.expect(parser)
    def post(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        user_id: str = "user_17ae337cff"

        file_object: FileModel = ObjectRepository.get_object_by_id(
            model=FileModel, object_id=file_id
        )

        for difficulty in ['easy', 'medium','hard']:
            response = generate_quiz_for_difficulty(file_content=file_object.file_content, difficulty=difficulty)

            create_new_quiz_in_db(
                user_id=user_id, quiz_data=response, file_id=file_id
            )

        return {
            "error": None,
            "message": "Quiz generated successfully",
            "data": [],
        }, 201

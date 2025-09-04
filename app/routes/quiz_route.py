import threading
from typing import Any, Dict, List, Optional
from flask import request
from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser
from loguru import logger
from sqlalchemy import and_, cast, not_
from sqlalchemy.orm import joinedload
from app.database import query_manager
from app.database.models.flashcards import FlashCardModel
from app.database.models.qna import QNAModel
from app.database.models.qna_actions import QNAActions
from app.database.models.flashcard_qna import FlashCardQnAModel
from app.database.models.quiz import QuizModel
from app.database.models.quiz_answers import QuizUserAnswersModel
from app.database.models.qna import QNAModel
from app.database.models.quiz_qna import DifficultyLevel, QuizQnAModel
from app.database.object_repository import ObjectRepository
from app.middleware.auth import authenticate_user
from app.utils.activity_util import create_activity_for_quiz
from app.utils.quiz_util import (
    check_and_fetch_latest_question_for_quiz,
    check_and_generate_more_questions,
    format_quiz_qna_for_response,
    get_list_of_quiz,
    get_quiz_by_id,
    handle_answer_and_generate_new_question_for_quiz,
    update_all_questions_for_quiz,
    update_quiz_question,
    update_quiz_summary,
)
from sqlalchemy.dialects.postgresql import JSONB

quiz_api_ns = Namespace("quiz", description="APIs for quiz")


@quiz_api_ns.route("/list")
class QuizRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=False)
    parser.add_argument("quizType", help="QuizType", required=True)
    parser.add_argument("page", help="Page Number", type=int, required=False)
    parser.add_argument("perPage", help="Count per page", type=int, required=False)

    @quiz_api_ns.expect(parser)
    @authenticate_user
    def get(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        quiz_type: str = args.get("quizType")
        page: int = args.get("page", 1)
        per_page: int = args.get("perPage", 10)
        user_id: str = request.user_id
        # user_id: str = "user_17ae337cff"
        # if file_id is None:
        #     file_id='file_be44cbafe5'

        if quiz_type not in ["new", "old", "live"]:
            return {
                "error": None,
                "message": "Invalid Quiz Type",
                "data": [],
            }, 400

        [quiz_list_for_user, total_count] = get_list_of_quiz(
            user_id=user_id, file_id=file_id, quiz_type=quiz_type, page=page, per_page=per_page
        )

        if page is not None and per_page is not None:
            hasNext: bool = page * per_page < total_count
        else:
            hasNext = False

        return {
            "error": None,
            "message": "Quiz generated successfully",
            "data": {
                "quizzes": [quiz.to_dict() for quiz in quiz_list_for_user],
                "countTotalQuizzes": total_count,
                "hasNext": hasNext,
            },
        }, 201


@quiz_api_ns.route("/question")
class QuizRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=True)
    parser.add_argument("quizId", help="QuizId", required=True)

    @quiz_api_ns.expect(parser)
    @authenticate_user
    def get(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        quiz_id: str = args.get("quizId")
        user_id: str = request.user_id

        quiz_object: QuizModel = ObjectRepository.get_object_by_id(
            model=QuizModel, object_id=quiz_id
        )

        question: QuizQnAModel
        is_last_question: bool

        question, is_last_question = check_and_fetch_latest_question_for_quiz(quiz_id=quiz_id)

        if not question:
            return {
                "error": "INVALID_QUIZ",
                "message": "Unable to fetch question, Please contact support",
                "data": {},
            }, 400

        try:
            question_qna: QNAModel = question.qna

            response: Dict[str, Any] = {
                "question": question_qna.question,
                "answer": question_qna.answer,
                "options": question.options,
                "difficulty": question.difficulty.value,
                "qna_id": question_qna.id,
                "is_last_question": f"{is_last_question}",
            }

            update_all_questions_for_quiz(quiz_id=quiz_id, except_qna_id=question.id)

            update_quiz_question(
                question_id=question.id,
                is_given_to_user=True,
                is_answered=question.is_answered,
                is_latest_question_given_to_user=True,
            )

            thread = threading.Thread(
                target=check_and_generate_more_questions,
                kwargs={"quiz_id": quiz_id, "last_difficulty": question.difficulty},
            )
            thread.start()

            create_activity_for_quiz(
                quiz_id=quiz_id,
                quiz_name=quiz_object.quiz_name,
                quiz_summary=quiz_object.quiz_summary,
                user_id=user_id,
            )

            return {
                "error": None,
                "message": "quiz question fetched successfully",
                "data": response,
            }, 200
        except Exception as e:
            return {
                "error": "INVALID_QUIZ",
                "message": f"Unable to fetch question, Please contact support, error: {e}",
                "data": {},
            }, 400


@quiz_api_ns.route("/answer")
class QuizAnswersRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("quizId", help="Quiz ID", required=True)
    parser.add_argument("qnaId", help="QNA ID", required=True)
    parser.add_argument("userAnswer", help="User's answer", required=True)
    parser.add_argument("timeTaken", help="Time taken in seconds", required=False, type=int)

    @quiz_api_ns.expect(parser)
    @authenticate_user
    def post(self):
        args: ParseResult = self.parser.parse_args()
        quiz_id: str = args.get("quizId")
        qna_id: str = args.get("qnaId")
        user_answer: str = args.get("userAnswer")
        time_taken: Optional[int] = args.get("timeTaken")
        user_id: str = request.user_id

        try:
            qna = ObjectRepository.get_object_by_id(model=QNAModel, object_id=qna_id)
            if not qna:
                return {
                    "error": "QNA not found",
                    "message": "Invalid QNA ID provided",
                    "data": None,
                }, 404

            quiz_qna: QuizQnAModel = ObjectRepository.get_object_by_id(
                model=QuizQnAModel, object_id=qna_id
            )
            if not quiz_qna:
                return {
                    "error": "QNA not found",
                    "message": "Invalid QNA ID provided",
                    "data": None,
                }, 404

            is_correct = user_answer.strip().lower() == qna.answer.strip().lower()

            existing_answer = query_manager.query_with_filter(
                model=QuizUserAnswersModel,
                filters=and_(
                    QuizUserAnswersModel.user_id == user_id,
                    QuizUserAnswersModel.quiz_id == quiz_id,
                    QuizUserAnswersModel.qna_id == qna_id,
                ),
            )

            if existing_answer:
                return {
                    "error": "Answer already exists",
                    "message": "User has already answered this question",
                    "data": None,
                }, 400

            quiz_answer = QuizUserAnswersModel(
                user_id=user_id,
                quiz_id=quiz_id,
                qna_id=qna_id,
                user_answer=user_answer,
                is_correct=is_correct,
                time_taken=time_taken,
            )

            answer = ObjectRepository.insert_single_object(quiz_answer)

            update_quiz_question(question_id=quiz_qna.id, is_given_to_user=True, is_answered=True)

            next_question, is_last_question = check_and_fetch_latest_question_for_quiz(
                quiz_id=quiz_id
            )

            logger.info(f"Next Question for quiz: {next_question}")
            quiz_object: QuizModel = ObjectRepository.get_object_by_id(
                model=QuizModel, object_id=quiz_id
            )
            if not next_question:
                create_activity_for_quiz(
                    quiz_id=quiz_id,
                    quiz_name=quiz_object.quiz_name,
                    quiz_summary=quiz_object.quiz_summary,
                    user_id=user_id,
                )

                quiz_object.has_completed = True
                ObjectRepository.update_single_object(quiz_object)

                return {
                    "error": None,
                    "message": "Quiz Ended successfully",
                    "data": None,
                }, 200

            update_all_questions_for_quiz(quiz_id=quiz_id, except_qna_id=next_question.id)

            thread = threading.Thread(
                target=check_and_generate_more_questions,
                kwargs={"quiz_id": quiz_id, "last_difficulty": next_question.difficulty},
            )
            thread.start()

            update_quiz_question(
                question_id=next_question.id,
                is_given_to_user=True,
                is_answered=next_question.is_answered,
                is_latest_question_given_to_user=True,
            )

            # Updating quiz summary
            updated_summary = update_quiz_summary(
                quiz_id=quiz_id, user_id=user_id, has_started=True
            )

            next_question_response = format_quiz_qna_for_response(question=next_question)
            next_question_response["is_last_question"] = is_last_question

            create_activity_for_quiz(
                quiz_id=quiz_id,
                quiz_name=quiz_object.quiz_name,
                quiz_summary=updated_summary,
                user_id=user_id,
            )
            return {
                "error": None,
                "message": "Answer submitted successfully",
                "data": {
                    "isCorrect": is_correct,
                    "correctAnswer": qna.answer,
                    "timeTaken": time_taken,
                    "next_question": next_question_response,
                },
            }, 201

        except Exception as e:
            return {
                "error": str(e),
                "message": "Failed to submit answer",
                "data": None,
            }, 500


@quiz_api_ns.route("/<string:quiz_id>")
class QuizRoute(Resource):
    @authenticate_user
    def get(self, quiz_id: str):
        user_id: str = request.user_id

        update_quiz_summary(quiz_id=quiz_id, user_id=user_id)

        return {
            "error": None,
            "message": "Quiz fetched successfully",
            "data": get_quiz_by_id(quiz_id=quiz_id),
        }, 201

from typing import Any, Dict, List, Optional
from flask import request
from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser
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
from app.utils.quiz_util import (
    fetch_next_question_in_quiz,
    format_quiz_qna_for_response,
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

    @quiz_api_ns.expect(parser)
    def get(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        quiz_type: str = args.get("quizType")
        # user_id: str = request.user_id
        user_id: str = "user_17ae337cff"

        if quiz_type not in ["new", "old"]:
            return {
                "error": None,
                "message": "Invalid Quiz Type",
                "data": [],
            }, 400

        if quiz_type == "new":
            filters = [
                QuizModel.user_id == user_id,
                QuizModel.has_started.is_(False),
            ]
            if file_id is not None:
                filters.append(QuizModel.file_id == file_id)
            quiz_list_for_user: List[QuizModel] = query_manager.query_with_filter(
                model=QuizModel,
                filters=and_(*tuple(filters)),
            )
        else:
            filters = [QuizModel.user_id == user_id, QuizModel.has_started.is_(True)]
            if file_id is not None:
                filters.append(QuizModel.file_id == file_id)
            quiz_list_for_user: List[QuizModel] = query_manager.query_with_filter(
                model=QuizModel,
                filters=and_(*tuple(filters)),
            )

        return {
            "error": None,
            "message": "Quiz generated successfully",
            "data": [quiz.to_dict() for quiz in quiz_list_for_user],
        }, 201


@quiz_api_ns.route("/question")
class QuizRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=True)
    parser.add_argument("quizId", help="QuizId", required=True)

    @quiz_api_ns.expect(parser)
    def get(self):
        args: ParseResult = self.parser.parse_args()
        file_id: str = args.get("fileId")
        quiz_id: str = args.get("quizId")
        user_id: str = request.user_id

        question: QuizQnAModel = fetch_next_question_in_quiz(quiz_id=quiz_id)

        question_qna: QNAModel = question.qna

        response: Dict[str, Any] = {
            "question": question_qna.question,
            "answer": question_qna.answer,
            "options": question.options,
            "difficulty": question.difficulty.value,
            "qna_id": question_qna.id,
        }

        update_quiz_question(
            question_id=question.id, is_given_to_user=True, is_answered=question.is_answered
        )

        return {
            "error": None,
            "message": "quiz question fetched successfully",
            "data": response,
        }, 200


@quiz_api_ns.route("/answer")
class QuizAnswersRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("quizId", help="Quiz ID", required=True)
    parser.add_argument("qnaId", help="QNA ID", required=True)
    parser.add_argument("userAnswer", help="User's answer", required=True)
    parser.add_argument("timeTaken", help="Time taken in seconds", required=False, type=int)

    @quiz_api_ns.expect(parser)
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

            next_question = fetch_next_question_in_quiz(quiz_id=quiz_id)
            update_quiz_question(
                question_id=next_question.id,
                is_given_to_user=True,
                is_answered=next_question.is_answered,
            )

            # Updating quiz summary
            update_quiz_summary(quiz_id=quiz_id, user_id=user_id, has_started=True)

            next_question_response = format_quiz_qna_for_response(question=next_question)

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

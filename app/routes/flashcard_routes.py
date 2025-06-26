from typing import Any, List, Optional
from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser
from sqlalchemy import and_

from app.database import query_manager
from app.database.models.flashcards import FlashCardModel
from app.database.models.qna import QNAModel, QuestionSource
from app.database.models.qna_actions import QNAActions
from app.utils.qna_util import insert_question_and_answer_in_db

flashcard_api_ns = Namespace("flashcard", description="APIs for flashcard")


@flashcard_api_ns.route("/")
class FlashcardRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=False)

    @flashcard_api_ns.expect(parser)
    def get(self):
        args: ParseResult = self.parser.parse_args()
        file_id: Optional[str] = args.get("fileId", None)
        user_id: str = "user_17ae337cff"
        flashcards_for_user = query_manager.query_with_filter(
            model=FlashCardModel, filters=(FlashCardModel.user_id == user_id)
        )

        response: List[str, Any] = []

        for flashcard in flashcards_for_user:
            qna_for_flashcards: List[QNAModel] = query_manager.query_with_filter(
                model=QNAModel,
                filters=and_(
                    QNAModel.source == QuestionSource.FLASHCARDS, QNAModel.source_id == flashcard.id
                ),
            )

            for qna in qna_for_flashcards:
                qna_action: List[QNAActions] = query_manager.query_with_filter(
                    model=QNAActions, filters=(QNAActions.qna_id == qna.id)
                )

                response.append(
                    {
                        "question": qna.question,
                        "answer": qna.answer,
                        "fileId": flashcard.file_id,
                        "qnaId": qna.id,
                        "created_at": qna.created_at.isoformat(),
                        "status": qna_action[0].qna_flashcard_action.value
                        if len(qna_action) > 0
                        else None,
                    }
                )
        return {
            "error": None,
            "message": "flashcards fetched successfully",
            "data": response,
        }, 201

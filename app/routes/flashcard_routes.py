from typing import Any, List, Optional
from flask import request
from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from app.database import query_manager
from app.database.models.flashcards import FlashCardModel
from app.database.models.qna import QNAModel
from app.database.models.qna_actions import QNAActions
from app.database.models.flashcard_qna import FlashCardQnAModel

flashcard_api_ns = Namespace("flashcard", description="APIs for flashcard")


@flashcard_api_ns.route("/")
class FlashcardRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("fileId", help="FileId", required=False)

    @flashcard_api_ns.expect(parser)
    def get(self):
        args: ParseResult = self.parser.parse_args()
        file_id: Optional[str] = args.get("fileId")
        try:
            user_id: str = request.user_id
        except Exception:
            user_id = "user_17ae337cff"

        flashcard_filters = [FlashCardModel.user_id == user_id]
        if file_id:
            flashcard_filters.append(FlashCardModel.file_id == file_id)

        flashcards_for_user: List[FlashCardModel] = query_manager.query_with_filter(
            model=FlashCardModel, filters=and_(*flashcard_filters)
        )

        response: List[dict] = []

        for flashcard in flashcards_for_user:
            flashcard_qnas: List[FlashCardQnAModel] = query_manager.query_with_filter(
                model=FlashCardQnAModel,
                filters=(FlashCardQnAModel.flashcard_id == flashcard.id),
                options=[joinedload(FlashCardQnAModel.qna)],
            )

            for fqna in flashcard_qnas:
                qna: QNAModel = fqna.qna

                qna_actions: List[QNAActions] = query_manager.query_with_filter(
                    model=QNAActions, filters=(QNAActions.qna_id == qna.id)
                )

                status = qna_actions[0].qna_flashcard_action.value if qna_actions else None

                response.append(
                    {
                        "question": qna.question,
                        "answer": qna.answer,
                        "fileId": flashcard.file_id,
                        "qnaId": qna.id,
                        "created_at": qna.created_at.isoformat(),
                        "status": status,
                    }
                )

        return {
            "error": None,
            "message": "flashcards fetched successfully",
            "data": response,
        }, 200

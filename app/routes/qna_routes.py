from typing import Any, List, Optional
from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser
from sqlalchemy import and_

from app.database import query_manager
from app.database.models.qna_actions import QNAActions, QnaFlashCardAction
from app.database.models.qna import QNAModel
from app.database.object_repository import ObjectRepository

qna_action_api_ns = Namespace("qna_action", description="APIs for QNA actions")


@qna_action_api_ns.route("/")
class QnaActionRoutes(Resource):
    parser: RequestParser = RequestParser()
    parser.add_argument("qnaId", help="QNA ID", required=True)
    parser.add_argument(
        "action", help="Flashcard Action", required=True, choices=["KNOWN", "REVIEW_LATER"]
    )

    @qna_action_api_ns.expect(parser)
    def post(self):
        args: ParseResult = self.parser.parse_args()
        qna_id: str = args.get("qnaId")
        action: str = args.get("action")

        qna_exists = query_manager.query_with_filter(
            model=QNAModel, filters=(QNAModel.id == qna_id)
        )

        if not qna_exists:
            return {
                "error": "QNA_NOT_FOUND",
                "message": "QNA with provided ID does not exist",
                "data": None,
            }, 404

        flashcard_action = QnaFlashCardAction(action)

        existing_action = query_manager.query_with_filter(
            model=QNAActions, filters=(QNAActions.qna_id == qna_id)
        )

        if existing_action:
            # Update existing action
            existing_action[0].qna_flashcard_action = flashcard_action
            query_manager.update_single_object(existing_action[0])

            return {
                "error": None,
                "message": "QNA action updated successfully",
                "data": {
                    "id": existing_action[0].id,
                    "qnaId": existing_action[0].qna_id,
                    "action": existing_action[0].qna_flashcard_action.value,
                    "updatedAt": existing_action[0].updated_at.isoformat(),
                },
            }, 200
        else:
            qna_action = QNAActions(qna_id=qna_id, qna_flashcard_action=flashcard_action)

            ObjectRepository.insert_single_object(qna_action)

            return {
                "error": None,
                "message": "QNA action created successfully",
                "data": {
                    "id": qna_action.id,
                    "qnaId": qna_action.qna_id,
                    "action": qna_action.qna_flashcard_action.value,
                    "createdAt": qna_action.created_at.isoformat(),
                },
            }, 201

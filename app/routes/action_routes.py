from flask_restx import Namespace, Resource
from flask_restx.reqparse import ParseResult, RequestParser

from app.constants import ChatGptPrompts, ChatGptMessagePayload
from app.database.models.file import FileModel
from app.database.object_repository import ObjectRepository
from app.utils.c_gpt import featch_and_stream_response_from_model
from typing import List, Dict, Any

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

        featch_and_stream_response_from_model(message_for_model=message_for_model, user_id='user_17ae337cff')

        return {}



from typing import Any, Dict

from app.utils.file_util import process_and_create_action_items_for_file


TASK_HANDLERS: Dict[str, Any] = {
    "process_file": process_and_create_action_items_for_file,
}

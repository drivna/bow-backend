from loguru import logger
from app.constants import ChatGptPrompts
from app.database.models.file_topics import FileTopicModel
from app.database.object_repository import ObjectRepository
from app.utils.c_gpt import fetch_response_from_model
from app.utils.knwoledge_map_util import update_full_knowledge_map_for_file


def generate_topics_for_file_and_update_knowledge_map(file_content, file_id, user_id):
    logger.info('Generating topics for file')
    def build_messages(system_prompt, pages):
        messages = [{"role": "system", "content": system_prompt}]
        for page_index in range(len(pages)):
            messages.append({"role": "user", "content": f"{page_index}:\n{pages[page_index]}"})
        return messages

    system_prompt = ChatGptPrompts.get_topic_generation_prompt()
    messages = build_messages(system_prompt, file_content)
    response = fetch_response_from_model(message_for_model=messages)

    logger.info(f"Response from model for topic generation: {response}")

    if not response:
        return None

    for res in response:
        key_list = res.split("_")
        page_number = key_list[-1]
        all_topics_for_page = []
        for topics_data in response[res]:
            topic_name = topics_data.get("topic", "")
            topics_description = topics_data.get("description", "")

            topic: FileTopicModel = FileTopicModel(
                file_id=file_id,
                page_number=page_number,
                topic_name=topic_name,
                topic_description=topics_description,
            )
            created_topic = ObjectRepository.insert_single_object(topic)
            logger.info(f"Created topic: {created_topic.id} for file, topic_name: {topic_name}")

            if topic_name.strip():
                all_topics_for_page.append(topic_name.strip())

            if all_topics_for_page:
                km_result = update_full_knowledge_map_for_file(
                    user_id=user_id,
                    file_id=file_id,
                    topics_list=all_topics_for_page,
                    page_number=page_number,
                )
                logger.info(f"Knowledge map updated for file={file_id}, result={km_result}")

    return response

from loguru import logger
from app.constants import ChatGptPrompts
from app.database.models.file_topics import FileTopicModel
from app.database.object_repository import ObjectRepository
from app.utils.c_gpt import fetch_response_from_model


def generate_topics_for_file(file_content, file_id):
    def build_messages(system_prompt, pages):
        messages = [{"role": "system", "content": system_prompt}]
        for page_index in range(len(pages)):
            messages.append({"role": "user", "content": f"{page_index}:\n{pages[page_index]}"})
        return messages

    system_prompt = ChatGptPrompts.get_topic_generation_prompt()
    messages = build_messages(system_prompt, file_content)
    response = fetch_response_from_model(message_for_model=messages)
    print(response)

    for res in response:
        key_list = res.split("_")
        page_number = key_list[-1]
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

    return response

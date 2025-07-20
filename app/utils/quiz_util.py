import json
from typing import Any, Dict, List, Optional, Tuple
import random
from sqlalchemy.orm import Session

from loguru import logger
from sqlalchemy import and_
from app.constants import LOW_POOL_THRESHOLD, ChatGptMessagePayload, ChatGptPrompts
from app.database.models.file import FileModel
from app.database.models.file_topics import FileTopicModel
from app.database.query_manager import database_engine
from app.database import query_manager
from app.database.models.qna import QNAModel
from app.database.models.quiz import QuizModel
from app.database.models.quiz_qna import DifficultyLevel, QuizQnAModel
from app.database.object_repository import ObjectRepository
from app.database.models.quiz_answers import QuizUserAnswersModel
from sqlalchemy.orm import joinedload

from app.utils.c_gpt import fetch_response_from_model


def generate_quiz_for_file(file_id: str, user_id: str):
    logger.info(f"Generating quiz for file_id:{file_id}")
    file_object: FileModel = ObjectRepository.get_object_by_id(model=FileModel, object_id=file_id)
    (
        existing_questions_of_quiz_for_file,
        existing_quiz_names,
    ) = get_all_questions_generated_for_file(file_id=file_id)

    def fetch_and_insert_quiz_in_db(topics: List[str]):
        response = generate_quiz_for_difficulty(
            file_content=file_object.file_content,
            prev_quiz_names=existing_quiz_names,
            prev_questions=existing_questions_of_quiz_for_file,
            topics=topics,
        )
        quiz_name: Optional[str] = response.get("quiz_name", None)
        if quiz_name is not None:
            quiz: QuizModel = QuizModel(user_id=user_id, file_id=file_id, quiz_name=quiz_name)
            created_quiz: QuizModel = ObjectRepository.insert_single_object(
                object_to_be_inserted=quiz, without_upsert_call=True
            )

            create_new_quiz_in_db(
                user_id=user_id, quiz_data=response, file_id=file_id, quiz_id=created_quiz.id
            )

            update_quiz_summary(quiz_id=quiz.id, user_id=user_id)

            logger.info(f"Generated quiz: {quiz.id} for file: {file_id}")

    logger.info(f"Generating quiz for entire file: {file_id}")

    fetch_and_insert_quiz_in_db(topics=[])

    topics_for_file: List[FileTopicModel] = query_manager.query_with_filter(
        model=FileTopicModel,
        filters=(FileTopicModel.file_id == file_id),
        order_by=(FileTopicModel.page_number.desc()),
    )
    topics: List[str] = []
    for topic in topics_for_file:
        topics.append(topic.topic_description)

    mid = len(topics) // 2
    logger.info(f"Generating quiz for entire file: {file_id} for topics: {topics[:mid]}")

    fetch_and_insert_quiz_in_db(topics=topics[:mid])

    logger.info(f"Generating quiz for entire file: {file_id} for topics: {topics[mid:]}")

    fetch_and_insert_quiz_in_db(topics=topics[mid:])

    return


def create_new_quiz_in_db(quiz_data: Dict[str, Any], user_id: str, file_id: str, quiz_id: str):
    logger.info(f"Creating quiz in db for user_id:{user_id}, file_id:{file_id}, quiz_id: {quiz_id}")

    for question_answer in quiz_data.get("questions", []):
        question: str = question_answer.get("question")
        answer: str = question_answer.get("correct_answer")
        options: str = question_answer.get("options")
        difficulty: str = question_answer.get("difficulty")

        qna: QNAModel = QNAModel(question=question, answer=answer)
        ObjectRepository.insert_single_object(qna)

        quiz_qna: QuizQnAModel = QuizQnAModel(
            quiz_id=quiz_id,
            difficulty=DifficultyLevel[difficulty.upper()],
            options=json.dumps(options),
            id=qna.id,
        )
        ObjectRepository.insert_single_object(quiz_qna, without_upsert_call=True)

    return


def get_next_question(
    correct_streak, last_difficulty, easy_questions, medium_questions, hard_questions
):
    def pick_random(question_pool):
        return random.choice(question_pool) if question_pool else None

    if correct_streak <= 1:
        # Stick to easy if user is new or making mistakes
        return pick_random(easy_questions)

    if correct_streak == 2:
        # Progress to medium if they’re doing well from easy
        if last_difficulty == "easy":
            return pick_random(medium_questions) or pick_random(easy_questions)
        return pick_random(easy_questions)

    if correct_streak >= 3:
        # Push difficulty if streak is good
        if last_difficulty == "medium":
            return pick_random(hard_questions) or pick_random(medium_questions)
        elif last_difficulty == "easy":
            return pick_random(medium_questions) or pick_random(easy_questions)
        elif last_difficulty == "hard":
            return pick_random(hard_questions) or pick_random(medium_questions)

    return pick_random(easy_questions + medium_questions + hard_questions)


def get_quiz_summary(quiz_id: str, user_id: str) -> Dict[str, Any]:
    quiz = ObjectRepository.get_object_by_id(model=QuizModel, object_id=quiz_id)
    if not quiz or quiz.user_id != user_id:
        raise ValueError("Quiz not found or access denied")

    quiz_qnas: List[QuizQnAModel] = query_manager.query_with_filter(
        model=QuizQnAModel,
        filters=and_(QuizQnAModel.quiz_id == quiz_id, QuizQnAModel.is_given_to_user == True),
        options=[joinedload(QuizQnAModel.qna)],
    )

    total_questions = len(quiz_qnas)

    # Handle empty quiz case
    if total_questions == 0:
        return {
            "quizId": quiz_id,
            "quizName": quiz.quiz_name,
            "totalQuestions": 0,
            "answeredQuestions": 0,
            "correctAnswers": 0,
            "incorrectAnswers": 0,
            "percentage": 0.0,
            "averageTimeTaken": 0.0,
            "isCompleted": False,
            "summary": {
                "easy": {"total": 0, "correct": 0, "percentage": 0.0},
                "medium": {"total": 0, "correct": 0, "percentage": 0.0},
                "hard": {"total": 0, "correct": 0, "percentage": 0.0},
            },
        }

    user_answers: List[QuizUserAnswersModel] = query_manager.query_with_filter(
        model=QuizUserAnswersModel,
        filters=and_(
            QuizUserAnswersModel.user_id == user_id,
            QuizUserAnswersModel.quiz_id == quiz_id,
        ),
    )

    # Calculate basic statistics
    answered_questions = len(user_answers)
    correct_answers = sum(1 for answer in user_answers if answer.is_correct)
    incorrect_answers = answered_questions - correct_answers
    percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0.0
    is_completed = answered_questions == total_questions
    current_streak: int = 0

    sorted_answers = sorted(user_answers, key=lambda x: x.created_at)

    for answer in reversed(sorted_answers):
        if answer.is_correct:
            current_streak += 1
        else:
            break

    # Calculate average time taken
    valid_times = [answer.time_taken for answer in user_answers if answer.time_taken is not None]
    average_time_taken = sum(valid_times) / len(valid_times) if valid_times else 0.0

    # Initialize difficulty statistics
    difficulty_stats = {
        "easy": {"total": 0, "correct": 0},
        "medium": {"total": 0, "correct": 0},
        "hard": {"total": 0, "correct": 0},
    }

    for qqna in quiz_qnas:
        diff_key = qqna.difficulty.value.lower()

        if diff_key in difficulty_stats:
            difficulty_stats[diff_key]["total"] += 1

    answer_dict = {answer.qna_id: answer for answer in user_answers}
    for qqna in quiz_qnas:
        diff_key = qqna.difficulty.value.lower()

        if diff_key in difficulty_stats and qqna.id in answer_dict:
            if answer_dict[qqna.id].is_correct:
                difficulty_stats[diff_key]["correct"] += 1

    # Calculate percentages for each difficulty
    summary = {}
    for diff, stats in difficulty_stats.items():
        percentage_diff = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        summary[diff] = {
            "total": stats["total"],
            "correct": stats["correct"],
            "percentage": round(percentage_diff, 2),
        }

    return {
        "quizId": quiz_id,
        "quizName": quiz.quiz_name,
        "totalQuestions": total_questions,
        "answeredQuestions": answered_questions,
        "correctAnswers": correct_answers,
        "incorrectAnswers": incorrect_answers,
        "percentage": round(percentage, 2),
        "averageTimeTaken": round(average_time_taken, 2),
        "isCompleted": is_completed,
        "summary": summary,
        "current_streak": current_streak,
    }


def update_quiz_summary(quiz_id: str, user_id: str, has_started: bool = False) -> None:
    with Session(database_engine) as session:
        quiz: QuizModel = (
            session.query(QuizModel)
            .options(joinedload(QuizModel.quiz_qna_items))
            .filter(QuizModel.id == quiz_id)
            .one_or_none()
        )
        if quiz is None:
            logger.warning(f"No quiz found with id={quiz_id}")
            return

        summary = get_quiz_summary(quiz_id=quiz_id, user_id=user_id)
        quiz.quiz_summary = summary

        if has_started == True:
            quiz.has_started = True

        session.commit()  # commits the changes
        logger.info(f"Updated quiz: {quiz_id} with summary: {summary}")


def update_quiz_question(
    question_id: str, is_given_to_user: bool = False, is_answered: bool = False
):
    with Session(database_engine) as session:
        quiz_qna: QuizQnAModel = (
            session.query(QuizQnAModel)
            .options(joinedload(QuizQnAModel.qna))
            .filter(QuizQnAModel.id == question_id)
            .one_or_none()
        )
        if quiz_qna is None:
            logger.warning(f"No quiz question found with id={quiz_qna}")
            return

        quiz_qna.is_given_to_user = is_given_to_user
        quiz_qna.is_answered = is_answered

        session.commit()  # commits the changes
        logger.info(
            f"Updated quiz_qna: {question_id} with is_answered: {is_answered}, is_given_to_user: {is_given_to_user}"
        )


def fetch_next_question_in_quiz(quiz_id: str):
    quiz: QuizModel = ObjectRepository.get_object_by_id(model=QuizModel, object_id=quiz_id)
    e_quiz_qna_list: List[QuizQnAModel] = query_manager.query_with_filter(
        model=QuizQnAModel,
        filters=and_(
            QuizQnAModel.quiz_id == quiz.id,
            QuizQnAModel.difficulty == DifficultyLevel.EASY,
            QuizQnAModel.is_given_to_user == False,
            # is_answered=False,
        ),
        options=[joinedload(QuizQnAModel.qna)],
    )
    m_quiz_qna_list: List[QuizQnAModel] = query_manager.query_with_filter(
        model=QuizQnAModel,
        filters=and_(
            QuizQnAModel.quiz_id == quiz.id,
            QuizQnAModel.difficulty == DifficultyLevel.MEDIUM,
            QuizQnAModel.is_given_to_user == False,
            # is_answered=False,
        ),
        options=[joinedload(QuizQnAModel.qna)],
    )
    h_quiz_qna_list: List[QuizQnAModel] = query_manager.query_with_filter(
        model=QuizQnAModel,
        filters=and_(
            QuizQnAModel.quiz_id == quiz.id,
            QuizQnAModel.difficulty == DifficultyLevel.HARD,
            QuizQnAModel.is_given_to_user == False,
            # QuizQnAModel,is_answered=False,
        ),
        options=[joinedload(QuizQnAModel.qna)],
    )

    question: QuizQnAModel = get_next_question(
        correct_streak=0,
        last_difficulty=DifficultyLevel.EASY.value.lower(),
        easy_questions=e_quiz_qna_list,
        medium_questions=m_quiz_qna_list,
        hard_questions=h_quiz_qna_list,
    )

    return question


def check_and_generate_more_questions(
    file_content: str,
    total_questions_served,
    easy_questions,
    medium_questions,
    hard_questions,
    correct_streak,
    last_difficulty,
    topics,
):
    difficulty_bucket_to_generate: Optional[str] = should_generate_more_questions(
        total_questions_served=total_questions_served,
        easy_questions=easy_questions,
        medium_questions=medium_questions,
        hard_questions=hard_questions,
        correct_streak=correct_streak,
        last_difficulty=last_difficulty,
    )

    if not difficulty_bucket_to_generate:
        return

    generate_quiz_for_difficulty(
        file_content=file_content, difficulty=difficulty_bucket_to_generate, topics=topics
    )

    return


def should_generate_more_questions(
    total_questions_served,
    easy_questions,
    medium_questions,
    hard_questions,
    correct_streak,
    last_difficulty,
):
    # Serve up to 10 questions based on user's performance (correct streak & last difficulty).
    # Preemptively generate more questions when a difficulty pool is low to ensure smooth progression.

    if total_questions_served >= 10:
        return None

    likely_needed = []

    if correct_streak <= 1:
        likely_needed.append("easy")

    elif correct_streak == 2:
        likely_needed.append("medium" if last_difficulty == "easy" else "easy")

    elif correct_streak >= 3:
        if last_difficulty == "easy":
            likely_needed.append("medium")
        elif last_difficulty == "medium":
            likely_needed.append("hard")
        elif last_difficulty == "hard":
            likely_needed.append("hard")

    # Add fallback options too
    likely_needed.append("easy")
    likely_needed.append("medium")
    likely_needed.append("hard")

    # Check if any needed pool is low
    for diff in likely_needed:
        pool = {"easy": easy_questions, "medium": medium_questions, "hard": hard_questions}[diff]

        if len(pool) <= LOW_POOL_THRESHOLD:
            return diff

    return None


def generate_quiz_for_difficulty(
    file_content: str, prev_questions: List[str], prev_quiz_names: List[str], topics: List[str]
):
    system_prompt_for_quiz_agent = ChatGptPrompts.get_quiz_generation_prompt_with_model_name(
        pdf_text=file_content,
        previous_questions=prev_questions,
        previous_quiz_names=prev_quiz_names,
        topics=topics,
    )
    message_for_model = ChatGptMessagePayload.get_message_payload_for_quiz(
        prompt=system_prompt_for_quiz_agent,
    )
    response = fetch_response_from_model(message_for_model=message_for_model)

    return response


def get_all_questions_generated_for_file(file_id: str) -> Tuple[List[str], List[str]]:
    quiz_list: List[QuizModel] = query_manager.query_with_filter(
        model=QuizModel, filters=(QuizModel.file_id == file_id)
    )
    questions: List[str] = []
    quiz_names: List[str] = []
    for quiz in quiz_list:
        quiz_names.append(quiz.quiz_name)
        e_quiz_qna_list: List[QuizQnAModel] = query_manager.query_with_filter(
            model=QuizQnAModel,
            filters=and_(
                QuizQnAModel.quiz_id == quiz.id,
                QuizQnAModel.difficulty == DifficultyLevel.EASY,
                QuizQnAModel.is_given_to_user == False,
                QuizQnAModel.is_answered == False,
            ),
            options=[joinedload(QuizQnAModel.qna)],
        )
        m_quiz_qna_list: List[QuizQnAModel] = query_manager.query_with_filter(
            model=QuizQnAModel,
            filters=and_(
                QuizQnAModel.quiz_id == quiz.id,
                QuizQnAModel.difficulty == DifficultyLevel.MEDIUM,
                QuizQnAModel.is_given_to_user == False,
                QuizQnAModel.is_answered == False,
            ),
            options=[joinedload(QuizQnAModel.qna)],
        )
        h_quiz_qna_list: List[QuizQnAModel] = query_manager.query_with_filter(
            model=QuizQnAModel,
            filters=and_(
                QuizQnAModel.quiz_id == quiz.id,
                QuizQnAModel.difficulty == DifficultyLevel.HARD,
                QuizQnAModel.is_given_to_user == False,
                QuizQnAModel.is_answered == False,
            ),
            options=[joinedload(QuizQnAModel.qna)],
        )

        for q in e_quiz_qna_list:
            qna: QNAModel = q.qna
            questions.append(qna.question)

        for q in m_quiz_qna_list:
            qna: QNAModel = q.qna
            questions.append(qna.question)

        for q in h_quiz_qna_list:
            qna: QNAModel = q.qna
            questions.append(qna.question)

    return questions, quiz_names


def format_quiz_qna_for_response(question: QuizQnAModel):
    question_qna: QNAModel = question.qna

    response: Dict[str, Any] = {
        "question": question_qna.question,
        "answer": question_qna.answer,
        "options": question.options,
        "difficulty": question.difficulty.value,
        "qna_id": question_qna.id,
    }
    return response

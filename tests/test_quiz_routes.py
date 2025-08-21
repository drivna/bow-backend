# from datetime import datetime
# import random
# import string
# from app.database.models.file import FileModel
# from app.database.models.qna import QNAModel
# from app.database.models.quiz_qna import QuizQnAModel
# from app.database.models.user import UserModel
# from app.database.object_repository import ObjectRepository
# from app.utils.pdf_util import get_file_hash, read_pdf_text
# from app.utils.quiz_util import check_and_fetch_latest_question_for_quiz, generate_quiz_for_file, get_list_of_quiz, handle_answer_and_generate_new_question_for_quiz
# from app.utils.topic_utils import generate_topics_for_file_and_update_knowledge_map

# def generate_random_string(length: int) -> str:
#     characters = string.digits
#     random_string = "".join(random.choice(characters) for _ in range(length))
#     return random_string


# def test_file_is_created():
#     file_bytes = None
#     suffix: str = generate_random_string(length=6)

#     user: UserModel = UserModel(
#         user_name = f'user_{suffix}',
#         email = f'user_{suffix}@gmail.com',
#         password = 'password'
#     )
#     ObjectRepository.insert_single_object(user)

#     with open('tests/leph105.pdf', 'rb') as file:
#         file_bytes = file.read()
    
#     filename = f"filename_{datetime.now().timestamp()}"  #

#     file_content = read_pdf_text(file_bytes)
#     file_content = [text.replace("\x00", "") for text in file_content]
#     file_content = "\n".join(file_content) 
#     file_hash = get_file_hash(file_content=file_content)


#     file_object = FileModel(
#         uploaded_by=user.id,
#         file_name=filename,
#         file_hash=file_hash,
#         file_content=file_content,
#         file_type="pdf",
#     )

#     saved_file: FileModel = ObjectRepository.insert_single_object(
#         object_to_be_inserted=file_object
#     )

#     assert saved_file

#     generate_quiz_for_file(file_id= saved_file.id, user_id= user.id)

#     new_quiz_for_user = get_list_of_quiz(user_id=user.id,file_id=saved_file.id, quiz_type='new')
#     assert len(new_quiz_for_user)==1

#     question: QuizQnAModel
#     is_last_question: bool

#     question, is_last_question = check_and_fetch_latest_question_for_quiz(quiz_id=new_quiz_for_user[0].id)

#     assert is_last_question == False

#     assert question 

#     i=1
#     question_qna: QNAModel = question.qna
#     answer = ''
#     question = handle_answer_and_generate_new_question_for_quiz(qna_id=question_qna.id, quiz_id=question.quiz_id, user_answer=answer,user_id=user.id)
#     assert question

#     while i<10:
#         if i%2==0:
#             user_answer = answer
#         else:
#             user_answer = ''
        
#         qna_id = question.get('qna_id')
#         answer = question.get('answer')
#         question = handle_answer_and_generate_new_question_for_quiz(qna_id=qna_id, quiz_id=new_quiz_for_user[0].id, user_answer=user_answer,user_id=user.id)

#         i += 1
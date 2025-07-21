from typing import Any, List


class ChatGptPrompts:
    @classmethod
    def get_pdf_summary_prompt(cls):
        """
        Returns a system prompt for AI to create comprehensive PDF content summaries.

        Returns:
            str: Complete system prompt for detailed PDF summarization
        """
        prompt = """You are a thorough assistant that creates comprehensive, detailed summaries of PDF content. Your task is to read through the entire PDF and extract ALL important information, covering every topic, section, and concept mentioned in the document.

        ## Comprehensive Summary Structure

        **Document Overview:**
        - Complete description of the document type and purpose
        - Full scope of topics covered
        - Target audience and context

        **Complete Topic Coverage:**
        Go through the document systematically and cover:
        - Every major section and subsection
        - All concepts, theories, and ideas presented
        - Every important detail, fact, and piece of information
        - All examples, case studies, and illustrations
        - Any data, statistics, research findings, or evidence
        - All processes, methodologies, and procedures described
        - Every definition, term, and explanation provided

        **Detailed Breakdown by Section:**
        For each major section of the document:
        - **Section Title/Topic**
        - Complete summary of all content in that section
        - All key points and supporting details
        - Any sub-topics or related concepts
        - Specific examples or applications mentioned
        - Important data or findings from that section

        **Technical Details and Specifications:**
        - All technical information, specifications, or requirements
        - Complete process descriptions and workflows
        - Any formulas, calculations, or technical procedures
        - System details, implementations, or configurations
        - Code snippets, algorithms, or technical examples

        **Complete Information Extraction:**
        - All names, dates, places, and references mentioned
        - Every conclusion, recommendation, or suggestion
        - Any limitations, challenges, or considerations discussed
        - All future work, next steps, or implications mentioned
        - Every citation, source, or reference provided

        ## Guidelines for Thoroughness

        **Leave Nothing Out:**
        - Read every section, paragraph, and important sentence
        - Cover all topics regardless of how minor they seem
        - Include both main ideas and supporting details
        - Capture nuances and subtle points made in the text

        **Organize Comprehensively:**
        - Follow the document's structure while ensuring nothing is missed
        - Group related information together logically
        - Use clear headings to organize different topics and sections
        - Maintain the flow and connections between ideas

        **Be Detailed and Specific:**
        - Provide specific details rather than general statements
        - Include exact numbers, dates, percentages, and measurements
        - Mention specific names, places, and references
        - Describe processes and procedures step-by-step

        **Format for Complete Coverage:**
        - Use detailed markdown formatting with multiple header levels
        - Create comprehensive bullet points that capture full information
        - Bold all important terms, names, and key concepts
        - Use numbered lists for sequences, steps, or ranked items
        - Write in clean format (avoid \\, \\\\, \\n symbols)

        Your goal is to create a summary so comprehensive that someone could understand the entire document content without reading the original. Cover everything - no topic should be left out, no important detail should be missed."""

        return prompt

    @classmethod
    def get_pdf_selected_content_summary_prompt(cls):
        """
        Returns a system prompt for AI to create detailed summaries of selected content from a PDF
        while maintaining awareness of the entire document context.

        Returns:
            str: Complete system prompt for contextual selected content summarization
        """
        prompt = """You are an intelligent assistant that creates detailed summaries of selected content from PDF documents. You have access to the ENTIRE PDF document content and must use this full context to provide the most accurate and comprehensive summary of the user's selected portion.

        ## Your Task

        **Context Awareness:**
        - You have access to the complete PDF document content
        - Use the full document context to understand the selected content better
        - Reference related information from other parts of the document when relevant
        - Understand how the selected content fits into the overall document structure

        **Selected Content Focus:**
        - Provide a detailed summary ONLY of the content the user has specifically selected
        - Do not summarize the entire document - focus solely on the selected portion
        - However, use your knowledge of the full document to provide better context and understanding

        ## Summary Structure for Selected Content

        **Selected Content Overview:**
        - Brief description of what the selected content covers
        - Its position/role within the overall document structure
        - How it relates to the main themes of the full document

        **Detailed Summary of Selected Content:**
        - Complete coverage of all information in the selected portion
        - Every key point, concept, and detail mentioned in the selection
        - All examples, data, statistics, or evidence within the selected text
        - Any processes, methodologies, or procedures described in the selection
        - All definitions, terms, and explanations provided in the selected content

        **Contextual Connections:**
        - How the selected content relates to other parts of the document
        - References to related concepts mentioned elsewhere in the full PDF
        - How this selection supports or connects to the document's main arguments
        - Any prerequisite knowledge from earlier sections that helps understand the selection

        **Technical Details (if applicable):**
        - All technical information, specifications, or requirements in the selection
        - Complete process descriptions and workflows from the selected content
        - Any formulas, calculations, or procedures mentioned in the selection
        - Code snippets, algorithms, or technical examples within the selected portion

        **Key Information Extraction:**
        - All names, dates, places, and references in the selected content
        - Every conclusion, recommendation, or suggestion within the selection
        - Any limitations, challenges, or considerations discussed in the selected portion
        - Citations, sources, or references mentioned in the selected text

        ## Guidelines for Contextual Selected Content Summarization

        **Use Full Document Context:**
        - Draw upon your knowledge of the entire document to better explain the selected content
        - Reference related sections when they help clarify the selected content
        - Explain technical terms or concepts using definitions from elsewhere in the document
        - Show how the selected content builds upon or leads to other parts of the document

        **Focus on Selection Only:**
        - Summarize ONLY what appears in the user's selected content
        - Do not include information from outside the selection unless it directly helps explain the selected content
        - Clearly distinguish between what's in the selection vs. contextual information from elsewhere

        **Be Comprehensive but Targeted:**
        - Cover every detail within the selected content thoroughly
        - Use specific details, numbers, dates, and exact information from the selection
        - Organize the summary logically, following the structure of the selected content
        - Include both main ideas and supporting details from the selection

        **Clear Formatting:**
        - Use detailed markdown formatting with appropriate header levels
        - Create comprehensive bullet points for complex information
        - Bold important terms, names, and key concepts
        - Use numbered lists for sequences or steps within the selected content
        - Write in clean format (avoid \\, \\\\, \\n symbols)

        **Contextual Enhancement:**
        - When a concept in the selection references something from elsewhere in the document, briefly explain it
        - If the selection mentions "as discussed earlier" or "as we'll see later," provide that context
        - Help the user understand the selected content even if they haven't read the entire document

        Your goal is to provide a comprehensive summary of the selected content that is enriched by your understanding of the entire document, making the selected portion fully understandable and placing it in proper context within the larger work."""

        return prompt

    @classmethod
    def get_flashcard_generation_prompt(cls, previous_questions: List[str] = []):
        base_prompt = """You are a personal tutor helping a student revise and understand a PDF they are reading.

        Your task is to carefully review the content of the PDF and generate a callout with open-ended, reflective questions that help the student think deeply about the material and reinforce their learning.

        Each question should:
        - Be directly based on the content of the PDF
        - Encourage reflection, personal opinions, interpretations, or real-world application
        - Be between 10 to 15 words in length
        - Be empathetic and conversational, as if a tutor is personally guiding the student"""

        # Handle exclusion instruction based on previous questions
        exclusion_instruction = ""
        if previous_questions:
            questions_text = "\n".join(previous_questions)
        else:
            questions_text = ""

        exclusion_instruction = f"""
        - Be completely different from any previously generated questions listed below

        AVOID generating questions similar to these previously asked ones:
        {questions_text}

        Focus on exploring different aspects, themes, or sections of the PDF that haven't been covered yet."""

        # Complete prompt
        output_format = """

        Return a JSON object with:
        - A short, descriptive "heading" (max 4 characters) summarizing the topic or goal of the callout
        - An array of exactly 5 open-ended questions
        - Each question must include a corresponding answer based on the PDF content

        Output format (do NOT include triple quotes or code fences):

        {
        "heading": "Callout title goes here",
        "questions": [
            {
            "type": "open_ended",
            "value": "What do you think the author meant by this section's central message?",
            "answer": "The author emphasized that resilience is developed through sustained challenges and reflection."
            },
            ...
        ]
        }

        Only return valid JSON. All text must be in English."""

        return base_prompt + exclusion_instruction + output_format

    @classmethod
    def get_quiz_generation_prompt_with_model_name(
        cls,
        pdf_text: str,
        topics: List[str] = None,
        previous_questions: List[str] = None,
        previous_quiz_names: List[str] = None,
    ) -> str:
        """
        Constructs a prompt to generate a quiz with 15 questions (5 each of easy, medium, and hard),
        and a unique quiz name suggested by the model.

        Args:
            pdf_text (str): Full extracted PDF content.
            topics (list, optional): Topics to restrict question generation to.
            previous_questions (list, optional): Previously asked questions to avoid.
            previous_quiz_names (list, optional): List of past quiz names to avoid repetition.

        Returns:
            str: Prompt string to be passed to the model.
        """

        topics_text = ", ".join(topics) if topics else ""
        topics_instruction = (
            f"strictly based on these topics only: {topics_text}"
            if topics
            else "based on the entire study material"
        )

        prev_qs_text = "\n".join(previous_questions) if previous_questions else ""
        prev_qs_instruction = (
            f'Do NOT repeat or paraphrase any of these previously asked questions:\n"""\n{prev_qs_text}\n"""'
            if previous_questions
            else ""
        )

        prev_quiz_names_text = "\n".join(previous_quiz_names) if previous_quiz_names else ""
        prev_name_instruction = (
            f'The quiz must have a **unique and meaningful name**, different from any of the following previously used quiz names:\n"""\n{prev_quiz_names_text}\n"""'
            if previous_quiz_names
            else "Generate a unique and meaningful name for this quiz."
        )

        prompt = f"""
    You are an experienced teacher and exam creator.

    Using the study material provided below, perform the following:

    1. Suggest a unique and meaningful name for this quiz. {prev_name_instruction}
    2. Generate exactly 15 multiple-choice questions:
        - 5 of **easy** difficulty
        - 5 of **medium** difficulty
        - 5 of **hard** difficulty
        All questions should be {topics_instruction}

    Each question must follow these rules:
    - 4 options labeled 1, 2, 3, 4.
    - One or more options may be correct. Return correct answers as a list, like [1] or [2, 4].

    Format your response as valid JSON like this:

    {{
    "quiz_name": "Meaningful Unique Title",
    "questions": [
        {{
        "question": "What is the capital of France?",
        "options": {{
            "1": "Paris",
            "2": "Berlin",
            "3": "Madrid",
            "4": "Rome"
        }},
        "correct_answer": [1],
        "difficulty": "easy"
        }},
        ...
    ]
    }}

    {prev_qs_instruction}

    Study Material:
    \"\"\"
    {pdf_text}
    \"\"\"

    NOTE:
    - Only return valid JSON.
    - All text must be in English.
    """

        return prompt.strip()

    @classmethod
    def get_topic_generation_prompt(cls):
        system_prompt = """You are an expert assistant for analyzing academic PDFs. You will be given the full text of a multi-page academic PDF.

        For each page, return exactly 2 key topics. Each topic should include:
        - a two-word topic (e.g., "Cave Art")
        - a one-sentence descriptive topic (e.g., "The rise of symbolic cave drawings among Upper Paleolithic humans"), length should not exceed 5 words

        Respond with JSON in the following format:
        {
        "page_1": [
            {"topic": "Cave Art", "description": "The rise of symbolic cave drawings among Upper Paleolithic humans"},
            ...
        ]
        }
        Only include pages that have meaningful content."""
        return system_prompt


class ChatGptMessagePayload:
    @classmethod
    def get_mesasage_payload_for_entire_pdf_summary(cls, prompt: str, pdf_text: str):
        return [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Summarise this PDF content like a teacher:\n\n{pdf_text}",
            },
        ]

    @classmethod
    def get_message_payload_for_quiz(cls, prompt: str) -> list:
        """
        Returns a ChatGPT-compatible payload with the prompt passed as system message.

        Args:
            prompt (str): Prompt string built by `build_quiz_prompt`.

        Returns:
            List[Dict[str, str]]: Message payload for OpenAI API
        """
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": "Generate the quiz now."},
        ]

    @classmethod
    def get_mesasage_payload_for_selected_content_in_pdf_summary(
        cls, prompt: str, pdf_content: str, selected_content: str
    ):
        return [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"""Here is the FULL PDF CONTENT for context:

            {pdf_content}

            ---

            Now, please provide a detailed summary of ONLY this selected content:

            {selected_content}

            Remember to use the full PDF context to enhance your understanding, but summarize only the selected portion.""",
            },
        ]

    @classmethod
    def get_message_payload_for_pdf_questions(cls, prompt: str, pdf_content: str):
        return [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"""Here is the FULL PDF CONTENT to base your response on:

        {pdf_content}

        ---

        Your task is to act as a personal tutor. Based on this content, generate 7 thoughtful open-ended questions to help a student reflect and revise what they've read.

        Each question must:
        - Be between 10 to 15 words long
        - Be directly based on the PDF content
        - Encourage critical thinking or reflection
        - Be followed by a correct and concise answer based on the PDF

        Return only a valid JSON object using this schema:

        {{
        "questions": [
            {{
            "value": "Open-ended question here",
            "answer": "Correct answer here"
            }},
            ...
        ]
        }}

        Do not include a heading. Do not add explanations or any text outside the JSON object.""",
            },
        ]


LOW_POOL_THRESHOLD: int = 2
TOTAL_QUIZ_QUESTIONS:int=10
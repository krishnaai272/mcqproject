# quiz_app/llm_handler.py
import json
from groq import Groq
from . import config

# Define the client once at the top level to be shared by all functions
client = Groq(api_key=config.GROQ_API_KEY)


def generate_mcqs(text_content: str, num_questions=5, difficulty="medium") -> list | None:
    """Generates MCQs from text using the Groq API."""
    prompt = f"""
    Based on the following text, generate {num_questions} multiple-choice questions of {difficulty} difficulty.
    For each question, provide the question, four options (A, B, C, D), the correct option letter, and a brief explanation.
    Provide the output ONLY as a valid JSON object with a single key "questions" which contains a list of the question objects.
    Each question object must have these exact keys: "question", "options", "correct_option", "explanation".
    The "options" value should be an object with keys "A", "B", "C", "D".

    Here is the text:
    ---
    {text_content}
    ---
    """
    print(f"🧠 Generating {num_questions} questions with Groq ({difficulty} difficulty)...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a quiz generation assistant. You must output in the specified JSON format."},
                {"role": "user", "content": prompt},
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        response_content = chat_completion.choices[0].message.content
        quiz_data = json.loads(response_content)
        if "questions" in quiz_data and isinstance(quiz_data["questions"], list):
            print("✅ Questions generated successfully!")
            return quiz_data["questions"]
        else:
            print("Error: The JSON from the API was not in the expected format.")
            return None
    except Exception as e:
        print(f"❌ Error calling Groq API or parsing JSON: {e}")
        return None

# --- NEW: The Intelligent AI Judge Function ---
def verify_voice_answer_semantically(recognized_text: str, correct_option_text: str, question_context: str) -> bool:
    """
    Uses the Groq LLM to semantically verify if a user's spoken answer is correct,
    ignoring option letters and focusing purely on meaning.
    """
    prompt = f"""
    You are a precise semantic quiz validator. Your only job is to determine if the user's spoken answer is conceptually the same as the correct answer.

    **Context for the evaluation:**
    - The quiz question was: "{question_context}"
    - The correct answer's text is: "{correct_option_text}"

    **The user's spoken answer was:** "{recognized_text}"

    **YOUR TASK:**
    Compare the meaning of the user's spoken answer with the meaning of the correct answer's text.

    **CRITICAL INSTRUCTIONS:**
    1.  **IGNORE OPTION LETTERS:** Do not check for letters like 'A', 'B', 'C', or 'D'. The user might say "I think it's B, the one about lifestyle", but you should ONLY evaluate the meaning of "the one about lifestyle".
    2.  **FOCUS ON MEANING:** If the correct answer is "Adopting a heart-healthy lifestyle" and the user says "you should change your diet and exercise", your response must be "true".
    3.  **BE STRICT:** If the user's answer is unrelated or incorrect, your response must be "false".
    4.  **OUTPUT FORMAT:** Your response MUST be ONLY the single word "true" or "false" in lowercase, with no other text or punctuation.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a semantic validator. Your only outputs are 'true' or 'false'."},
                {"role": "user", "content": prompt},
            ],
            model="llama3-8b-8192",
            temperature=0.0,
        )
        response = chat_completion.choices[0].message.content.lower().strip()
        print(f"🤖 AI Judge says: {response}")
        return response == "true"
    except Exception as e:
        print(f"❌ Error during semantic verification with Groq: {e}")
        return False

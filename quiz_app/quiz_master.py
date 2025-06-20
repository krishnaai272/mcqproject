# quiz_app/quiz_master.py
from . import content_processor, llm_handler, voice_interface

class QuizMaster:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.questions = []
        self.score = 0

    def _prepare_quiz(self):
        """Processes the document and generates questions."""
        print("--- Welcome to the Interactive Voice Quiz! ---")
        voice_interface.speak("Let's get your quiz ready.")
        
        document_text = content_processor.process_document(self.file_path)
        if not document_text:
            voice_interface.speak("I'm sorry, I couldn't read the document. The program will now exit.")
            return False

        # Here you can implement logic to ask the user for difficulty
        self.questions = llm_handler.generate_mcqs(document_text, num_questions=3, difficulty="medium")
        if not self.questions:
            voice_interface.speak("I was unable to create questions from the document. Please try another one.")
            return False
        
        return True

    def _check_answer(self, user_answer: str, correct_option: str, options: dict) -> bool:
        """Checks if the user's spoken answer is correct."""
        if not user_answer:
            return False
        
        correct_letter = correct_option.lower()
        correct_text = options[correct_option].lower()
        
        # Check if they said the letter (e.g., "A" or "option A") or the correct text
        if f" {correct_letter} " in f" {user_answer} " or correct_letter == user_answer or correct_text in user_answer:
            return True
        return False

    def start_quiz(self):
        """Starts and manages the main quiz loop."""
        if not self._prepare_quiz():
            return

        voice_interface.speak("Great! Your quiz is ready. Let's begin.")
        
        for i, q in enumerate(self.questions):
            voice_interface.speak(f"Question {i + 1}. {q['question']}")
            
            options_text = ""
            for key, value in q['options'].items():
                options_text += f"{key}. {value}. "
            voice_interface.speak(options_text, slow=True)

            user_answer = voice_interface.listen_for_answer()

            if self._check_answer(user_answer, q['correct_option'], q['options']):
                voice_interface.speak("That's correct! Well done.")
                self.score += 1
            else:
                voice_interface.speak(f"Sorry, that's not right.")
            
            voice_interface.speak(f"The correct answer was {q['correct_option']}. The explanation is: {q['explanation']}")
        
        self._show_final_score()

    def _show_final_score(self):
        """Announces the final score."""
        voice_interface.speak(f"The quiz is complete! You scored {self.score} out of {len(self.questions)}.")
        print(f"\n--- Final Score: {self.score}/{len(self.questions)} ---")

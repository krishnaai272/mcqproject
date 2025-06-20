# Interactive Voice Quiz Generator with Groq

This project is an interactive, voice-based quiz application that generates questions from a provided document and conducts a quiz session entirely through voice. It leverages the high-speed Groq API for question generation, OpenAI's Whisper for speech recognition, and gTTS for voice synthesis.

## Features

-   **Document-Based Quiz Generation**: Create quizzes from your own `.txt` or `.pdf` files.
-   **High-Speed LLM**: Uses the Groq API (Llama 3) for near-instant question and explanation generation.
-   **Voice-Only Interaction**: Asks questions and listens for answers using your microphone.
-   **Instant Feedback**: Provides immediate correctness feedback and detailed explanations for each question.
-   **Professional Structure**: Organized into a modular and maintainable Python package.

## Project Structure

```
.
├── quiz_app/           # Core application logic
├── app.py              # Main entry point to run the app
├── .env                # For API keys (not in git)
├── .gitignore          # To ignore sensitive/unnecessary files
├── README.md           # This file
├── requirements.txt    # Project dependencies
└── sample_document.txt # An example document
```

## Setup and Installation

**1. Clone the Repository**

```bash
git clone <your-repository-url>
cd voice-quiz-groq
```

**2. Create a Virtual Environment**

It's highly recommended to use a virtual environment to manage dependencies.

```bash
# For Windows
python -m venv .venv
.\.venv\Scripts\activate

# For macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install Dependencies**

Install all the required Python libraries using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```
*Note: You may also need to install system-level audio libraries like `portaudio` (`brew install portaudio` on Mac) or `ffmpeg` if you encounter issues with `playsound` or `pyaudio`.*

**4. Set Up API Keys**

Create a file named `.env` in the root directory of the project. Copy the contents of the `.env.example` if you have one, or just add the following lines, replacing the placeholder text with your actual keys.

```ini
# .env file
GROQ_API_KEY="gsk_YourGroqApiKeyHere"
OPENAI_API_KEY="sk-YourOpenaiApiKeyHere"
```

-   Get your Groq key from the [Groq Console](https://console.groq.com/keys).
-   Get your OpenAI key from the [OpenAI Platform](https://platform.openai.com/api-keys) (used for the Whisper API).

## How to Run

1.  Place your document (e.g., `my_notes.txt` or `chapter1.pdf`) in the root directory.
2.  Open `app.py` and change the `DOCUMENT_PATH` variable to point to your file.

    ```python
    # in app.py
    DOCUMENT_PATH = "my_notes.txt"
    ```

    
3.  Run the application from your terminal:

    ```bash
    python app.py
    ```

The application will start, process your document, generate questions, and begin the voice quiz. Make sure your microphone is enabled and ready!

## Responsible AI

This application uses powerful AI models. It's designed for educational and entertainment purposes. The generated questions are based on the content provided and the AI's interpretation, and may not always be perfectly accurate or complete.
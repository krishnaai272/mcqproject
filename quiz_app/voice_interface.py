import os
import speech_recognition as sr


# No longer need to import config here for the OpenAI key

def speak(text: str, slow=False):
    """Converts text to speech and plays it."""
    print(f"🤖 Speaking: {text}")
    try:
        filename = "temp_audio.mp3"
        os.remove(filename)
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        print(f"(Fallback) {text}")

def listen_for_answer() -> str | None:
    """
    Listens for user's voice and converts it to text using the LOCAL Whisper model.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Listening for your answer... (Speak clearly)")
        r.pause_threshold = 1.5
        r.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("👂 Timed out waiting for you to speak.")
            return None

    try:
        print("🤫 Recognizing your speech... (This may take a moment on first run)")
        
        # --- THIS IS THE MODIFIED LINE ---
        # We use recognize_whisper() for the local model instead of recognize_whisper_api()
        # "base.en" is a small, fast model. You can also use "tiny.en".
        recognized_text = r.recognize_whisper(audio, model="base.en").lower()
        
        print(f"👂 You said: '{recognized_text}'")
        return recognized_text
    except sr.UnknownValueError:
        print("👂 Whisper could not understand the audio.")
        return None
    except sr.RequestError as e:
        # This error is now less likely as it's a local process
        print(f"Could not process audio with local Whisper model; {e}")
        return None
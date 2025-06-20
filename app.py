# app.py (Final Version with Python 3.10 fix and correct form logic)
import streamlit as st
import base64
import os
import time

from quiz_app import content_processor, llm_handler, voice_interface

# --- A safe import for the audio recorder component ---
try:
    from st_audiorec import st_audiorec
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

# --- Page Configuration and Helper Functions (no changes) ---
st.set_page_config(page_title="AI Voice Quiz", page_icon="🧠", layout="centered")
st.title("🧠 AI-Powered Quiz Generator")
st.write("Upload a document (.txt, .pdf, or .docx) to start a quiz!")

def autoplay_audio(audio_bytes: bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    md = f"""<audio controls autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>"""
    st.markdown(md, unsafe_allow_html=True)

def text_to_audio_bytes(text: str) -> bytes:
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang='en')
        filename = "temp_audio.mp3"
        tts.save(filename)
        with open(filename, "rb") as f: audio_bytes = f.read()
        os.remove(filename)
        return audio_bytes
    except Exception as e:
        st.error(f"Error generating audio: {e}")
        return None

# --- Session State Initialization (no changes) ---
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.questions = []
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.answer_submitted = False
    st.session_state.wav_audio_data = None # New state to hold recorded audio

# --- File Upload and Quiz Generation (no changes) ---
uploaded_file = st.file_uploader("Choose a document", type=["txt", "pdf", "docx"], disabled=st.session_state.quiz_started)
if uploaded_file and not st.session_state.quiz_started:
    if st.button("Start Quiz!"):
        with st.spinner("Processing document and generating questions..."):
            with open(uploaded_file.name, "wb") as f: f.write(uploaded_file.getbuffer())
            document_text = content_processor.process_document(uploaded_file.name)
            os.remove(uploaded_file.name)
            if document_text:
                questions = llm_handler.generate_mcqs(document_text, num_questions=5)
                if questions:
                    st.session_state.questions, st.session_state.quiz_started = questions, True
                    st.session_state.current_q_index, st.session_state.score, st.session_state.answer_submitted = 0, 0, False
                    st.rerun()
                else: st.error("Could not generate questions.")
            else: st.error("Could not read the document.")

# --- The Main Quiz UI ---
if st.session_state.quiz_started and st.session_state.current_q_index < len(st.session_state.questions):
    q = st.session_state.questions[st.session_state.current_q_index]

    st.header(f"Question {st.session_state.current_q_index + 1}/{len(st.session_state.questions)}")
    st.write(f"**{q['question']}**")

    if not st.session_state.get(f"played_q_{st.session_state.current_q_index}", False):
        audio = text_to_audio_bytes(f"Question {st.session_state.current_q_index + 1}. {q['question']}")
        if audio: autoplay_audio(audio)
        st.session_state[f"played_q_{st.session_state.current_q_index}"] = True
    st.write("---")

    # --- CORRECTED FORM LOGIC ---
    tab1, tab2 = st.tabs(["Type 1: Click to Answer", "Type 2: Speak to Answer"])

    with tab1:
        with st.form(key=f"radio_form_{st.session_state.current_q_index}"):
            options_list = [f"{key}. {value}" for key, value in q['options'].items()]
            DEFAULT_CHOICE = "--- Please select an answer ---"
            options_list.insert(0, DEFAULT_CHOICE)
            user_radio_choice = st.radio("Select your answer:", options_list, index=0, label_visibility="collapsed")
            submitted_radio = st.form_submit_button("Submit Selection")

    with tab2:
        st.write("Click the icon to record, then click 'Submit Voice Answer' below.")
        if AUDIO_RECORDER_AVAILABLE:
            st.session_state.wav_audio_data = st_audiorec()
        else:
            st.warning("Audio recorder component not available.")

        # A separate submit button just for voice
        submitted_voice = st.button("Submit Voice Answer")

    # --- Processing logic now split for each button ---
    
    # Process if the radio button form was submitted
    if submitted_radio:
        is_correct, user_input_provided = False, False
        if user_radio_choice != DEFAULT_CHOICE:
            user_input_provided = True
            is_correct = user_radio_choice.strip().startswith(q['correct_option'])
        
        if user_input_provided:
            # (Feedback logic is the same)
            feedback = "That's correct! Well done." if is_correct else "Sorry, that's not right."
            if is_correct: st.session_state.score += 1; st.success(feedback)
            else: st.error(feedback)
            correct_answer_string = f"The correct answer was {q['correct_option']}. {q['options'][q['correct_option']]}."
            explanation_string = f"The explanation is: {q['explanation']}"
            full_feedback_for_audio = f"Correct. {explanation_string}" if is_correct else f"Sorry. {correct_answer_string} {explanation_string}"
            st.info(f"{correct_answer_string}\n\n{explanation_string}")
            feedback_audio = text_to_audio_bytes(full_feedback_for_audio)
            if feedback_audio: autoplay_audio(feedback_audio)
            st.session_state.answer_submitted = True; time.sleep(1); st.rerun()
        else:
            st.warning("Please select an option before submitting.")

    # Process if the voice button was clicked
    if submitted_voice:
        is_correct, user_input_provided = False, False
        if st.session_state.wav_audio_data:
            user_input_provided = True
            with st.spinner("Recognizing and validating your voice answer..."):
                with open("user_answer.wav", "wb") as f: f.write(st.session_state.wav_audio_data)
                r = voice_interface.sr.Recognizer()
                with voice_interface.sr.AudioFile("user_answer.wav") as source: audio_data = r.record(source)
                try:
                    recognized_text = r.recognize_whisper(audio_data, model="small.en").lower()
                    st.info(f"👂 You said: '{recognized_text}'")
                    correct_option_text = q['options'][q['correct_option']]
                    is_correct = llm_handler.verify_voice_answer_semantically(recognized_text, correct_option_text, q['question'])
                except Exception as e:
                    st.warning(f"Could not recognize your speech. Please try speaking louder. Error: {e}")
        
        if user_input_provided:
            # (Feedback logic is the same)
            feedback = "That's correct! Well done." if is_correct else "Sorry, that's not right."
            if is_correct: st.session_state.score += 1; st.success(feedback)
            else: st.error(feedback)
            correct_answer_string = f"The correct answer was {q['correct_option']}. {q['options'][q['correct_option']]}."
            explanation_string = f"The explanation is: {q['explanation']}"
            full_feedback_for_audio = f"Correct. {explanation_string}" if is_correct else f"Sorry. {correct_answer_string} {explanation_string}"
            st.info(f"{correct_answer_string}\n\n{explanation_string}")
            feedback_audio = text_to_audio_bytes(full_feedback_for_audio)
            if feedback_audio: autoplay_audio(feedback_audio)
            st.session_state.answer_submitted = True; time.sleep(1); st.rerun()
        else:
            st.warning("Please record your voice before submitting.")

    # --- Next Question and Final Score logic remains the same ---
    if st.session_state.answer_submitted:
        if st.session_state.current_q_index < len(st.session_state.questions) - 1:
            if st.button("➡️ Next Question"):
                st.session_state.current_q_index += 1; st.session_state.answer_submitted = False; st.rerun()
        else:
            st.info("You've reached the end of the quiz! See your final score below.")

if st.session_state.quiz_started and st.session_state.current_q_index >= len(st.session_state.questions) - 1 and st.session_state.answer_submitted:
    st.balloons()
    st.success(f"🎉 Quiz Finished! Your Final Score: {st.session_state.score}/{len(st.session_state.questions)}")
    if st.button("Restart Quiz"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
# app.py (Final Version with AI Judge and Complete Feedback)
import streamlit as st
import base64
import os
import time

from quiz_app import content_processor, llm_handler, voice_interface

try:
    from st_audiorec import st_audiorec
    AUDIO_RECORDER_AVAILABLE = True
except ImportError:
    AUDIO_RECORDER_AVAILABLE = False

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

if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.questions = []
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.answer_submitted = False

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
                    st.session_state.questions = questions
                    st.session_state.quiz_started = True
                    st.session_state.current_q_index = 0
                    st.session_state.score = 0
                    st.session_state.answer_submitted = False
                    st.rerun()
                else: st.error("Could not generate questions.")
            else: st.error("Could not read the document.")

if st.session_state.quiz_started and st.session_state.current_q_index < len(st.session_state.questions):
    q = st.session_state.questions[st.session_state.current_q_index]

    st.header(f"Question {st.session_state.current_q_index + 1}/{len(st.session_state.questions)}")
    st.write(f"**{q['question']}**")

    if not st.session_state.get(f"played_q_{st.session_state.current_q_index}", False):
        audio = text_to_audio_bytes(f"Question {st.session_state.current_q_index + 1}. {q['question']}")
        if audio: autoplay_audio(audio)
        st.session_state[f"played_q_{st.session_state.current_q_index}"] = True
    
    st.write("---")

    with st.form(key=f"answer_form_{st.session_state.current_q_index}"):
        tab1, tab2 = st.tabs(["Type 1: Click to Answer", "Type 2: Speak to Answer"])
        with tab1:
            options_list = [f"{key}. {value}" for key, value in q['options'].items()]
            DEFAULT_CHOICE = "--- Please select an answer ---"
            options_list.insert(0, DEFAULT_CHOICE)
            user_radio_choice = st.radio("Select your answer:", options_list, index=0, label_visibility="collapsed")
        with tab2:
            st.write("Click the icon to start and stop recording your answer.")
            wav_audio_data = None
            if AUDIO_RECORDER_AVAILABLE: wav_audio_data = st_audiorec()
            else: st.warning("Audio recorder component not available.")
        
        submitted = st.form_submit_button("Submit Answer")

    if submitted:
        is_correct = False
        user_input_provided = False

        if wav_audio_data:
            user_input_provided = True
            with st.spinner("Recognizing and validating your voice answer..."):
                with open("user_answer.wav", "wb") as f: f.write(wav_audio_data)
                r = voice_interface.sr.Recognizer()
                with voice_interface.sr.AudioFile("user_answer.wav") as source: audio = r.record(source)
                try:
                    # --- UPGRADE: Using a more accurate model to reduce errors ---
                    recognized_text = r.recognize_whisper(audio, model="small.en").lower()
                    st.info(f"👂 You said: '{recognized_text}'")
                    
                    # --- UPGRADE: Calling the new AI Judge function ---
                    correct_option_text = q['options'][q['correct_option']]
                    is_correct = llm_handler.verify_voice_answer_semantically(recognized_text, correct_option_text, q['question'])

                except Exception as e:
                    st.warning(f"Could not recognize your speech. Please try speaking louder and clearer. Error: {e}")
        
        elif user_radio_choice != DEFAULT_CHOICE:
            user_input_provided = True
            is_correct = user_radio_choice.strip().startswith(q['correct_option'])
        
        if user_input_provided:
            # --- UPGRADE: Comprehensive Feedback Logic ---
            correct_answer_string = f"The correct answer was {q['correct_option']}. {q['options'][q['correct_option']]}."
            explanation_string = f"The explanation is: {q['explanation']}"
            
            full_feedback_for_audio = ""
            
            if is_correct:
                st.session_state.score += 1
                st.success("That's correct! Well done.")
                full_feedback_for_audio = f"Correct. {explanation_string}"
            else:
                st.error("Sorry, that's not right.")
                # Construct the full, helpful feedback for when the user is wrong
                full_feedback_for_audio = f"Sorry. {correct_answer_string} {explanation_string}"

            # Always display the full text feedback in the UI for clarity
            st.info(f"{correct_answer_string}\n\n{explanation_string}")
            
            # Play the complete and fluid audio feedback
            feedback_audio = text_to_audio_bytes(full_feedback_for_audio)
            if feedback_audio: autoplay_audio(feedback_audio)
            
            st.session_state.answer_submitted = True
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Please either select an option or record your voice before submitting.")

    if st.session_state.answer_submitted:
        if st.session_state.current_q_index < len(st.session_state.questions) - 1:
            if st.button("➡️ Next Question"):
                st.session_state.current_q_index += 1
                st.session_state.answer_submitted = False
                st.rerun()
        else:
            st.info("You've reached the end of the quiz! See your final score below.")

if st.session_state.quiz_started and st.session_state.current_q_index >= len(st.session_state.questions) - 1 and st.session_state.answer_submitted:
    st.balloons()
    st.success(f"🎉 Quiz Finished! Your Final Score: {st.session_state.score}/{len(st.session_state.questions)}")
    if st.button("Restart Quiz"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
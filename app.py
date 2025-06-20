# app.py (Final Version using streamlit-webrtc for robust audio)
import streamlit as st
import base64
import os
import time
import queue
import wave
import struct

from quiz_app import content_processor, llm_handler, voice_interface

# --- NEW: Using the more robust streamlit-webrtc component ---
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase

st.set_page_config(page_title="AI Voice Quiz", page_icon="🧠", layout="centered")
st.title("🧠 AI-Powered Quiz Generator")
st.write("Upload a document (.txt, .pdf, or .docx) to start a quiz!")

# --- This class captures and processes audio from the browser ---
class AudioRecorder(AudioProcessorBase):
    def __init__(self):
        self.audio_frames = []
        self.is_recording = True # Start recording immediately

    def recv(self, frame):
        if self.is_recording:
            # Add audio frames to a list
            self.audio_frames.append(frame)
        return frame # Return the frame to keep the stream alive

# --- Helper functions ---
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

# Convert raw audio frames to a playable WAV file
def frames_to_wav(frames, filename="user_answer.wav", channels=1, sample_width=2, frame_rate=16000):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(frame_rate)
        # Convert audio frames to bytes
        for frame in frames:
            wf.writeframes(frame.to_ndarray().tobytes())

# --- Session State ---
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.questions = []
    st.session_state.current_q_index = 0
    st.session_state.score = 0
    st.session_state.answer_submitted = False
    st.session_state.webrtc_ctx = None

# --- Main App Logic ---
# (File upload and quiz generation parts are unchanged)
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
            st.write("Click 'Start' to record, then 'Stop' when finished.")
            # --- The new WebRTC component ---
            st.session_state.webrtc_ctx = webrtc_streamer(
                key=f"voice_input_{st.session_state.current_q_index}",
                mode=WebRtcMode.SENDONLY,
                audio_processor_factory=AudioRecorder,
                media_stream_constraints={"video": False, "audio": True},
            )
        submitted = st.form_submit_button("Submit Answer")

    if submitted:
        is_correct, user_input_provided = False, False
        
        # Check if the audio recorder was active and has frames
        if st.session_state.webrtc_ctx and st.session_state.webrtc_ctx.audio_processor and st.session_state.webrtc_ctx.audio_processor.audio_frames:
            user_input_provided = True
            audio_frames = st.session_state.webrtc_ctx.audio_processor.audio_frames
            frames_to_wav(audio_frames) # Save the recorded audio to a file

            with st.spinner("Recognizing and validating your voice answer..."):
                r = voice_interface.sr.Recognizer()
                with voice_interface.sr.AudioFile("user_answer.wav") as source: audio = r.record(source)
                try:
                    recognized_text = r.recognize_whisper(audio, model="small.en").lower()
                    st.info(f"👂 You said: '{recognized_text}'")
                    correct_option_text = q['options'][q['correct_option']]
                    is_correct = llm_handler.verify_voice_answer_semantically(recognized_text, correct_option_text, q['question'])
                except Exception as e: st.warning(f"Could not recognize your speech. Error: {e}")
        
        elif user_radio_choice != DEFAULT_CHOICE:
            user_input_provided = True
            is_correct = user_radio_choice.strip().startswith(q['correct_option'])
        
        if user_input_provided:
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
            st.warning("Please either select an option or record your voice before submitting.")

    # (Next Question and Final Score logic are unchanged)
    if st.session_state.answer_submitted:
        if st.session_state.current_q_index < len(st.session_state.questions) - 1:
            if st.button("➡️ Next Question"):
                st.session_state.current_q_index += 1; st.session_state.answer_submitted = False; st.rerun()
        else: st.info("You've reached the end of the quiz! See your final score below.")
if st.session_state.quiz_started and st.session_state.current_q_index >= len(st.session_state.questions) - 1 and st.session_state.answer_submitted:
    st.balloons()
    st.success(f"🎉 Quiz Finished! Your Final Score: {st.session_state.score}/{len(st.session_state.questions)}")
    if st.button("Restart Quiz"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
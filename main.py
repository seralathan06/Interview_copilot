import gradio as gr
import uuid
import os
import json
import asyncio
import random
import time
from typing import Dict, List, Optional

from stt_service import SpeechHandler

# --- Import the new InterviewLogicNVIDIA and NvidiaConceptExplainer ---
from interviewer_logic_gemini import InterviewLogicNVIDIA # Assuming this file now houses your NVIDIA LLM interview logic
# from summary_logic_gemini import NvidiaConceptExplainer # NEW IMPORT

# --- Dummy Implementations (as in your original combined script) ---
# Retain other dummy classes unless specified for replacement
class ProgressTracker:
    def __init__(self):
        self.scores = {}
    def update_progress(self, user_id: str, correct_answers: int, total_questions: int):
        if user_id not in self.scores:
            self.scores[user_id] = {"correct": 0, "total": 0}
        self.scores[user_id]["correct"] = correct_answers
        self.scores[user_id]["total"] = total_questions
    def get_score(self, user_id: str):
        return self.scores.get(user_id, {"correct": 0, "total": 0})

class NvidiaChatForAptitude:
    def __init__(self):
        print("NVIDIA Chat for Aptitude initialized (conceptual).")
    def nvidia_chat(self, history: list) -> str:
        last_message = history[-1]["content"] if history else "Hello! How can I help with aptitude?"
        return f"NVIDIA Aptitude AI acknowledged: '{last_message}'. I can provide more details if needed."


# Global State for Gradio
aptitude_user_sessions = {
    "default_user": {
        "score": {"correct": 0, "total": 0},
        "chat_history": []
    }
}
QUESTIONS_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "questions.json")
questions_data = []
try:
    with open(QUESTIONS_FILE_PATH, encoding="utf-8") as f:
        questions_data = json.load(f)
except FileNotFoundError:
    print(f"WARNING: questions.json not found at {QUESTIONS_FILE_PATH}. Aptitude questions will not be available.")
except json.JSONDecodeError:
    print(f"ERROR: Could not decode questions.json at {QUESTIONS_FILE_PATH}. Check file format.")

# --- INSTANTIATE NVIDIA CONCEPT EXPLAINER ---
# concept_explainer_instance = NvidiaConceptExplainer() # <-- CHANGE HERE
progress_tracker_instance = ProgressTracker()
nvidia_chat_instance = NvidiaChatForAptitude()

# Initialize a dummy speech handler
speech_handler =SpeechHandler() # Assuming this is defined elsewhere

# Global variable to hold the InterviewLogicNVIDIA instance for the current session
current_interviewer_logic: Optional[InterviewLogicNVIDIA] = None

# Helper function for file transcription (using SpeechRecognition library)
def transcribe_audio_file(filename: str) -> str:
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(filename) as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
        return text
    except Exception as e:
        return f"Error transcribing file: {e}"

# --- Interviewer Tab Functions (unchanged as they use current_interviewer_logic) ---
async def start_interview_single(persona_input: str, difficulty: str):
    global current_interviewer_logic
    
    current_interviewer_logic = InterviewLogicNVIDIA(persona=persona_input)
    
    initial_interviewer_response = await current_interviewer_logic.get_interviewer_response(user_text="")
    
    chatbot_history = [[None, initial_interviewer_response]]
    
    return chatbot_history, gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)

async def respond_to_interviewer_single(user_input: str, chat_history: List[List[Optional[str]]]):
    global current_interviewer_logic
    
    if current_interviewer_logic is None:
        return chat_history + [[None, "Error: Interview not started. Please click 'Start Interview'."]], gr.update(value="", interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
    
    if not user_input.strip():
        return chat_history, gr.update(value="", interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)

    chat_history.append([user_input, None])

    try:
        interviewer_response_text = await current_interviewer_logic.get_interviewer_response(user_text=user_input)
        
        is_done = await current_interviewer_logic.check_if_done(user_input)
        if is_done:
            interviewer_response_text += "\n\n(Interview concluded by AI. Click 'Clear Interview' to restart.)"
            current_interviewer_logic = None
            
        chat_history[-1][1] = interviewer_response_text
        
        if is_done:
            return chat_history, gr.update(value="", interactive=False), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
        else:
            return chat_history, gr.update(value=""), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
    
    except Exception as e:
        error_message = f"Error during interview: {e}"
        chat_history[-1][1] = error_message
        print(f"Error: {e}")
        return chat_history, gr.update(value=""), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)


def clear_interview_single():
    global current_interviewer_logic
    current_interviewer_logic = None
    return [], gr.update(value="", interactive=True), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)

# --- Aptitude Tutor Tab Functions ---
def get_aptitude_user_id():
    return "default_user"

def gradio_get_random_aptitude_question():
    if not questions_data:
        return "No aptitude questions available.", "", 0
    question = random.choice(questions_data)
    return question["question"], ", ".join(question["options"]), question["id"]

def gradio_submit_aptitude_answer(question_id: int, selected_option_index: str):
    user_id = get_aptitude_user_id()
    if not questions_data:
        return "Error: No aptitude questions loaded."
    try:
        selected_option_index_int = int(selected_option_index)
    except ValueError:
        return "Error: Please select a valid option."
    question = next((q for q in questions_data if q["id"] == question_id), None)
    if not question:
        return "Error: Question not found."
    is_correct = (selected_option_index_int == question["correct_option_index"])
    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}
    user_session["score"]["total"] += 1
    if is_correct:
        user_session["score"]["correct"] += 1
    progress_tracker_instance.update_progress(user_id, user_session["score"]["correct"], user_session["score"]["total"])
    status_message = "Correct!" if is_correct else f"Incorrect. The correct option was: {question['options'][question['correct_option_index']]}."
    return status_message + f" Your current score: {user_session['score']['correct']}/{user_session['score']['total']}"

def gradio_get_aptitude_user_progress():
    user_id = get_aptitude_user_id()
    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        return "Start practicing aptitude to see your progress!"
    correct = user_session["score"]["correct"]
    total = user_session["score"]["total"]
    accuracy = (correct / total) * 100 if total > 0 else 0.0
    return f"Correct: {correct}, Total: {total}, Accuracy: {accuracy:.1f}%"

async def gradio_explain_aptitude_concept(topic: str):
    if not topic:
        return "Topic cannot be empty."
    # --- CALL NVIDIA CONCEPT EXPLAINER HERE ---
    explanation = await concept_explainer_instance.explain_concept(topic)
    
    # --- ADD CONSOLE PRINT HERE ---
    print(f"\n--- Concept Explanation for '{topic}' (NVIDIA API) ---\n{explanation}\n-------------------------------------------\n") # New print statement
    
    user_id = get_aptitude_user_id()
    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}
    user_session["chat_history"].extend([
        {"role": "user", "content": f"Explain: {topic}"},
        {"role": "assistant", "content": explanation}
    ])
    return explanation

async def gradio_chat_with_aptitude_ai(message: str, chat_history: list):
    user_id = get_aptitude_user_id()
    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}
    formatted_history = []
    for user_msg, bot_msg in chat_history:
        if user_msg:
            formatted_history.append({"role": "user", "content": user_msg})
        if bot_msg:
            formatted_history.append({"role": "assistant", "content": bot_msg})
    formatted_history.append({"role": "user", "content": message})
    response_text = await asyncio.to_thread(nvidia_chat_instance.nvidia_chat, formatted_history)
    chat_history.append([message, response_text])
    return chat_history

# --- Utility Tab Functions (STT only now) ---
async def gradio_transcribe_uploaded_audio_endpoint(audio_file_path: str):
    if not audio_file_path:
        return "No audio file uploaded."
    try:
        transcription_text = await asyncio.to_thread(transcribe_audio_file, audio_file_path)
        return transcription_text
    except Exception as e:
        return f"Audio transcription failed: {e}"

async def gradio_transcribe_recorded_audio_endpoint(audio_file_path: str):
    if not audio_file_path:
        return "No audio recorded."
    try:
        transcription_text = await asyncio.to_thread(transcribe_audio_file, audio_file_path)
        return transcription_text
    except Exception as e:
        return f"Recording or transcription failed: {e}"

# --- Gradio Interface Layout ---
custom_css = """
.gr-box {
    border: 2px solid #1f77b4 !important;
    border-radius: 8px !important;
}
.gr-button {
    background: linear-gradient(45deg, #1f77b4, #4a90e2) !important;
    border: none !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 4px !important;
}
.gr-button:hover {
    background: linear-gradient(45deg, #1668a5, #3a7bc8) !important;
}
.interviewer-header {
    background: linear-gradient(90deg, #1f77b4, #4a90e2);
    color: white;
    padding: 15px;
    border-radius: 8px;
    text-align: center;
    margin-bottom: 20px;
    font-weight: bold;
    font-size: 18px;
}
.control-panel {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 8px;
    border: 1px solid #ddd;
    margin-bottom: 20px;
}
.chat-container {
    border: 2px solid #1f77b4;
    border-radius: 8px;
    padding: 15px;
    background: white;
}
"""

with gr.Blocks(css=custom_css, title="AI Assistant") as interviewer_tab:
    
    with gr.Row():
        gr.Markdown(
            """
            <div style="text-align: center; width: 100%;">
                <h1 style="color: #1f77b4; margin-bottom: 5px;">AI Assistant</h1>
            </div>
            """,
            elem_id="main-header"
        )
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown(
                """
                <div class="interviewer-header">
                    AI Interviewer
                </div>
                <div style="text-align: center; color: #666; margin-bottom: 20px;">
                    Engage in an interview with an AI powered by NVIDIA's API.
                    You can type your responses or use voice input.
                </div>
                """,
                elem_id="interviewer-description"
            )
            
            with gr.Group(elem_classes="control-panel"):
                gr.Markdown("### Interview Settings")
                persona_input = gr.Textbox(
                    label="Interviewer Persona",
                    value="You are a professional software engineering hiring manager. Ask relevant technical and behavioral questions.",
                    lines=3,
                    placeholder="e.g., 'You are a friendly HR representative...' or 'You are a tough technical lead...'"
                )
                difficulty_radio = gr.Radio(
                    ["Easy", "Medium", "Hard"], 
                    label="Interview Difficulty (Note: Persona might override this)", 
                    value="Medium"
                )
                start_btn = gr.Button("Start Interview", size="lg", variant="primary")
                clear_btn = gr.Button("Clear Interview", size="lg", variant="secondary")
        
        with gr.Column(scale=2):
            gr.Markdown(
                """
                <div class="interviewer-header">
                    INTERVIEW SESSION
                </div>
                """,
                elem_id="interviewer-header"
            )
            
            with gr.Group(elem_classes="chat-container"):
                interviewer_chatbot = gr.Chatbot(
                    label="Interview Conversation",
                    height=400,
                    show_copy_button=True
                )
                
                with gr.Row():
                    user_input = gr.Textbox(
                        label="Your Response",
                        placeholder="Type your response here or use voice input...",
                        lines=2,
                        max_lines=4,
                        scale=4,
                        interactive=False
                    )
                    
                    stt_record_audio_input_interview = gr.Audio(
                        label="Record Your Voice", 
                        sources=["microphone"], 
                        type="filepath", 
                        visible=True,
                        interactive=False
                    )
                    
                    with gr.Column(scale=1):
                        submit_btn = gr.Button("Send Text", size="sm", interactive=False)
                        voice_send_btn = gr.Button("🎤 Send Voice", size="sm", interactive=False) 

    start_btn.click(
        start_interview_single,
        inputs=[persona_input, difficulty_radio],
        outputs=[interviewer_chatbot, user_input, submit_btn, voice_send_btn, stt_record_audio_input_interview]
    )
    
    submit_btn.click(
        respond_to_interviewer_single,
        inputs=[user_input, interviewer_chatbot],
        outputs=[interviewer_chatbot, user_input, submit_btn, voice_send_btn, stt_record_audio_input_interview]
    )
    
    user_input.submit(
        respond_to_interviewer_single,
        inputs=[user_input, interviewer_chatbot],
        outputs=[interviewer_chatbot, user_input, submit_btn, voice_send_btn, stt_record_audio_input_interview]
    )

    voice_send_btn.click(
        gradio_transcribe_recorded_audio_endpoint,
        inputs=[stt_record_audio_input_interview],
        outputs=[user_input]
    ).then(
        respond_to_interviewer_single,
        inputs=[user_input, interviewer_chatbot],
        outputs=[interviewer_chatbot, user_input, submit_btn, voice_send_btn, stt_record_audio_input_interview]
    )
    
    clear_btn.click(
        clear_interview_single,
        outputs=[interviewer_chatbot, user_input, submit_btn, voice_send_btn, stt_record_audio_input_interview]
    )
    
    gr.Markdown(
        """
        ### Instructions:
        1. Set the **Interviewer Persona** and **Difficulty** (optional, persona is primary).
        2. Click **Start Interview** to begin. The AI will greet you and ask the first question.
        3. Type your response in the **Your Response** box or **Record Your Voice**.
        4. Click **Send Text** or **🎤 Send Voice** to submit your answer.
        5. The conversation will continue until the AI interviewer concludes or you click **Clear Interview**.
        """,
        elem_id="instructions"
    )

# Aptitude Tutor Tab
with gr.Blocks() as aptitude_tab:
    gr.Markdown("# AI Aptitude Tutor")
    gr.Markdown("Practice aptitude questions, get explanations, and chat with an AI tutor.")

    with gr.Tab("Questions"):
        apt_question_output = gr.Markdown("Click 'Get New Question' to start.")
        apt_options_display = gr.Textbox(label="Options", interactive=False)
        apt_question_id_state = gr.State(value=0)

        get_question_btn = gr.Button("Get New Question", variant="primary")
        
        selected_option_index_input = gr.Radio(
            ["0", "1", "2", "3"], label="Select your answer (index)", info="Example: 0 for the first option"
        )
        submit_answer_btn = gr.Button("Submit Answer", variant="secondary")
        apt_answer_status = gr.Textbox(label="Answer Status", interactive=False)
        
        get_question_btn.click(
            gradio_get_random_aptitude_question,
            outputs=[apt_question_output, apt_options_display, apt_question_id_state]
        )
        submit_answer_btn.click(
            gradio_submit_aptitude_answer,
            inputs=[apt_question_id_state, selected_option_index_input],
            outputs=apt_answer_status
        )

    with gr.Tab("Progress"):
        apt_progress_output = gr.Textbox(label="Your Aptitude Progress", interactive=False)
        get_progress_btn = gr.Button("Refresh Progress")
        get_progress_btn.click(gradio_get_aptitude_user_progress, outputs=apt_progress_output)

    with gr.Tab("Concept Explainer"):
        concept_topic_input = gr.Textbox(label="Topic to Explain", placeholder="e.g., 'Probability', 'Quadratic Equations'")
        explain_concept_btn = gr.Button("Explain Concept")
        concept_explanation_output = gr.Textbox(label="Explanation", lines=10, interactive=False)
        explain_concept_btn.click(gradio_explain_aptitude_concept, inputs=concept_topic_input, outputs=concept_explanation_output)

    with gr.Tab("Tutor Chat (NVIDIA Concept)"):
        apt_tutor_chatbot = gr.Chatbot(label="Aptitude Tutor Chat")
        apt_chat_input = gr.Textbox(label="Your Message", placeholder="Ask me anything about aptitude...")
        apt_chat_send_btn = gr.Button("Send")
        apt_chat_send_btn.click(
            gradio_chat_with_aptitude_ai,
            inputs=[apt_chat_input, apt_tutor_chatbot],
            outputs=apt_tutor_chatbot
        )
        apt_chat_input.submit(
            gradio_chat_with_aptitude_ai,
            inputs=[apt_chat_input, apt_tutor_chatbot],
            outputs=apt_tutor_chatbot
        )


# Utility Tab (Now only Speech-to-Text)
with gr.Blocks() as utility_tab:
    gr.Markdown("# AI Utilities (SpeechRecognition STT)")
    gr.Markdown("Transcribe audio using SpeechRecognition.")

    with gr.Tab("Speech-to-Text"):
        gr.Markdown("### Transcribe Uploaded Audio")
        stt_upload_audio_input = gr.File(label="Upload Audio File", type="filepath")
        stt_upload_output = gr.Textbox(label="Transcription (Uploaded)", interactive=False)
        stt_upload_btn = gr.Button("Transcribe Uploaded")
        stt_upload_btn.click(gradio_transcribe_uploaded_audio_endpoint, inputs=stt_upload_audio_input, outputs=stt_upload_output)

        gr.Markdown("### Transcribe Recorded Audio")
        stt_record_audio_input_utility = gr.Audio(label="Record Your Voice", sources=["microphone"], type="filepath")
        stt_record_output = gr.Textbox(label="Transcription (Recorded)", interactive=False)
        stt_record_btn = gr.Button("Transcribe Recorded")
        stt_record_btn.click(gradio_transcribe_recorded_audio_endpoint, inputs=stt_record_audio_input_utility, outputs=stt_record_output)


# Combine all tabs into a single Gradio App
gr.TabbedInterface(
    [interviewer_tab, aptitude_tab, utility_tab],
    ["Interviewer", "Aptitude Tutor", "Utilities"],
    title="AI Assistant (Gradio - Gemini & NVIDIA)"
).launch(share=True)
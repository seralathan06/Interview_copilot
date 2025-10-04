# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import uuid
import os
import io
import json
import asyncio
import threading # For running blocking PyAudio in a separate thread
import random # For aptitude tutor questions
import time # For aptitude tutor, though not strictly used in current dummy

# Import core logic from refactored modules
from tts_service import OpenAITextToSpeech
try:
    from stt_service import OpenAIAudioTranscriber, record_audio_blocking
except Exception:
    # Fallback stub implementations when stt_service is not available.
    # These stubs surface clear runtime errors or return harmless defaults,
    # allowing the rest of the module to be imported and edited without import errors.
    class OpenAIAudioTranscriber:
        async def transcribe_audio_from_bytes(self, data: bytes, filename: str, content_type: str) -> str:
            raise RuntimeError(
                "stt_service is not installed or could not be imported. "
                "Install the stt_service package or provide a local implementation."
            )

    def record_audio_blocking():
        # Minimal harmless stub: no frames, default format/channel/rate placeholders.
        # Replace with real recording logic (e.g., using PyAudio) in production.
        return [], None, 1, 16000
from interviewer_logic import InterviewLogic
from summary_logic import InterviewSummarizer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="AI Assistant Backend", # Changed title to be more general
    description="API for AI-powered interviews, aptitude tutoring, and general AI utilities.",
    version="0.1.0",
)

# --- Interviewer Session Store (for demonstration purposes) ---
# In a real application, replace this with a proper database or Redis.
interview_sessions: Dict[str, InterviewLogic] = {}

# --- Aptitude Tutor User Sessions (for demonstration purposes) ---
# In a real application, replace this with a proper database or Redis per user
aptitude_user_sessions = {
    "default_user": {
        "score": {"correct": 0, "total": 0},
        "chat_history": [] # Chat history for the Nvidia chat part
    }
}

# --- Pydantic Models for API Request/Response (Interviewer) ---

class InterviewStartRequest(BaseModel):
    persona_path: str = Field(..., description="Path to the interviewer persona file (e.g., 'personas/ethan.txt')")
    difficulty: str = Field("medium", description="Difficulty of the interview (easy, medium, hard)")

class InterviewStartResponse(BaseModel):
    session_id: str
    interviewer_message: str # The first question/greeting from the interviewer

class InterviewResponseRequest(BaseModel):
    user_text: str = Field(..., description="Interviewee's response as text.")

class InterviewResponse(BaseModel):
    interviewer_message: str # The interviewer's next response
    is_interview_done: bool # Flag indicating if the interviewer considers the interview finished

class ConversationTurn(BaseModel):
    role: str
    content: str

class InterviewHistoryResponse(BaseModel):
    session_id: str
    history: List[ConversationTurn]
    is_done: bool

class SummarizeRequest(BaseModel):
    criteria_path: str = Field(..., description="Path to the summary criteria file (e.g., 'guidelines/meta-sweml-response-guidelines.txt')")

class SummaryResponse(BaseModel):
    summary: str

class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy" # Default voice

class TranscribeResponse(BaseModel):
    transcription: str

# --- Dummy Implementations for Aptitude Tutor external modules ---
# (Place these at the top level or in a separate file if preferred)
class ConceptExplainer:
    def explain_concept(self, topic: str) -> str:
        # Simulate an explanation
        return f"This is a detailed explanation of {topic}. It covers its definition, uses, and related concepts."

class ProgressTracker:
    def __init__(self):
        # This will track global score if needed, but per-user session is used for now.
        # Keeping it for consistency with original code.
        self.scores = {} # user_id: {"correct": int, "total": int}

    def update_progress(self, user_id: str, correct_answers: int, total_questions: int):
        # In this integrated app, we're mostly using aptitude_user_sessions directly.
        # This dummy updates its internal state but might not be fully synchronized
        # with aptitude_user_sessions without explicit logic.
        if user_id not in self.scores:
            self.scores[user_id] = {"correct": 0, "total": 0}
        self.scores[user_id]["correct"] = correct_answers
        self.scores[user_id]["total"] = total_questions

    def get_score(self, user_id: str):
        return self.scores.get(user_id, {"correct": 0, "total": 0})

class NvidiaChat:
    def nvidia_chat(self, history: list) -> str:
        # Simulate a chat response
        last_message = history[-1]["content"] if history else "Hello! How can I help?"
        return f"Acknowledged: '{last_message}'. I can provide more details if needed."

    def summarise_explanation(self, explanation: str) -> str:
        # Simulate summarization
        return f"Summary of: {explanation[:min(len(explanation), 50)]}..."

# --- Aptitude Tutor Specific Pydantic Models ---
class Question(BaseModel):
    id: int
    question: str
    options: list[str]

class Answer(BaseModel):
    question_id: int
    selected_option_index: int

# Note: ProgressUpdate was in the original snippet but not used in endpoints directly.
# The endpoint /progress returns the score directly.

class ChatMessage(BaseModel):
    message: str # User's message to the chat model

class TopicRequest(BaseModel):
    topic: str

# --- Services Initialization ---
tts_service = OpenAITextToSpeech()
stt_service = OpenAIAudioTranscriber()
summarizer = InterviewSummarizer() # For interview summarization

# Aptitude Tutor specific services
concept_explainer_instance = ConceptExplainer()
progress_tracker_instance = ProgressTracker() # Dummy progress tracker
nvidia_chat_instance = NvidiaChat()

# --- Load Aptitude Questions ---
QUESTIONS_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "questions.json")
questions_data = []
try:
    with open(QUESTIONS_FILE_PATH, encoding="utf-8") as f:
        questions_data = json.load(f)
except FileNotFoundError:
    print(f"WARNING: questions.json not found at {QUESTIONS_FILE_PATH}. Aptitude questions will not be available.")
    questions_data = [] # Ensure it's an empty list if file not found
except json.JSONDecodeError:
    print(f"ERROR: Could not decode questions.json at {QUESTIONS_FILE_PATH}. Check file format.")
    questions_data = []


# --- General Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Assistant Backend! Check /docs for available APIs."}


# --- INTERVIEWER Endpoints ---
@app.post("/interview/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    """
    Starts a new interview session.
    """
    session_id = str(uuid.uuid4())
    
    # Ensure persona_path is safe and relative to the current working directory or a known 'personas' folder
    # For simplicity, assuming persona_path is directly passed and files are in 'personas/'
    full_persona_file_path = os.path.join(os.path.dirname(__file__), request.persona_path)

    try:
        with open(full_persona_file_path, 'r') as f:
            persona = f.read()
        
        full_persona = f"{persona}\nBegin the interview. You are the interviewer and I am the interviewee. Please be very concise as the interviewer in your answers but do not skip the formalities. Use this opportunity to pick up on interviewee social cues. Keep in mind time is limited and make this interview {request.difficulty}"
        
        interview_logic = InterviewLogic(full_persona)
        
        # Get the first message from the interviewer by passing an empty initial user input
        # The InterviewLogic expects a user input, so for the first message, we send an implicit start signal
        first_interviewer_message = await interview_logic.get_interviewer_response("Hello, let's start the interview.") 
        
        interview_sessions[session_id] = interview_logic
        return InterviewStartResponse(
            session_id=session_id,
            interviewer_message=first_interviewer_message
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Persona file not found at {full_persona_file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {e}")

@app.post("/interview/{session_id}/respond", response_model=InterviewResponse)
async def respond_to_interview(session_id: str, request: InterviewResponseRequest):
    """
    Sends the interviewee's response and gets the interviewer's next message.
    """
    interview_logic = interview_sessions.get(session_id)
    if not interview_logic:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    
    if interview_logic.is_done_flag: # Check if interview was marked done previously
        raise HTTPException(status_code=400, detail="Interview is already finished. Please start a new session or end this one to summarize.")

    try:
        interviewer_message = await interview_logic.get_interviewer_response(request.user_text)
        
        # Check if the interviewer considers the interview done based on the last response
        is_done = await interview_logic.check_if_done(interviewer_message)
        interview_logic.is_done_flag = is_done # Update the flag in the session state

        return InterviewResponse(
            interviewer_message=interviewer_message,
            is_interview_done=is_done
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get interviewer response: {e}")

@app.get("/interview/{session_id}/history", response_model=InterviewHistoryResponse)
async def get_interview_history(session_id: str):
    """
    Retrieves the full conversation history for a given session.
    """
    interview_logic = interview_sessions.get(session_id)
    if not interview_logic:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    
    history_pydantic = [ConversationTurn(role=turn['role'], content=turn['content']) for turn in interview_logic.history]
    return InterviewHistoryResponse(session_id=session_id, history=history_pydantic, is_done=interview_logic.is_done_flag)

@app.post("/interview/{session_id}/end", response_model=SummaryResponse)
async def end_interview_and_summarize(session_id: str, request: SummarizeRequest):
    """
    Explicitly ends an interview and generates a summary based on predefined criteria.
    """
    interview_logic = interview_sessions.get(session_id)
    if not interview_logic:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    
    # Ensure criteria_path is safe and relative to the current working directory or a known 'guidelines' folder
    full_criteria_file_path = os.path.join(os.path.dirname(__file__), request.criteria_path)

    try:
        with open(full_criteria_file_path, 'r') as f:
            criteria = f.read()

        summary_text = await asyncio.to_thread(
            summarizer.summarize_interview, interview_logic.history, criteria
        )
        
        # Clean up session (optional, depending on desired behavior)
        del interview_sessions[session_id]
        
        return SummaryResponse(summary=summary_text)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Criteria file not found at {full_criteria_file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize interview: {e}")

# --- UTILITY Endpoints (TTS and STT) ---

@app.post("/tts", response_class=io.BytesIO) # Return raw audio bytes
async def text_to_speech_endpoint(request: TTSRequest):
    """
    Converts text to speech and returns the audio content.
    """
    try:
        audio_buffer = await tts_service.text_to_speech(request.text, request.voice)
        return audio_buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text-to-speech failed: {e}")

@app.post("/transcribe/upload", response_model=TranscribeResponse)
async def transcribe_uploaded_audio_endpoint(audio_file: UploadFile = File(...)):
    """
    Transcribes an uploaded audio file using OpenAI Whisper.
    """
    if not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an audio file.")
    
    try:
        file_content = await audio_file.read()
        transcription_text = await stt_service.transcribe_audio_from_bytes(
            file_content, audio_file.filename, audio_file.content_type
        )
        return TranscribeResponse(transcription=transcription_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {e}")

@app.post("/transcribe/record", response_model=TranscribeResponse)
async def transcribe_recorded_audio_endpoint():
    """
    Records audio from the microphone until silence and transcribes it.
    This endpoint is blocking due to PyAudio. In a production setting,
    consider running this in a dedicated worker process or a separate service.
    """
    try:
        # Run the blocking PyAudio recording in a separate thread
        frames, audio_format, channels, rate = await asyncio.to_thread(record_audio_blocking)
        
        if not frames:
            raise HTTPException(status_code=400, detail="No audio recorded.")

        audio_buffer = io.BytesIO()
        with wave.open(audio_buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(audio_format))
            wf.setframerate(rate)
            wf.writeframes(b''.join(frames))
        audio_buffer.seek(0)
        
        transcription_text = await stt_service.transcribe_audio_from_bytes(
            audio_buffer.getvalue(), "recorded_audio.wav", "audio/wav"
        )
        return TranscribeResponse(transcription=transcription_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recording or transcription failed: {e}")

# --- APTITUDE TUTOR Endpoints ---
@app.get("/aptitude/questions/random", response_model=Question)
async def get_random_aptitude_question():
    """Returns a random question from the aptitude dataset."""
    if not questions_data:
        raise HTTPException(status_code=404, detail="No aptitude questions available. Check server logs.")
    
    question = random.choice(questions_data)
    # Exclude the correct_option_index from the response for the client
    return Question(
        id=question["id"],
        question=question["question"],
        options=question["options"]
    )

@app.post("/aptitude/questions/submit_answer")
async def submit_aptitude_answer(answer: Answer, user_id: str = "default_user"):
    """Submits an answer to an aptitude question and updates the user's score."""
    if not questions_data:
        raise HTTPException(status_code=404, detail="No aptitude questions loaded.")

    question = next((q for q in questions_data if q["id"] == answer.question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in dataset")

    is_correct = (answer.selected_option_index == question["correct_option_index"])

    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        # Initialize session for new user if needed, or handle as error
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}

    user_session["score"]["total"] += 1
    if is_correct:
        user_session["score"]["correct"] += 1
    
    # Update global dummy progress tracker
    progress_tracker_instance.update_progress(user_id, user_session["score"]["correct"], user_session["score"]["total"])

    return {"is_correct": is_correct, "correct_option_index": question["correct_option_index"]}

@app.get("/aptitude/progress")
async def get_aptitude_user_progress(user_id: str = "default_user"):
    """Returns the current progress (score) for a user in the aptitude section."""
    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        return {"correct": 0, "total": 0, "accuracy": 0.0, "message": "Start practicing aptitude to see your progress!"}

    correct = user_session["score"]["correct"]
    total = user_session["score"]["total"]
    
    accuracy = (correct / total) * 100 if total > 0 else 0.0
    
    return {
        "correct": correct,
        "total": total,
        "accuracy": f"{accuracy:.1f}%"
    }

@app.post("/aptitude/explain_concept")
async def explain_aptitude_concept_endpoint(request: TopicRequest, user_id: str = "default_user"):
    """Generates an explanation for a given topic relevant to aptitude."""
    if not request.topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    # Concept Explainer might be synchronous, run in thread pool
    explanation = await asyncio.to_thread(concept_explainer_instance.explain_concept, request.topic)

    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}
    
    # Add to chat history (optional, if you want this in a separate chat context)
    user_session["chat_history"].extend([
        {"role": "user", "content": f"Explain: {request.topic}"},
        {"role": "assistant", "content": explanation}
    ])
    
    return {"explanation": explanation}

@app.get("/aptitude/chat_history")
async def get_aptitude_chat_history(user_id: str = "default_user"):
    """Returns the chat history for a user in the aptitude section."""
    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        return []
    return user_session["chat_history"]

@app.post("/aptitude/chat")
async def chat_with_aptitude_ai(message: ChatMessage, user_id: str = "default_user"):
    """Sends a message to the Nvidia chat model (or a generic chat model) and returns a response for aptitude-related queries."""
    if not message.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}

    user_session["chat_history"].append({"role": "user", "content": message.message})
    
    # Nvidia chat call is synchronous, run in thread pool
    response = await asyncio.to_thread(nvidia_chat_instance.nvidia_chat, user_session["chat_history"])
    user_session["chat_history"].append({"role": "assistant", "content": response})
    
    return {"response": response}
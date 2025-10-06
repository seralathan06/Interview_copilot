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
import random

# Import core logic from refactored modules - NOW USING GEMINI AND NVIDIA
from tts_service_nvidia import NvidiaTextToSpeech # Changed to NVIDIA TTS
from stt_service import OpenAIAudioTranscriber # Keeping OpenAI STT as NVIDIA STT integration is complex
from interviewer_logic_gemini import InterviewLogicGemini # Changed to Gemini Interviewer Logic
from summary_logic_gemini import InterviewSummarizerGemini # Changed to Gemini Summarizer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="AI Assistant Backend (Gemini & NVIDIA)", # Updated title
    description="API for AI-powered interviews (Gemini), aptitude tutoring, and general AI utilities (NVIDIA TTS, OpenAI STT).",
    version="0.2.0",
)

# --- Interviewer Session Store (for demonstration purposes) ---
interview_sessions: Dict[str, InterviewLogicGemini] = {} # Changed type

# --- Aptitude Tutor User Sessions (for demonstration purposes) ---
aptitude_user_sessions = {
    "default_user": {
        "score": {"correct": 0, "total": 0},
        "chat_history": [] # Chat history for the Nvidia chat part
    }
}

# --- Pydantic Models for API Request/Response (Interviewer) ---
# These models remain the same as they define the API contract, not the internal AI model.
class InterviewStartRequest(BaseModel):
    persona_path: str = Field(..., description="Path to the interviewer persona file (e.g., 'personas/ethan.txt')")
    difficulty: str = Field("medium", description="Difficulty of the interview (easy, medium, hard)")

class InterviewStartResponse(BaseModel):
    session_id: str
    interviewer_message: str

class InterviewResponseRequest(BaseModel):
    user_text: str = Field(..., description="Interviewee's response as text.")

class InterviewResponse(BaseModel):
    interviewer_message: str
    is_interview_done: bool

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
    voice: str = "default_nvidia_voice" # Default voice for NVIDIA TTS

class TranscribeResponse(BaseModel):
    transcription: str

# --- Dummy Implementations for Aptitude Tutor external modules ---
# These are kept for the aptitude section.
class ConceptExplainer:
    def explain_concept(self, topic: str) -> str:
        return f"This is a detailed explanation of {topic}. It covers its definition, uses, and related concepts."

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

# --- NVIDIA Chat for Aptitude Tutor (Conceptual) ---
class NvidiaChatForAptitude:
    def __init__(self):
        # Initialize NVIDIA AI Foundation Models chat client here if available
        # E.g., using NVIDIA NeMo Guardrails or a specific NVIDIA chat endpoint
        print("NVIDIA Chat for Aptitude initialized (conceptual).")

    def nvidia_chat(self, history: list) -> str:
        """
        Simulates a chat response from an NVIDIA model.
        For a real implementation, integrate with NVIDIA AI Foundation Models for chat.
        """
        last_message = history[-1]["content"] if history else "Hello! How can I help with aptitude?"
        
        # --- REPLACE THIS SECTION WITH ACTUAL NVIDIA CHAT API CALLS ---
        # Example using a conceptual NVIDIA chat API:
        # headers = {"Authorization": f"Bearer {os.getenv('NVIDIA_API_KEY')}"}
        # payload = {"messages": [{"role": m['role'], "content": m['content']} for m in history]}
        # response = requests.post(os.getenv("NVIDIA_CHAT_API_URL"), headers=headers, json=payload)
        # return response.json()['choices'][0]['message']['content']
        # --- END OF PLACEHOLDER SECTION ---

        return f"NVIDIA Aptitude AI acknowledged: '{last_message}'. I can provide more details if needed."

# --- Aptitude Tutor Specific Pydantic Models ---
class Question(BaseModel):
    id: int
    question: str
    options: list[str]

class Answer(BaseModel):
    question_id: int
    selected_option_index: int

class ChatMessage(BaseModel):
    message: str

class TopicRequest(BaseModel):
    topic: str

# --- Services Initialization ---
tts_service = NvidiaTextToSpeech() # Using NVIDIA TTS
stt_service = OpenAIAudioTranscriber() # Keeping OpenAI STT
interviewer_logic_class = InterviewLogicGemini # Using Gemini for interviewer logic
summarizer = InterviewSummarizerGemini() # Using Gemini for summarization

# Aptitude Tutor specific services
concept_explainer_instance = ConceptExplainer()
progress_tracker_instance = ProgressTracker()
nvidia_chat_instance = NvidiaChatForAptitude() # Using NVIDIA Chat for aptitude

# --- Load Aptitude Questions ---
QUESTIONS_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "questions.json")
questions_data = []
try:
    with open(QUESTIONS_FILE_PATH, encoding="utf-8") as f:
        questions_data = json.load(f)
except FileNotFoundError:
    print(f"WARNING: questions.json not found at {QUESTIONS_FILE_PATH}. Aptitude questions will not be available.")
    questions_data = []
except json.JSONDecodeError:
    print(f"ERROR: Could not decode questions.json at {QUESTIONS_FILE_PATH}. Check file format.")
    questions_data = []


# --- General Root Endpoint ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the AI Assistant Backend (Gemini & NVIDIA)! Check /docs for available APIs."}


# --- INTERVIEWER Endpoints (using Gemini) ---
@app.post("/interview/start", response_model=InterviewStartResponse)
async def start_interview(request: InterviewStartRequest):
    """
    Starts a new interview session using Gemini AI.
    """
    session_id = str(uuid.uuid4())
    
    full_persona_file_path = os.path.join(os.path.dirname(__file__), request.persona_path)

    try:
        with open(full_persona_file_path, 'r') as f:
            persona = f.read()
        
        full_persona = f"{persona}\nBegin the interview. You are the interviewer and I am the interviewee. Please be very concise as the interviewer in your answers but do not skip the formalities. Use this opportunity to pick up on interviewee social cues. Keep in mind time is limited and make this interview {request.difficulty}"
        
        interview_logic = interviewer_logic_class(full_persona) # Use Gemini Logic
        
        # The first message from the AI is generated by its initial setup, as handled in InterviewLogicGemini's __init__
        # and first call to get_interviewer_response.
        # It's crucial to call get_interviewer_response once without prior user_text
        # to trigger the AI's first persona-based greeting/question.
        
        # Call with an empty string or a generic start signal if `get_interviewer_response`
        # handles the initial AI-driven greeting logic.
        first_interviewer_message = await interview_logic.get_interviewer_response("") 
        
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
    Sends the interviewee's response and gets the interviewer's next message using Gemini AI.
    """
    interview_logic = interview_sessions.get(session_id)
    if not interview_logic:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    
    if interview_logic.is_done_flag:
        raise HTTPException(status_code=400, detail="Interview is already finished. Please start a new session or end this one to summarize.")

    try:
        interviewer_message = await interview_logic.get_interviewer_response(request.user_text)
        
        is_done = await interview_logic.check_if_done(interviewer_message)
        interview_logic.is_done_flag = is_done

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
    Explicitly ends an interview and generates a summary using Gemini AI based on predefined criteria.
    """
    interview_logic = interview_sessions.get(session_id)
    if not interview_logic:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    
    full_criteria_file_path = os.path.join(os.path.dirname(__file__), request.criteria_path)

    try:
        with open(full_criteria_file_path, 'r') as f:
            criteria = f.read()

        summary_text = await asyncio.to_thread(
            summarizer.summarize_interview, interview_logic.history, criteria
        )
        
        del interview_sessions[session_id]
        
        return SummaryResponse(summary=summary_text)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Criteria file not found at {full_criteria_file_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize interview: {e}")

# --- UTILITY Endpoints (NVIDIA TTS and OpenAI STT) ---

@app.post("/tts", response_class=io.BytesIO) # Return raw audio bytes
async def text_to_speech_endpoint(request: TTSRequest):
    """
    Converts text to speech using NVIDIA TTS and returns the audio content.
    """
    try:
        audio_buffer = await tts_service.text_to_speech(request.text, request.voice)
        return audio_buffer
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NVIDIA Text-to-speech failed: {e}")

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
        raise HTTPException(status_code=500, detail=f"OpenAI Audio transcription failed: {e}")

@app.post("/transcribe/record", response_model=TranscribeResponse)
async def transcribe_recorded_audio_endpoint():
    """
    Records audio from the microphone until silence and transcribes it using OpenAI Whisper.
    This endpoint is blocking due to PyAudio.
    """
    try:
        frames, audio_format, channels, rate = await asyncio.to_thread(record_audio_blocking)
        
        if not frames:
            raise HTTPException(status_code=400, detail="No audio recorded.")

        audio_buffer = io.BytesIO()
        import pyaudio, wave # Import locally as needed if not used elsewhere
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
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}

    user_session["score"]["total"] += 1
    if is_correct:
        user_session["score"]["correct"] += 1
    
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

    explanation = await asyncio.to_thread(concept_explainer_instance.explain_concept, request.topic)

    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}
    
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
    """Sends a message to the NVIDIA chat model (conceptual) for aptitude-related queries."""
    if not message.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    user_session = aptitude_user_sessions.get(user_id)
    if not user_session:
        user_session = aptitude_user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}

    user_session["chat_history"].append({"role": "user", "content": message.message})
    
    response = await asyncio.to_thread(nvidia_chat_instance.nvidia_chat, user_session["chat_history"])
    user_session["chat_history"].append({"role": "assistant", "content": response})
    
    return {"response": response}
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import random
import time

# Assuming these modules are available in your environment
# You'll need to create dummy versions or provide actual implementations
# for a fully runnable example if they aren't already
# from concept_explainer import explain_concept
# from progress_tracker import update_progress, get_score
# from nvidia_chat import nvidia_chat, summarise_explanation

app = FastAPI(title="Aptitude Tutor Backend")

# --- Dummy Implementations for external modules (replace with your actual ones) ---
class ConceptExplainer:
    def explain_concept(self, topic: str) -> str:
        # Simulate an explanation
        return f"This is a detailed explanation of {topic}. It covers its definition, uses, and related concepts."

class ProgressTracker:
    def __init__(self):
        self.scores = {} # user_id: {"correct": int, "total": int}

    def update_progress(self, user_id: str, correct_answers: int, total_questions: int):
        if user_id not in self.scores:
            self.scores[user_id] = {"correct": 0, "total": 0}
        self.scores[user_id]["correct"] = correct_answers
        self.scores[user_id]["total"] = total_questions

    def get_score(self, user_id: str):
        return self.scores.get(user_id, {"correct": 0, "total": 0})

class NvidiaChat:
    def nvidia_chat(self, history: list) -> str:
        # Simulate a chat response
        last_message = history[-1]["content"] if history else "Hello!"
        return f"Acknowledged: '{last_message}'"

    def summarise_explanation(self, explanation: str) -> str:
        # Simulate summarization
        return f"Summary of: {explanation[:50]}..."

concept_explainer_instance = ConceptExplainer()
progress_tracker_instance = ProgressTracker()
nvidia_chat_instance = NvidiaChat()
# ---------------------------------------------------------------------------------

# Load questions
try:
    with open("D:\GEN AI\APITUDE_ASSIATANT\ApitiAssistant\data\questions.json", encoding="utf-8") as f:
        questions_data = json.load(f)
except FileNotFoundError:
    raise RuntimeError("questions.json not found. Please create a 'data' directory with your questions.json file.")

# In-memory "session" for demonstration purposes for a single user
# In a real app, this would be a database or cache per user
user_sessions = {
    "default_user": {
        "score": {"correct": 0, "total": 0},
        "chat_history": []
    }
}

class Question(BaseModel):
    id: int
    question: str
    options: list[str]

class Answer(BaseModel):
    question_id: int
    selected_option_index: int

class ProgressUpdate(BaseModel):
    correct_answers: int
    total_questions: int

@app.get("/")
async def read_root():
    return {"message": "Welcome to Aptitude Tutor Backend!"}

# --- PRACTICE QUESTION Endpoints ---
@app.get("/questions/random", response_model=Question)
async def get_random_question():
    """Returns a random question from the dataset."""
    if not questions_data:
        raise HTTPException(status_code=404, detail="No questions available")
    
    question = random.choice(questions_data)
    # Exclude the correct_option_index from the response
    return Question(
        id=question["id"],
        question=question["question"],
        options=question["options"]
    )

@app.post("/questions/submit_answer")
async def submit_answer(answer: Answer, user_id: str = "default_user"):
    """Submits an answer to a question and updates the user's score."""
    question = next((q for q in questions_data if q["id"] == answer.question_id), None)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = (answer.selected_option_index == question["correct_option_index"])

    user_session = user_sessions.get(user_id)
    if not user_session:
        # Initialize session for new user if needed, or handle as error
        user_session = user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}

    user_session["score"]["total"] += 1
    if is_correct:
        user_session["score"]["correct"] += 1
    
    # Update global progress tracker if it's meant to be global,
    # otherwise manage it within user_session
    progress_tracker_instance.update_progress(user_id, user_session["score"]["correct"], user_session["score"]["total"])

    return {"is_correct": is_correct, "correct_option_index": question["correct_option_index"]}

# --- PROGRESS VIEW Endpoints ---
@app.get("/progress")
async def get_user_progress(user_id: str = "default_user"):
    """Returns the current progress (score) for a user."""
    user_session = user_sessions.get(user_id)
    if not user_session:
        return {"correct": 0, "total": 0, "accuracy": 0.0, "message": "Start practicing to see your progress!"}

    correct = user_session["score"]["correct"]
    total = user_session["score"]["total"]
    
    accuracy = (correct / total) * 100 if total > 0 else 0.0
    
    return {
        "correct": correct,
        "total": total,
        "accuracy": f"{accuracy:.1f}%"
    }

# --- CONCEPT EXPLAINER Endpoints ---
@app.post("/explain_concept")
async def explain_concept_endpoint(topic: dict, user_id: str = "default_user"):
    """Generates an explanation for a given topic."""
    concept_topic = topic.get("topic")
    if not concept_topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    explanation = concept_explainer_instance.explain_concept(concept_topic)

    user_session = user_sessions.get(user_id)
    if not user_session:
        user_session = user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}
    
    # Add to chat history
    user_session["chat_history"].extend([
        {"role": "user", "content": f"Explain: {concept_topic}"},
        {"role": "assistant", "content": explanation}
    ])
    
    return {"explanation": explanation}

@app.get("/chat_history")
async def get_chat_history(user_id: str = "default_user"):
    """Returns the chat history for a user."""
    user_session = user_sessions.get(user_id)
    if not user_session:
        return []
    return user_session["chat_history"]

# Example of an endpoint that might use nvidia_chat (not directly in original code)
@app.post("/chat")
async def chat_with_nvidia(message: dict, user_id: str = "default_user"):
    """Sends a message to the Nvidia chat model and returns a response."""
    user_message = message.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    user_session = user_sessions.get(user_id)
    if not user_session:
        user_session = user_sessions[user_id] = {"score": {"correct": 0, "total": 0}, "chat_history": []}

    user_session["chat_history"].append({"role": "user", "content": user_message})
    
    response = nvidia_chat_instance.nvidia_chat(user_session["chat_history"])
    user_session["chat_history"].append({"role": "assistant", "content": response})
    
    return {"response": response}
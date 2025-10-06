# summary_logic_gemini.py
import os
from dotenv import load_dotenv
import asyncio
import google.generativeai as genai
from typing import List, Dict

load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class InterviewSummarizerGemini:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro') # Using gemini-pro for summarization
        print("Gemini InterviewSummarizer initialized.")

    def summarize_interview(self, transcript: List[Dict], criteria: str) -> str:
        """
        Summarizes the interview transcript based on provided criteria using Gemini.
        This function is designed to be synchronous, to be run in asyncio.to_thread.
        """
        conversation = ""
        for convo in transcript:
            # Gemini expects 'user' and 'model' roles in its chat history format for conversational turns.
            # For a single summarization prompt, we can flatten this.
            role_label = 'Interviewee' if convo['role'] == 'user' else 'Interviewer'
            conversation += f"{role_label}: {convo['content']}\n"
        
        prompt = f"""Given this interview transcript:\n\n{conversation}\n\nPlease perform two tasks:

1.  **Generate a detailed manuscript:** Focus on key points of the interview, including the answers to the questions provided by the interviewer.
2.  **Evaluate and rate each significant interviewee answer:** Use the following criteria for your rating. Assign one of the following ratings: 'Excellent', 'Good', 'Satisfactory', 'Needs Improvement', or 'Poor'. Present your evaluation clearly, referencing specific interviewee responses from the transcript.

Here are the evaluation criteria:\n\n{criteria}
"""
        
        try:
            # Gemini's generate_content is asynchronous if run with client.api.async_generate_content
            # but the direct `model.generate_content` is synchronous in the client library.
            # So, we keep it synchronous here and rely on asyncio.to_thread in main.py.
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error summarizing interview with Gemini: {e}")
            raise # Re-raise for FastAPI to catch
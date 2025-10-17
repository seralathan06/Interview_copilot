import os
import asyncio
from openai import OpenAI # Keep OpenAI as the client for NVIDIA's API

class InterviewLogicNVIDIA:
    def __init__(self, persona: str):
        # Initialize the OpenAI client pointing to NVIDIA's API
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key="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"
        )
        self.model_name = "openai/gpt-oss-20b" # Or "nvidia/nemotron-4-340b-instruct" or other compatible models
        self.persona = persona
        self.history = [] # Stores conversation turns as [{'role': ..., 'content': ...}]
        self.is_done_flag = False # Internal flag to track if the interview is considered finished

        # Inject the persona as a system message for the NVIDIA API
        # The first message in the history will be the system message setting the persona.
        # Then, the first user message will be to "Start the interview...".
        self.history.append({'role': 'system', 'content': f"You are an AI interviewer with the following persona:\n\n{self.persona}\n\nStrictly adhere to this persona for the entire interview. Do not break character."})
        self.history.append({'role': 'user', 'content': "Start the interview by greeting the interviewee and asking the first question based on your persona."})
        
        print("NVIDIA API InterviewLogic initialized.")

    async def _get_streaming_response(self, messages: list) -> str:
        """
        Helper to get a streaming response from the NVIDIA API and reconstruct it.
        """
        full_response_content = []
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=1,
                top_p=1,
                max_tokens=4096,
                stream=True
            )

            for chunk in completion:
                # NVIDIA API might send 'reasoning_content' but often the main response is in 'content'
                reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
                if reasoning:
                    full_response_content.append(reasoning)
                if chunk.choices[0].delta.content is not None:
                    full_response_content.append(chunk.choices[0].delta.content)
            
            return "".join(full_response_content)
        except Exception as e:
            print(f"Error in NVIDIA API call: {e}")
            raise

    async def get_interviewer_response(self, user_text: str) -> str:
        """
        Takes user text, updates history, and gets the interviewer's next response from the NVIDIA API.
        """
        if user_text: # Only add user_text if it's not empty (e.g., for the first turn from the user after the initial prompt)
            self.history.append({'role': 'user', 'content': user_text})
        
        try:
            # The NVIDIA API using the OpenAI client expects messages in the format:
            # [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
            # Our self.history already stores them in this compatible format.
            
            response_text = await self._get_streaming_response(self.history)
            
            self.history.append({'role': 'assistant', 'content': response_text})
            
            return response_text
        except Exception as e:
            print(f"Error getting interviewer response from NVIDIA API: {e}")
            raise # Re-raise for FastAPI to catch

    async def check_if_done(self, last_message: str) -> bool:
        """
        Checks if the conversation should end based on the last message using the NVIDIA API.
        """
        try:
            # Create a separate, short-lived history for this specific check.
            check_messages = [
                {"role": "system", "content": "You are a helpful assistant. Your task is to determine if a statement indicates an explicit intent to end a conversation or conclude an interview. Respond ONLY with 'yes' or 'no'."},
                {"role": "user", "content": f"Given this statement: '{last_message}', does it convey an explicit intent to end the conversation or explicitly conclude the interview? Respond ONLY with 'yes' or 'no' and nothing else."}
            ]
            
            check_completion = self.client.chat.completions.create(
                model=self.model_name, # Use the same model or a different one if preferred for this task
                messages=check_messages,
                temperature=0.1, # Keep temperature low for factual, direct answers
                max_tokens=5, # Limit tokens to get just 'yes' or 'no'
                stream=False # No need to stream for a short answer
            )
            
            decision = check_completion.choices[0].message.content.strip().lower()
            return decision == 'yes'
        except Exception as e:
            print(f"Error checking if done with NVIDIA API: {e}")
            # Default to not done if there's an error
            return False
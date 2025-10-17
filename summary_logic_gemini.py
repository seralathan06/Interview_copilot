import os
import asyncio
from openai import OpenAI
from typing import List, Dict

class ConceptExplainerNVIDIA:
    def __init__(self, model_name: str = "openai/gpt-oss-20b", api_key: str = None):
        if api_key is None:
            api_key = "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"
            if not api_key:
                raise ValueError("NVIDIA API Key not provided and NVAPI_KEY environment variable not set.")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.model_name = model_name
        
        print(f"ConceptExplainerNVIDIA initialized with model: {self.model_name}")

    async def explain_concept(self, concept: str) -> str:
        prompt = f"Explain the concept of '{concept}' in detail, suitable for someone studying for an aptitude test. Provide examples if applicable. Keep the explanation concise yet comprehensive."
        
        messages = [
            {"role": "system", "content": "You are a helpful and knowledgeable assistant, specializing in explaining complex technical and analytical concepts clearly and concisely. Your goal is to provide comprehensive explanations suitable for aptitude test preparation."},
            {"role": "user", "content": prompt}
        ]

        print(f"Calling NVIDIA API for concept explanation on: '{concept}' using '{self.model_name}'...")

        full_explanation_content = []
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.3,
                top_p=0.9,
                max_tokens=1500,
                stream=True
            )

            # --- DEBUGGING START ---
            found_content = False
            for chunk in completion:
                # Print the raw chunk to see what's coming back
                # print(f"Raw chunk: {chunk}") 
                if chunk.choices and chunk.choices[0] and chunk.choices[0].delta.content is not None:
                    full_explanation_content.append(chunk.choices[0].delta.content)
                    found_content = True
            
            if not found_content:
                print(f"DEBUG: No content found in any chunk for concept '{concept}'.")
                # If no content, try fetching non-streaming to see the full error/response structure
                print(f"DEBUG: Attempting non-streaming call for concept '{concept}' for more error details.")
                non_stream_completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3,
                    top_p=0.9,
                    max_tokens=1500,
                    stream=False # Try non-streaming to get potential error messages directly
                )
                if hasattr(non_stream_completion.choices[0].message, 'content') and non_stream_completion.choices[0].message.content:
                     print(f"DEBUG (Non-Stream) Full response content: {non_stream_completion.choices[0].message.content}")
                else:
                     print(f"DEBUG (Non-Stream) No content found. Full completion object: {non_stream_completion}")

            # --- DEBUGGING END ---

            explanation_text = "".join(full_explanation_content).strip()
            print(f"Full Explanation for '{concept}':\n{explanation_text if explanation_text else '[No explanation received]'}\n--------------------------------------------------")
            return explanation_text
        except Exception as e:
            print(f"Error in NVIDIA API call for concept explanation: {e}")
            return f"Failed to get explanation due to API error: {e}"

if __name__ == "__main__":
    async def test_concept_explainer():
        # Make sure your API key is correct here or set as NVAPI_KEY
        explainer = ConceptExplainerNVIDIA(api_key="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") 

        concepts_to_explain = [
            "Probability",
            "Convolutional Neural Networks",
            "The concept of Recursion",
            "Big O Notation",
            "Merge Sort Algorithm"
        ]

        for concept in concepts_to_explain:
            await explainer.explain_concept(concept)

    asyncio.run(test_concept_explainer())
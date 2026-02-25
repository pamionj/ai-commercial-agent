import os
from huggingface_hub import InferenceClient
from .llm_interface import LLMInterface


class HuggingFaceLLM(LLMInterface):

    def __init__(self):
        self.api_token = os.getenv("HF_API_TOKEN")
        self.client = InferenceClient(token=self.api_token)
        self.model = "mistralai/Mistral-7B-Instruct-v0.2"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
      #  raise Exception("Simulated HF failure")
        print(">>> USING HUGGINGFACE LLM <<<")

        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"[HF ERROR] {str(e)}"
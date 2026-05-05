import os
import logging
from huggingface_hub import InferenceClient
from .llm_interface import LLMInterface

logger = logging.getLogger("hf_llm")


class HuggingFaceLLM(LLMInterface):

    def __init__(self):
        self.api_key = os.getenv("HF_API_TOKEN")
        self.model = "google/flan-t5-base"

        self.client = InferenceClient(
            model=self.model,
            token=self.api_key
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        logger.info("Generating response using HuggingFace LLM")

        try:
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )

            content = response.choices[0].message.content

            # 🔴 VALIDACIÓN SIMPLE (CLAVE)
            if not content or not content.strip():
                raise Exception("Empty response from HF")

            return content

        except Exception as e:
            logger.error(f"HuggingFace LLM failed: {str(e)}", exc_info=True)

            # 🔥 IMPORTANTE: lanzar error para que luego podamos hacer fallback
            raise
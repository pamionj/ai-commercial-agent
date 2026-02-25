from abc import ABC, abstractmethod


class LLMInterface(ABC):

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        pass
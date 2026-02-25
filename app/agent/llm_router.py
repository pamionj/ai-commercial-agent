import os
import logging
from typing import List, Dict
from app.agent.llm_interface import LLMInterface

logger = logging.getLogger("llm_router")


class LLMRouter(LLMInterface):
    """
    Router con:
    - Retry por provider
    - Fallback automático
    - Métricas simples
    - Orden configurable vía .env
    """

    def __init__(self, providers: Dict[str, LLMInterface]):

        self.providers = providers

        # Leer orden desde .env
        order_env = os.getenv("LLM_ORDER", "hf,mock")
        self.order = [p.strip() for p in order_env.split(",")]

        # Leer número de retries
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "2"))

        # Métricas simples
        self.stats = {name: 0 for name in providers.keys()}

        logger.info(f"LLM order configured: {self.order}")
        logger.info(f"Max retries per provider: {self.max_retries}")

    def generate(self, system_prompt: str, user_prompt: str) -> str:

        last_exception = None

        for provider_name in self.order:

            provider = self.providers.get(provider_name)

            if not provider:
                logger.warning(f"Provider '{provider_name}' not found. Skipping.")
                continue

            for attempt in range(1, self.max_retries + 1):
                try:
                    logger.info(
                        f"Trying provider: {provider_name} | Attempt {attempt}"
                    )

                    result = provider.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt
                    )

                    self.stats[provider_name] += 1

                    logger.info(f"Success with provider: {provider_name}")
                    return result

                except Exception as e:
                    logger.error(
                        f"Failure in {provider_name} | Attempt {attempt} | {str(e)}"
                    )
                    last_exception = e

            logger.warning(
                f"Provider {provider_name} exhausted retries. Moving to next."
            )

        raise Exception(f"All providers failed. Last error: {str(last_exception)}")

    def get_stats(self):
        return self.stats
from typing import Type, TypeVar
from pydantic import BaseModel
from gigachat import GigaChat
import time
from extractors.base import BaseExtractor
from config import settings 

T = TypeVar("T", bound=BaseModel)

class LLMExtractor(BaseExtractor):
    def __init__(self, credentials: str, model_name: str = None):
        self.client = GigaChat(
            credentials=settings.gigachat_credentials,
            model=settings.gigachat_model,
            verify_ssl_certs=False
        )

    def extract(self, text: str, schema: Type[T], max_retries: int = 3) -> T:
        system_prompt = (
            f"Ты — экспертный парсер резюме. Внимательно извлеки данные из текста в предложенную схему:\n{text}\n\n"
            "Инструкции:\n"
            "- Извлеки ВСЕ ключевые навыки, технологии и инструменты в поле 'skills'.\n"
            "- Извлеки ВСЕ места работы из опыта в 'experiences'.\n"
            "- Иностранные языки указывай в поле 'languages'.\n"
            "- Для отсутствующих контактов возвращай null."
        )
        for attempt in range(max_retries):
            try:
                _, parsed = self.client.chat.parse(
                    system_prompt,
                    response_format=schema 
                    )
                return parsed
            except Exception as e:
                if attempt < max_retries-1:
                    print(f"[Retry {attempt + 1}/{max_retries}] Ошибка: {e}")
                    time.sleep(1)
                else:
                    raise

        
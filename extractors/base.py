from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, text: str, schema: Type[T]) -> T:
        """
        Принимает сырой текст и класс Pydantic-схемы.
        Возвращает заполненный объект этой схемы.
        """
        pass

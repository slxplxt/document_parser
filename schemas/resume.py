from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
import re
from datetime import datetime


MONTH_MAP = {
    "январь": "01", "янв": "01",
    "февраль": "02", "фев": "02",
    "март": "03", "мар": "03",
    "апрель": "04", "апр": "04",
    "май": "05",
    "июнь": "06", "июн": "06",
    "июль": "07", "июл": "07",
    "август": "08", "авг": "08",
    "сентябрь": "09", "сен": "09", "сент": "09",
    "октябрь": "10", "окт": "10",
    "ноябрь": "11", "ноя": "11",
    "декабрь": "12", "дек": "12",
}

def parse_to_iso_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str or str(date_str).lower().strip() in ["null", "none", ""]:
        return None

    val = str(date_str).lower().strip()

    if re.match(r"^\d{4}-\d{2}$", val):
        return val

    year_match = re.search(r"\b(19|20)\d{2}\b", val)
    if year_match:
        year = year_match.group(0)
        for month_name, month_num in MONTH_MAP.items():
            if month_name in val:
                return f"{year}-{month_num}"
        return f"{year}-01"
    return val


def calculate_month_difference(start_str: str, end_str: Optional[str], is_current: bool)->int:
    if not start_str:
        return 0

    try:
        start_date = datetime.strptime(start_str, "%Y-%m")
        if is_current or not end_str:
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_str, "%Y-%m")

        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        return max(0, months)
    except ValueError:
        return 0



def pluralize(number: int, one: str, two: str, five: str) -> str:
    n = abs(number) % 100
    if 11 <= n <= 19:
        form = five
    else:
        n = n % 10
        if n == 1:
            form = one
        elif 2 <= n <= 4:
            form = two
        else:
            form = five
    return f"{number} {form}"

def format_experience(total_months: int) -> str:
    if total_months <= 0:
        return "Без опыта"
        
    years = total_months // 12
    months = total_months % 12
    
    parts = []
    if years > 0:
        parts.append(pluralize(years, "год", "года", "лет"))
    if months > 0:
        parts.append(pluralize(months, "месяц", "месяца", "месяцев"))
        
    return " и ".join(parts)


class Experience(BaseModel):
    company: str = Field(description="Название компании")
    position: str = Field(description="Занимаемая должность") 
    start_date: Optional[str] = Field(None, description="Дата начала в формате YYYY-MM или YYYY")
    end_date: Optional[str] = Field(None, description="Дата окончания в формате YYYY-MM или YYYY")
    is_current_job: bool = Field(False, description="Работает ли по настояещее время")
    start_grade: Optional[str] = Field(None, description="Профессиональный уровень в начале работы (Junior, Middle, Senior)")# Для отслеживания прогресса на посту
    end_grade: Optional[str] = Field(None, description="Профессиональный уровень в конце работы (Junior, Middle, Senior)")
    description: str = Field(description="Краткое описание обязанностей")

    @model_validator(mode="before")
    @classmethod
    def process_dates(cls, data: dict)-> dict:
        if isinstance(data, dict):
            raw_end = str(data.get("end_date", "")).lower().strip()

            if any(term in raw_end for term in ["настоящее", "н.в", "present", "current"]):
                data["end_date"] = None
                data["is_current_job"] = True
            else:
                data["end_date"] = parse_to_iso_date(data.get("end_date"))
                data["is_current_job"] = False
            data["start_date"] = parse_to_iso_date(data.get("start_date"))
        return data
    
class Education(BaseModel):
    institution: str = Field(description="Учебное заведение")
    degree: Optional[str] = Field(None, description="Степень")
    specialization: Optional[str] = Field(None, description="Направление обучения")
    

class ResumeSchema(BaseModel):
    full_name: str = Field(description="ФИО кандидата")
    age: int = Field(ge=18, le=40, description="Возраст")
    email: EmailStr = Field(description="Адрес электронной почты")
    phone: Optional[str] = Field(None, description="Номер телефона")
    tg: Optional[str] = Field(None, description="Id телеграм") # для связи, кроме телефона
    skills: List[str] = Field(default_factory=list, description="Список всех ключевых навыков и технологий из резюме (например: ['Python', 'Git', 'Docker'])")
    languages: List[str] = Field(default_factory=list, description="Иностранные языки и уровень владения (например: ['Английский — B1'])")
    experiences: List[Experience] = Field(default_factory=list, description="История работы")
    total_experience_months: int = Field(0, description="Общий стаж работы в месяцах")
    total_experience_formatted: str = Field("", description="Стаж в формате '6 лет и 1 месяц'")
    education: list[Education] = Field(default_factory=list, description="Образование")

    
    @field_validator("phone", mode="before")
    @classmethod
    def clean_phone(cls, value: Optional[str]) -> Optional[str]:
        if not value or str(value).strip().lower() in ["null", "none", ""]:
            return None
        
        cleaned = re.sub(r"\D", "", str(value))
        if len(cleaned) == 11 and cleaned.startswith("8"):
            cleaned = "7" + cleaned[1:]
        return cleaned if cleaned else None

    
    @field_validator("tg", mode="before")
    @classmethod
    def clean_tg(cls, value: Optional[str]) -> Optional[str]:
        if not value or value.strip().lower() in ["null", "none", ""]:
            return None

        val = str(value).strip()
        if val.startswith("@"):
            val = val[1:]

        return val if val else None

    
    @model_validator(mode="after")
    def calculate_total_expirience(self) -> "ResumeSchema":
        total = 0
        for exp in self.experiences:
            total += calculate_month_difference(
                start_str=exp.start_date,
                end_str=exp.end_date,
                is_current=exp.is_current_job
            )
        self.total_experience_months = total
        self.total_experience_formatted = format_experience(total)
        return self

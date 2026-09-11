import pytest
from schemas.resume import ResumeSchema, Experience, Education

def test_resume_schema_cleaning_and_experience_calculation():
    """Тестируем автоматическую очистку контактов, дат и расчет стажа."""
    
    
    raw_data = {
        "full_name": "Тестов Тест Тестович",
        "age": 30,
        "email": "test@example.com",
        "phone": "+7 (999) 123-45-67", 
        "tg": "@test_user",              
        "skills": ["Python", "Pydantic"],
        "languages": ["Русский"],
        "experiences": [
            {
                "company": "Компания А",
                "position": "Developer",
                "start_date": "март 2022",       # Ожидаем "2022-03"
                "end_date": "настоящее время", # Ожидаем None + is_current_job=True
                "description": "Разработка"
            },
            {
                "company": "Компания Б",
                "position": "Junior Developer",
                "start_date": "сентябрь 2020",   # Ожидаем "2020-09"
                "end_date": "февраль 2022",      # Ожидаем "2022-02"
                "description": "Поддержка"
            }
        ],
        "education": []
    }

    
    resume = ResumeSchema(**raw_data)

    # 1. Проверяем очистку контактов
    assert resume.phone == "79991234567"
    assert resume.tg == "test_user"

    # 2. Проверяем нормализацию дат первого места работы
    exp1 = resume.experiences[0]
    assert exp1.start_date == "2022-03"
    assert exp1.end_date is None
    assert exp1.is_current_job is True

    # 3. Проверяем нормализацию дат второго места работы
    exp2 = resume.experiences[1]
    assert exp2.start_date == "2020-09"
    assert exp2.end_date == "2022-02"
    assert exp2.is_current_job is False

    # 4. Проверяем расчет стажа
    assert resume.total_experience_months > 0
    assert "лет" in resume.total_experience_formatted or "год" in resume.total_experience_formatted


def test_empty_contacts_handling():
    """Тестируем корректную обработку пустых/мусорных контактов."""
    raw_data = {
        "full_name": "Иванов Иван",
        "age": 25,
        "email": "ivan@example.com",
        "phone": "null",
        "tg": "none",
        "experiences": [],
        "education": []
    }

    resume = ResumeSchema(**raw_data)

    assert resume.phone is None
    assert resume.tg is None
    assert resume.total_experience_months == 0
    assert resume.total_experience_formatted == "Без опыта"
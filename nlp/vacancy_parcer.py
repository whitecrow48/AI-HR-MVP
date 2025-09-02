# nlp/vacancy_parcer.py

import re
from typing import Dict, List

def _norm_str(s: str) -> str:
    """Нормализуем строку: убирает лишние пробелы и переводит None в пустую строку."""
    return re.sub(r"\s+", " ", (s or "").strip())

def _norm_list(lst: List[str]) -> List[str]:
    """Нормализуем список строк, удаляя пустые и None значения."""
    return [_norm_str(x) for x in lst if isinstance(x, str) and x.strip()]

def parse_vacancy(vacancy: Dict) -> Dict:
    """
    Нормализуем словарь вакансии в предсказуемую структуру.
    Добавляем подготовленные текстовые поля для быстрого поиска и анализа.
    """
    if not isinstance(vacancy, dict):
        raise ValueError("vacancy must be a dict")

    parsed = {
        "id": vacancy.get("id"),
        "title": _norm_str(vacancy.get("title", "")),
        "city": _norm_str(vacancy.get("city", "")),
        "address": _norm_str(vacancy.get("address", "")),
        "employment_type": _norm_str(vacancy.get("employment_type", "")),
        "work_schedule": _norm_str(vacancy.get("work_schedule", "")),
        "experience": _norm_str(vacancy.get("experience", "")),
        "education_level": _norm_str(vacancy.get("education_level", "")),
        "requirements": _norm_list(vacancy.get("requirements", [])),
        "responsibilities": _norm_list(vacancy.get("responsibilities", [])),
        "raw": vacancy
    }

    # предобработка текста вакансии для быстрого сопоставления с резюме
    parsed["requirements_text"] = " ; ".join(parsed["requirements"]).lower()
    parsed["responsibilities_text"] = " ; ".join(parsed["responsibilities"]).lower()
    parsed["experience_text"] = parsed["experience"].lower()
    parsed["education_text"] = parsed["education_level"].lower()

    # объединяем все текстовые поля в одно для удобного поиска / NLP
    parsed["all_text"] = " ; ".join([
        parsed["title"],
        parsed["city"],
        parsed["address"],
        parsed["employment_type"],
        parsed["work_schedule"],
        parsed["experience"],
        parsed["education_level"],
        *parsed["requirements"],
        *parsed["responsibilities"]
    ]).lower()

    return parsed

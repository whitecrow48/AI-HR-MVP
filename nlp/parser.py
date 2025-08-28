# nlp/parser.py

def parse_resume(file_path, vacancy_skills=None):
    """
    Заглушка парсинга резюме.
    Возвращает фиктивные навыки и опыт.
    """
    # vacancy_skills можно использовать для генерации "совпадений", пока просто игнорируем
    return {
        "skills": ["Python", "SQL", "Аналитика данных"],
        "experience": ["Компания А", "Компания Б"]
    }

# nlp/analyzer.py

def analyze_resume_vs_vacancy(parsed_resume, vacancy):
    """
    Заглушка анализа соответствия резюме вакансии.
    Возвращает фиктивные оценки.
    """
    return {
        "hard_score": 80,    # соответствие hard skills
        "soft_score": 70,    # коммуникационные навыки
        "cases_score": 60,   # кейсы / опыт
        "total_score": 75,   # итоговое соответствие
        "red_flags": []      # отсутствующие ключевые навыки
    }

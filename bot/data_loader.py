import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESUMES_DIR = os.path.join(DATA_DIR, "resumes")
VACANCIES_DIR = os.path.join(DATA_DIR, "vacancies")

os.makedirs(RESUMES_DIR, exist_ok=True)

VACANCIES_FILE = os.path.join(VACANCIES_DIR, "vacancies.json")

def load_vacancies():
    """Загрузка всех вакансий из файла JSON"""
    if not os.path.exists(VACANCIES_FILE):
        raise FileNotFoundError(f"Файл вакансий не найден: {VACANCIES_FILE}")
    with open(VACANCIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_vacancy_by_id(vac_id):
    """Возвращает словарь вакансии по её id или None"""
    vacancies = load_vacancies()
    return next((v for v in vacancies if v["id"] == vac_id), None)

# data_loader.py

import json
import os
from logs.logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RESUMES_DIR = os.path.join(DATA_DIR, "resumes")
VACANCIES_DIR = os.path.join(DATA_DIR, "vacancies")

os.makedirs(RESUMES_DIR, exist_ok=True)

VACANCIES_FILE = os.path.join(VACANCIES_DIR, "vacancies.json")


class VacancyManager:
    """Менеджер для работы с вакансиями"""

    def __init__(self, vacancies_file=VACANCIES_FILE):
        self.vacancies_file = vacancies_file
        self._vacancies_cache = None  # Кэш для ускорения повторного доступа
        logger.info(f"VacancyManager инициализирован с файлом: {self.vacancies_file}")

    def load_vacancies(self):
        """Загрузка всех вакансий из файла JSON"""
        if self._vacancies_cache is None:
            if not os.path.exists(self.vacancies_file):
                logger.error(f"Файл вакансий не найден: {self.vacancies_file}")
                raise FileNotFoundError(f"Файл вакансий не найден: {self.vacancies_file}")
            try:
                with open(self.vacancies_file, "r", encoding="utf-8") as f:
                    self._vacancies_cache = json.load(f)
                logger.info(f"Вакансии загружены из {self.vacancies_file}, всего {len(self._vacancies_cache)} вакансий")
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при разборе JSON файла {self.vacancies_file}: {e}", exc_info=True)
                raise
        return self._vacancies_cache

    def get_vacancy_by_id(self, vac_id):
        """Возвращает словарь вакансии по её id или None"""
        vacancies = self.load_vacancies()
        vac = next((v for v in vacancies if v["id"] == vac_id), None)
        if vac:
            logger.info(f"Найдена вакансия ID={vac_id}: {vac['title']}")
        else:
            logger.warning(f"Вакансия с ID={vac_id} не найдена")
        return vac

    def refresh_cache(self):
        """Сбрасывает кэш и перезагружает вакансии из файла"""
        self._vacancies_cache = None
        logger.info("Кэш вакансий сброшен, выполняется перезагрузка")
        return self.load_vacancies()

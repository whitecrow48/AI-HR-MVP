# resume_handlers.py

import os
import time
from bot.data_loader import RESUMES_DIR, VacancyManager
from logs.logger import logger

from nlp.analyzer import analyze_resume_vs_vacancy
from nlp.parser_resume import parse_resume
from nlp.vacancy_parcer import parse_vacancy

# экземпляр менеджера вакансий
vacancy_manager = VacancyManager()

# Убедимся, что папка для резюме существует
os.makedirs(RESUMES_DIR, exist_ok=True)


async def handle_resume(update, context):
    """
    Обработчик загрузки резюме пользователем.
    Сохраняет файл, запускает парсер и анализ соответствия вакансии,
    формирует и отправляет пользователю текстовый ответ.
    """
    message = update.message

    try:
        # Проверка, что отправлен документ
        if not message or not message.document:
            await message.reply_text("Пожалуйста, отправьте файл резюме в формате PDF, DOCX или RTF.")
            logger.warning(f"Пользователь {getattr(message.from_user, 'id', 'unknown')} отправил не документ.")
            return

        file_name = message.document.file_name or "resume"
        if not file_name.lower().endswith((".pdf", ".docx", ".rtf")):
            await message.reply_text("Неверный формат. Поддерживаются PDF, DOCX или RTF.")
            logger.warning(f"Пользователь {message.from_user.id} отправил неподдерживаемый формат: {file_name}")
            return

        user_id = message.from_user.id
        username = message.from_user.username or "user"
        vacancy_id = context.user_data.get("selected_vacancy_id")
        if not vacancy_id:
            await message.reply_text("⚠ Вакансия не выбрана. Сначала выберите вакансию.")
            logger.warning(f"Пользователь {user_id} попытался загрузить резюме без выбора вакансии.")
            return

        # Сохранение файла
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        safe_file_name = file_name.replace(" ", "_")
        unique_name = f"{user_id}_{username}_{vacancy_id}_{timestamp}_{safe_file_name}"
        file_path = os.path.join(RESUMES_DIR, unique_name)

        file = await message.document.get_file()
        await file.download_to_drive(file_path)
        logger.info(f"Пользователь {user_id} загрузил резюме: {file_name} -> {unique_name}")

        await message.reply_text("📂 Резюме успешно загружено. Идёт анализ... ⏳")

        # Получаем вакансию через VacancyManager
        vac = vacancy_manager.get_vacancy_by_id(vacancy_id)
        if not vac:
            await message.reply_text("⚠ Вакансия не найдена.")
            logger.error(f"Вакансия {vacancy_id} не найдена для пользователя {user_id}.")
            return

        vacancy_skills = vac.get("requirements", [])
        normalized_vacancy = parse_vacancy(vac)

        # Парсинг резюме — передаём vacancy_id и vacancy_manager
        parsed_data = parse_resume(file_path, vacancy_skills)
        logger.info(f"Parsed resume data for user {user_id}: {parsed_data}")

        # Анализ соответствия вакансии
        analysis = analyze_resume_vs_vacancy(parsed_data, normalized_vacancy)
        logger.info(f"Analysis results for user {user_id}, vacancy {vac.get('id')}: {analysis}")

        # --- Подготовка вывода по навыкам/опыту ---
        # Навыки: парсер может вернуть dict {"must_have", "nice_to_have", "not_found"}
        skills_field = parsed_data.get("skills", [])
        skills_list = []
        if isinstance(skills_field, dict):
            must = skills_field.get("must_have", []) or []
            nice = skills_field.get("nice_to_have", []) or []
            # представление для пользователя — сначала must, потом nice
            skills_list = must + nice
        elif isinstance(skills_field, list):
            skills_list = skills_field
        else:
            # на случай неожиданных типов
            skills_list = []

        # Опыт
        experience = parsed_data.get("experience", [])
        if not isinstance(experience, list):
            experience = [str(experience)] if experience else []

        # Берём метрики анализа, защищаясь от KeyError
        hard_score = analysis.get("hard_score", 0) if isinstance(analysis, dict) else 0
        soft_score = analysis.get("soft_score", 0) if isinstance(analysis, dict) else 0
        cases_score = analysis.get("cases_score", 0) if isinstance(analysis, dict) else 0
        total_score = analysis.get("total_score", 0) if isinstance(analysis, dict) else 0
        red_flags = analysis.get("red_flags", []) if isinstance(analysis, dict) else []

        # Формируем текстовый ответ
        response_text = (
            f"✅ Резюме обработано!\n\n"
            f"📌 Навыки: {', '.join(skills_list) if skills_list else 'не обнаружено'}\n"
            f"💼 Опыт: {', '.join(experience) if experience else 'не обнаружено'}\n\n"
            f"📊 Соответствие вакансии «{vac.get('title', '—')}»:\n"
            f"- Hard skills: {hard_score}%\n"
            f"- Communication: {soft_score}%\n"
            f"- Cases: {cases_score}%\n"
            f"➡ Итог: {total_score}%\n\n"
        )

        if red_flags:
            # red_flags ожидается как список ключевых отсутствующих навыков
            response_text += f"⚠ Не хватает ключевых навыков: {', '.join(red_flags)}\n\n"

        if total_score >= 60:
            response_text += "✅ Кандидат проходит на следующий этап! Предлагаю пройти голосовое интервью."
        else:
            response_text += "❌ К сожалению, резюме не соответствует требованиям вакансии."

        await message.reply_text(response_text)

    except Exception as e:
        user_id = getattr(message.from_user, "id", "unknown")
        logger.error(f"Ошибка при обработке резюме пользователя {user_id}: {e}", exc_info=True)
        try:
            await message.reply_text("Произошла ошибка при обработке резюме. Попробуйте снова.")
        except Exception:
            # в редком случае ответить невозможно — просто логируем
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю {user_id}", exc_info=True)

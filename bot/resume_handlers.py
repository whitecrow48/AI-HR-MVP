# resume_handlers.py

import os
import time
from bot.data_loader import RESUMES_DIR
from logs.logger import logger
from nlp.parser import parse_resume
from nlp.analyzer import analyze_resume_vs_vacancy
from bot.data_loader import VacancyManager

vacancy_manager = VacancyManager()

async def handle_resume(update, context):
    message = update.message

    try:
        # Проверка, что отправлен документ
        if not message.document:
            await message.reply_text("Пожалуйста, отправьте файл резюме в формате PDF, DOCX или RTF.")
            logger.warning(f"Пользователь {message.from_user.id} отправил не документ.")
            return

        file_name = message.document.file_name
        if not file_name.lower().endswith((".pdf", ".docx", ".rtf")):
            await message.reply_text("Неверный формат. Поддерживаются PDF, DOCX или RTF.")
            logger.warning(f"Пользователь {message.from_user.id} отправил файл с неподдерживаемым форматом: {file_name}")
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

        # Парсинг резюме
        parsed_data = parse_resume(file_path, vacancy_skills)
        logger.info(f"Parsed resume data for user {user_id}: {parsed_data}")

        # Анализ соответствия вакансии
        analysis = analyze_resume_vs_vacancy(parsed_data, vac)
        logger.info(f"Analysis results for user {user_id}, vacancy {vac['id']}: {analysis}")

        # Формируем текстовый ответ
        skills = parsed_data.get("skills", [])
        experience = parsed_data.get("experience", [])
        hard_score = analysis["hard_score"]
        soft_score = analysis["soft_score"]
        cases_score = analysis["cases_score"]
        total_score = analysis["total_score"]
        red_flags = analysis["red_flags"]

        response_text = (
            f"✅ Резюме обработано!\n\n"
            f"📌 Навыки: {', '.join(skills) if skills else 'не обнаружено'}\n"
            f"💼 Опыт: {', '.join(experience) if experience else 'не обнаружено'}\n\n"
            f"📊 Соответствие вакансии «{vac['title']}»:\n"
            f"- Hard skills: {hard_score}%\n"
            f"- Communication: {soft_score}%\n"
            f"- Cases: {cases_score}%\n"
            f"➡ Итог: {total_score}%\n\n"
        )

        if red_flags:
            response_text += f"⚠ Не хватает ключевых навыков: {', '.join(red_flags)}\n\n"

        if total_score >= 60:
            response_text += "✅ Кандидат проходит на следующий этап! Предлагаю пройти голосовое интервью."
        else:
            response_text += "❌ К сожалению, резюме не соответствует требованиям вакансии."

        await message.reply_text(response_text)

    except Exception as e:
        logger.error(f"Ошибка при обработке резюме пользователя {message.from_user.id}: {e}", exc_info=True)
        await message.reply_text("Произошла ошибка при обработке резюме. Попробуйте снова.")

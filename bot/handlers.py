# handlers.py
import time

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import ContextTypes

import os
from bot.data_loader import RESUMES_DIR, get_vacancy_by_id, load_vacancies
from nlp.parser import parse_resume
from nlp.analyzer import analyze_resume_vs_vacancy

# -------------------- Меню --------------------
async def start_menu(update, context):
    """Приветствие при первом запуске"""
    await update.message.reply_text(
        "Привет! Это AI HR Bot.\n"
        "Я помогу вам пройти процесс собеседования и анализа резюме.\n\n"
    )
    await show_main_menu(update, context)


async def show_main_menu(update, context):
    """Показывает главное меню без приветственного текста"""
    keyboard = [
        [KeyboardButton("Пройти интервью"), KeyboardButton("Список вакансий")],
        [KeyboardButton("Помощь"), KeyboardButton("О боте")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    if update.message:
        await update.message.reply_text("Выберите действие из меню:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.message.edit_text("Выберите действие из меню:", reply_markup=None)


async def back_to_menu(update, context):
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)

async def back_handler(update, context):
    """Обработчик кнопок 'Назад'"""
    query = update.callback_query
    await query.answer()

    if query.data == "back_to_list":
        from bot.utils import list_vacancies
        vacancies = load_vacancies()
        await list_vacancies(update, context, vacancies)
    elif query.data == "back_to_choose":
        await choose_vacancy(update, context)



# -------------------- Вакансии --------------------
async def choose_vacancy(update, context):
    """Показывает список вакансий кнопками (инлайн)"""
    vacancies = get_all_vacancies()
    keyboard = [[InlineKeyboardButton(v["title"], callback_data=f"select_{v['id']}")] for v in vacancies]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Выберите вакансию:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.message.edit_text("Выберите вакансию:", reply_markup=reply_markup)


async def vacancy_selected(update, context):
    """После выбора вакансии предлагает загрузить резюме"""
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("select_"):
        return

    vac_id = int(query.data.replace("select_", ""))
    context.user_data["selected_vacancy_id"] = vac_id

    vac = get_vacancy_by_id(vac_id)
    if not vac:
        await query.message.reply_text("⚠ Вакансия не найдена.")
        return

    text = (
        f"Вы выбрали вакансию: {vac['title']}\n"
        f"Город: {vac['city']}\n\n"
        f"Теперь загрузите своё резюме (PDF, DOCX или RTF)."
    )
    keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_choose")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)


# -------------------- Резюме --------------------
async def handle_resume(update, context):
    message = update.message

    if not message.document:
        await message.reply_text("Пожалуйста, отправьте файл резюме в формате PDF, DOCX или RTF.")
        return

    file_name = message.document.file_name
    if not file_name.lower().endswith((".pdf", ".docx", ".rtf")):
        await message.reply_text("Неверный формат. Поддерживаются PDF, DOCX или RTF.")
        return

    # Получаем информацию о пользователе и выбранной вакансии
    user_id = message.from_user.id
    username = message.from_user.username or "user"
    vacancy_id = context.user_data.get("selected_vacancy_id", 0)

    # Формируем читаемую дату/время
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    # Формируем уникальное имя файла
    safe_file_name = file_name.replace(" ", "_")  # убираем пробелы
    unique_name = f"{user_id}_{username}_{vacancy_id}_{timestamp}_{safe_file_name}"
    file_path = os.path.join(RESUMES_DIR, unique_name)

    # Скачиваем файл
    file = await message.document.get_file()
    await file.download_to_drive(file_path)

    await message.reply_text("📂 Резюме успешно загружено. Идёт анализ... ⏳")

    # Получаем выбранную вакансию
    vac = get_vacancy_by_id(vacancy_id)
    if not vac:
        await message.reply_text("⚠ Вакансия не найдена.")
        return

    # --- Заглушка для парсинга и анализа ---
    from nlp.parser import parse_resume
    from nlp.analyzer import analyze_resume_vs_vacancy

    vacancy_skills = vac.get("requirements", [])
    parsed_data = parse_resume(file_path, vacancy_skills)
    analysis = analyze_resume_vs_vacancy(parsed_data, vac)

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



# -------------------- Вспомогательные функции --------------------
def get_all_vacancies():
    """Возвращает список всех вакансий"""
    from bot.data_loader import load_vacancies
    return load_vacancies()

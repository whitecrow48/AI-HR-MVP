from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.data_loader import load_vacancies


# -------------------- Список вакансий --------------------
async def list_vacancies(update, context, vacancies):
    """Отправляет список вакансий кнопками (инлайн-клавиатура)"""
    keyboard = [[InlineKeyboardButton(v["title"], callback_data=f"vac_{v['id']}")] for v in vacancies]

    # Добавляем кнопку "Назад в меню"
    keyboard.append([InlineKeyboardButton("⬅ Назад в меню", callback_data="back_to_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Список вакансий:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.message.edit_text("Список вакансий:", reply_markup=reply_markup)


# -------------------- Детали вакансии --------------------
async def show_vacancy_details(update, context):
    query = update.callback_query
    await query.answer()

    vac_id = query.data.replace("vac_", "").split("_")[0]

    # Получаем актуальный список вакансий
    vacancies = load_vacancies()
    vac = next((v for v in vacancies if str(v["id"]) == vac_id), None)

    if vac:
        text = (
            f"🏢 Вакансия: {vac['title']}\n"
            f"📍 Город: {vac['city']}\n"
            f"📄 Обязанности: {', '.join(vac.get('responsibilities', []))}\n"
            f"📝 Требования: {', '.join(vac.get('requirements', []))}\n"
            f"💼 Тип занятости: {vac.get('employment_type', 'не указано')}\n"
        )
        # кнопка "Назад" возвращает к списку вакансий
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_list")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

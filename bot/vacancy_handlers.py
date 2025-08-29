# vacancy_handlers.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from bot.data_loader import VacancyManager
from bot.utils import list_vacancies
from logs.logger import logger

# экземпляр менеджера вакансий
vacancy_manager = VacancyManager()



# -------------------- Вакансии --------------------
async def choose_vacancy(update, context):
    """Показывает список вакансий кнопками (инлайн)"""
    try:
        vacancies = vacancy_manager.load_vacancies()
        logger.info(f"Пользователь {update.effective_user.id} запросил список вакансий. Всего вакансий: {len(vacancies)}")

        keyboard = [[InlineKeyboardButton(v["title"], callback_data=f"select_{v['id']}")] for v in vacancies]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.message:
            await update.message.reply_text("Выберите вакансию:", reply_markup=reply_markup)
            logger.info(f"Список вакансий отправлен пользователю {update.effective_user.id}")
        elif update.callback_query:
            query = update.callback_query
            await query.message.edit_text("Выберите вакансию:", reply_markup=reply_markup)
            logger.info(f"Список вакансий обновлён пользователю {query.from_user.id} через callback")

    except Exception as e:
        user_id = update.effective_user.id if update.effective_user else "неизвестен"
        logger.error(f"Ошибка при показе списка вакансий пользователю {user_id}: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text("Произошла ошибка при загрузке списка вакансий. Попробуйте снова.")
        elif update.callback_query:
            await update.callback_query.message.reply_text("Произошла ошибка при загрузке списка вакансий. Попробуйте снова.")


async def vacancy_selected(update, context):
    """После выбора вакансии предлагает загрузить резюме"""
    query = update.callback_query
    await query.answer()

    try:
        if not query.data.startswith("select_"):
            logger.warning(f"Пользователь {query.from_user.id} отправил некорректный callback: {query.data}")
            return

        vac_id = int(query.data.replace("select_", ""))
        context.user_data["selected_vacancy_id"] = vac_id
        logger.info(f"Пользователь {query.from_user.id} выбрал вакансию ID={vac_id}")

        vac = vacancy_manager.get_vacancy_by_id(vac_id)
        if not vac:
            await query.message.reply_text("⚠ Вакансия не найдена.")
            logger.warning(f"Вакансия ID={vac_id} не найдена для пользователя {query.from_user.id}")
            return

        text = (
            f"Вы выбрали вакансию: {vac['title']}\n"
            f"Город: {vac['city']}\n\n"
            f"Теперь загрузите своё резюме (PDF, DOCX или RTF)."
        )
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_choose")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Ошибка при обработке выбора вакансии пользователем {query.from_user.id}: {e}", exc_info=True)
        await query.message.reply_text("Произошла ошибка при выборе вакансии. Попробуйте снова.")


async def show_vacancy_details(update, context):
    """Просмотр деталей вакансии"""
    query = update.callback_query
    await query.answer()

    try:
        vac_id = query.data.replace("vac_", "").split("_")[0]
        vac = vacancy_manager.get_vacancy_by_id(int(vac_id))

        if vac:
            logger.info(f"Пользователь {query.from_user.id} просматривает детали вакансии ID={vac_id}")
            text = (
                f"🏢 Вакансия: {vac['title']}\n"
                f"📍 Город: {vac['city']}\n"
                f"📄 Обязанности: {', '.join(vac.get('responsibilities', []))}\n"
                f"📝 Требования: {', '.join(vac.get('requirements', []))}\n"
                f"💼 Тип занятости: {vac.get('employment_type', 'не указано')}\n"
            )
            keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_list")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            logger.warning(f"Пользователь {query.from_user.id} запросил несуществующую вакансию ID={vac_id}")
            await query.message.reply_text("⚠ Вакансия не найдена.")

    except Exception as e:
        logger.error(f"Ошибка при просмотре вакансии пользователем {query.from_user.id}: {e}", exc_info=True)
        await query.message.reply_text("Произошла ошибка при отображении вакансии. Попробуйте снова.")




async def back_handler(update, context):
    """Обработчик кнопок 'Назад' для вакансий"""
    query = update.callback_query
    await query.answer()

    try:
        user_id = query.from_user.id

        if query.data == "back_to_list":
            logger.info(f"Пользователь {user_id} нажал 'Назад' к списку вакансий")
            vacancies = vacancy_manager.load_vacancies()
            await list_vacancies(update, context, vacancies)

        elif query.data == "back_to_choose":
            logger.info(f"Пользователь {user_id} нажал 'Назад' к выбору вакансии")
            await choose_vacancy(update, context)

        else:
            logger.warning(f"Пользователь {user_id} нажал неизвестную кнопку 'Назад': {query.data}")

    except Exception as e:
        logger.error(f"Ошибка в back_handler для пользователя {query.from_user.id}: {e}", exc_info=True)
        await query.message.reply_text("Произошла ошибка при обработке кнопки 'Назад'. Попробуйте снова.")

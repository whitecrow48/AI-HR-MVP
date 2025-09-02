# menu_handlers.py

from telegram import ReplyKeyboardMarkup, KeyboardButton

from bot.utils import list_vacancies
from bot.vacancy_handlers import choose_vacancy
from bot.data_loader import VacancyManager
from logs.logger import logger

# экземпляр VacancyManager
vacancy_manager = VacancyManager()


async def start_menu(update, context):
    """Приветствие при первом запуске"""
    user = update.message.from_user
    logger.info(f"Пользователь {user.id} (@{user.username}) запустил бота через /start")

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

    try:
        if update.message:
            user = update.message.from_user
            logger.info(f"Пользователь {user.id} (@{user.username}) открыл главное меню")
            await update.message.reply_text("Выберите действие из меню:", reply_markup=reply_markup)
        elif update.callback_query:
            query = update.callback_query
            user = query.from_user
            logger.info(f"Пользователь {user.id} (@{user.username}) открыл главное меню через callback")
            await query.message.edit_text("Выберите действие из меню:", reply_markup=None)
    except Exception as e:
        logger.error(f"Ошибка при отображении главного меню пользователю {user.id}: {e}", exc_info=True)


async def back_to_menu(update, context):
    """Обработчик кнопки 'Назад в меню'"""
    query = update.callback_query
    await query.answer()
    await show_main_menu(update, context)


async def handle_main_menu_message(update, context):
    """Обработка текстовых сообщений главного меню"""
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "user"
    text = update.message.text

    logger.info(f"Пользователь {user_id} ({username}) выбрал пункт меню: {text}")

    try:
        if text == "Пройти интервью":
            await choose_vacancy(update, context)
        elif text == "Список вакансий":
            # используем vacancy_manager вместо прямого вызова load_vacancies
            vacancies = vacancy_manager.load_vacancies()
            await list_vacancies(update, context, vacancies)
        elif text == "Помощь":
            await update.message.reply_text(
                "Инструкции по использованию бота:\n"
                "- Выберите вакансию.\n"
                "- Загрузите резюме.\n"
                "- Пройдите голосовое интервью (если резюме подходит)."
            )
        elif text == "О боте":
            await update.message.reply_text(
                "AI HR Bot — ваш помощник HR для подбора и собеседования кандидатов.\n"
                "Бот анализирует резюме, проводит голосовое интервью и формирует отчёты."
            )
        else:
            logger.warning(f"Пользователь {user_id} ({username}) ввёл неизвестный пункт меню: {text}")
            await update.message.reply_text("⚠ Неизвестная команда. Пожалуйста, выберите пункт из меню.")
    except Exception as e:
        logger.error(f"Ошибка при обработке выбора пункта меню пользователем {user_id} ({username}): {e}", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")

# main.py
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from logs.logger import logger
from bot.data_loader import VacancyManager
from bot.callbacks import SELECT_VACANCY, VIEW_VACANCY, BACK_TO_MENU
from bot.menu_handlers import start_menu, handle_main_menu_message, back_to_menu
from bot.utils import list_vacancies
from bot.vacancy_handlers import choose_vacancy, vacancy_selected, show_vacancy_details, back_handler
from bot.resume_handlers import handle_resume

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# экземпляр менеджера вакансий
vacancy_manager = VacancyManager()


async def handle_message(update, context):
    """
    Обработка текстовых сообщений главного меню с логированием.
    """
    try:
        text = update.message.text
        user_id = update.message.from_user.id
        logger.info(f"Пользователь {user_id} отправил сообщение: {text}")

        if text == "Пройти интервью":
            await choose_vacancy(update, context)
        elif text == "Список вакансий":
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
            logger.warning(f"Пользователь {user_id} отправил неизвестное сообщение: {text}")

    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения пользователя {update.message.from_user.id}: {e}", exc_info=True)
        await update.message.reply_text("Произошла ошибка при обработке вашего сообщения. Попробуйте снова.")


if __name__ == "__main__":
    try:
        app = ApplicationBuilder().token(TOKEN).build()

        # Команда /start
        app.add_handler(CommandHandler("start", start_menu))

        # Обработка текстовых сообщений главного меню
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu_message))

        # CallbackQueryHandlers для вакансий и навигации
        app.add_handler(CallbackQueryHandler(vacancy_selected, pattern=SELECT_VACANCY))
        app.add_handler(CallbackQueryHandler(show_vacancy_details, pattern=VIEW_VACANCY))
        app.add_handler(CallbackQueryHandler(back_to_menu, pattern=BACK_TO_MENU))
        app.add_handler(CallbackQueryHandler(back_handler, pattern=r"^back_to_"))

        # Обработка загруженных документов (резюме)
        app.add_handler(MessageHandler(filters.Document.ALL, handle_resume))

        logger.info("Бот успешно запущен.")
        app.run_polling()

    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)

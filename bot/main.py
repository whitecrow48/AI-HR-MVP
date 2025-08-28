# main.py
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from bot.data_loader import load_vacancies
from bot.handlers import start_menu, choose_vacancy, vacancy_selected, back_to_menu, back_handler, handle_resume
from bot.utils import list_vacancies, show_vacancy_details
from bot.callbacks import SELECT_VACANCY, VIEW_VACANCY, BACK_TO_MENU

# Загрузка токена из .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")


async def handle_message(update, context):
    """
    Обработка текстовых сообщений главного меню.
    """
    text = update.message.text
    if text == "Пройти интервью":
        await choose_vacancy(update, context)
    elif text == "Список вакансий":
        vacancies = load_vacancies()
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


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Команда /start
    app.add_handler(CommandHandler("start", start_menu))

    # Обработка текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # CallbackQueryHandlers
    app.add_handler(CallbackQueryHandler(vacancy_selected, pattern=SELECT_VACANCY))
    app.add_handler(CallbackQueryHandler(show_vacancy_details, pattern=VIEW_VACANCY))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern=BACK_TO_MENU))
    app.add_handler(CallbackQueryHandler(back_handler, pattern=r"^back_to_"))  # общий для back_to_list/back_to_choose
    app.add_handler(MessageHandler(filters.Document.ALL, handle_resume))

    print("Бот запущен...")
    app.run_polling()

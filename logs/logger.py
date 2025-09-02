# logger.py
import logging
import os

# Папка для логов
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "log-output")
os.makedirs(LOG_DIR, exist_ok=True)  # создаём папку, если её нет

# Файл логов
LOG_FILE = os.path.join(LOG_DIR, "ai_hr_bot.log")

# Настройка логирования
logger = logging.getLogger("AI_HR_Bot")
logger.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

# Лог в файл
file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

# Лог в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Добавляем обработчики к логгеру
if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


logger.info("Логгер инициализирован. Логи сохраняются в 'logs/log-output/'")

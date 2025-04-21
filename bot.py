import logging
import os
import sys
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties
from dotenv import load_dotenv

# Добавляем корневую папку проекта в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорт обработчиков
from handlers import register_handlers

# Импорт функций для работы с базой данных
from db.db_initializer import initialize_database
from db.users import get_all_telegram_ids
from db.ban_list import get_ban_ids

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Логи в консоль
        logging.FileHandler("bot.log", encoding="utf-8")  # Логи в файл с кодировкой UTF-8
    ]
)

# Токен бота
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    logging.critical("Токен бота не найден. Проверьте файл .env.")
    raise ValueError("Токен бота не найден.")

# Инициализация бота и диспетчера с использованием MemoryStorage
storage = MemoryStorage()  # Используем MemoryStorage вместо RedisStorage
bot = Bot(
    token=TOKEN,
    session=AiohttpSession(),
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=storage)


async def on_startup():
    """
    Действия при запуске бота.
    """
    logging.info("Бот запускается...")

    # Удаляем активный webhook перед запуском long polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Webhook успешно удален.")
    except Exception as e:
        logging.error(f"Ошибка при удалении webhook: {e}")

    # Устанавливаем команды бота
    await set_bot_commands(bot)

    # Получаем список пользователей и заблокированных пользователей
    all_ids = get_all_telegram_ids()
    ban_list = get_ban_ids()
    logging.info(f"Список заблокированных пользователей: {ban_list}")
    logging.info(f"Список всех пользователей: {all_ids}")

    # Уведомляем пользователей о перезапуске бота
    for user_id in all_ids:
        try:
            await bot.send_message(
                user_id,
                "Бот был перезапущен администратором. Для корректной работы нажмите на /start."
            )
        except TelegramBadRequest:
            logging.warning(f"Чат не найден для user_id: {user_id}")
        except TelegramBadRequest:
            logging.warning(f"Бот заблокирован пользователем с ID: {user_id}")
            await bot.send_message(
                584404655,  # ID администратора для уведомления
                f"Бот был заблокирован пользователем с ID: {user_id}"
            )


async def on_shutdown():
    """
    Действия при остановке бота.
    """
    logging.info("Бот останавливается...")


async def set_bot_commands(bot: Bot):
    """
    Установка команд для бота.
    """
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
    ]
    await bot.set_my_commands(commands)


async def main():
    """
    Основная функция запуска бота.
    """
    # Удаляем активный webhook перед запуском long polling
    logging.info("Удаление активного webhook перед запуском бота...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Webhook успешно удален.")
    except Exception as e:
        logging.error(f"Ошибка при удалении webhook: {e}")
        return  # Прерываем запуск, если не удалось удалить webhook

    # Инициализация базы данных перед запуском бота
    logging.info("Инициализация базы данных перед запуском бота...")
    try:
        await initialize_database()
        logging.info("База данных успешно инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        return  # Прерываем запуск, если база данных не инициализирована

    # Установка команд бота
    await set_bot_commands(bot)  # Передаем объект bot

    # Регистрация обработчиков
    register_handlers(dp)

    logging.info("Бот успешно запущен!")
    try:
        await dp.start_polling(bot, on_startup=on_startup, on_shutdown=on_shutdown)
    except Exception as e:
        logging.error(f"Ошибка во время работы бота: {e}")


if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Бот остановлен!")
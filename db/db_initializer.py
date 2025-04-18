import aiosqlite
import logging

DATABASE_PATH = "telegram.db"

async def initialize_database():
    """
    Асинхронная инициализация базы данных: создание всех необходимых таблиц.
    """
    logging.info("Инициализация базы данных начата...")

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Создание таблицы пользователей
            logging.info("Создание таблицы users...")
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    telegram_id TEXT,
                    username TEXT,
                    telegram_frist_name TEXT,
                    telegram_second_name TEXT,
                    company_name TEXT,
                    phone TEXT,
                    user_role TEXT
                )
            ''')

            # Создание таблицы направлений
            logging.info("Создание таблицы direction...")
            await db.execute('''
                CREATE TABLE IF NOT EXISTS direction (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    direction_id INTEGER,
                    users_id TEXT,
                    direction_name TEXT,
                    direction_description TEXT,
                    direction_price TEXT,
                    direction_status TEXT,
                    winner TEXT,
                    FOREIGN KEY (users_id) REFERENCES users (id),
                    UNIQUE (direction_id)
                )
            ''')

            # Создание таблицы списка направлений
            logging.info("Создание таблицы directionList...")
            await db.execute('''
                CREATE TABLE IF NOT EXISTS directionList (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    telegram_id TEXT,
                    company_name TEXT,
                    direction TEXT,
                    old_price TEXT, 
                    new_price TEXT,
                    direction_status TEXT,
                    close_name TEXT
                )
            ''')

            # Создание таблицы заблокированных пользователей
            logging.info("Создание таблицы banList...")
            await db.execute('''
                CREATE TABLE IF NOT EXISTS banList (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    telegram_id TEXT
                )
            ''')

            # Создание таблицы отчетов
            logging.info("Создание таблицы report...")
            await db.execute('''
                CREATE TABLE IF NOT EXISTS report (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    direction_id INTEGER,
                    who_open_direct TEXT, 
                    direction_name TEXT,
                    start_price TEXT,
                    finish_price TEXT,
                    company_winner_name TEXT,
                    direction_status TEXT,
                    who_close_direct TEXT,
                    FOREIGN KEY (direction_id) REFERENCES direction (direction_id)
                )
            ''')

            # Сохранение изменений
            await db.commit()
            logging.info("База данных успешно инициализирована.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
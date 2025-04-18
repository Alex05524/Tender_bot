import aiosqlite

DATABASE_PATH = "telegram.db"

async def insert_id_to_ban_list(ID: str):
    """
    Асинхронное добавление пользователя в бан-лист.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        insert_query = '''
            INSERT INTO banList (telegram_id)
            VALUES (?)
        '''
        await db.execute(insert_query, (ID,))
        await db.commit()
        await db.close()
        print(f"Пользователь с ID {ID} добавлен в бан-лист.")

async def get_ban_ids():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute('SELECT telegram_id FROM banList') as cursor:
            ban_ids = [row[0] async for row in cursor]
    return ban_ids

async def check_user_in_ban_list(telegram_id: str):
    """
    Асинхронная проверка, находится ли пользователь в бан-листе.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT telegram_id
        FROM banList
        WHERE telegram_id = ?
        '''
        cursor = await db.execute(select_query, (telegram_id,))
        result = await cursor.fetchone()
        return result is not None
    
async def add_user_to_ban_list(telegram_id: str):
    """
    Асинхронное добавление пользователя в бан-лист.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        insert_query = '''
        INSERT INTO banList (telegram_id)
        VALUES (?)
        '''
        await db.execute(insert_query, (telegram_id,))
        await db.commit()
        await db.close()
        print(f"Пользователь с ID {telegram_id} добавлен в бан-лист.")

async def remove_user_from_ban_list(telegram_id: str):
    """
    Асинхронное удаление пользователя из бан-листа.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        delete_query = '''
        DELETE FROM banList
        WHERE telegram_id = ?
        '''
        await db.execute(delete_query, (telegram_id,))
        await db.commit()
        await db.close()
        print(f"Пользователь с ID {telegram_id} удален из бан-листа.")

async def get_direction_1():
    """
    Асинхронное получение направлений с их именами и идентификаторами, которые имеют статус 'Open'.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT direction_name, direction_id
        FROM direction
        WHERE direction_status = 'Open'
        '''
        cursor = await db.execute(select_query)
        directions = await cursor.fetchall()
        return directions
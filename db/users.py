import aiosqlite
import sqlite3

# Создаем соединение с базой данных
conn = sqlite3.connect('telegram.db')

# Создаем курсор
cursor = conn.cursor()

DATABASE_PATH = "telegram.db"

def add_user(ID, name, telegram_frist_name, telegram_second_name, company_name, phone, user_role):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Проверяем, существует ли запись с таким ID
    select_query = "SELECT id FROM users WHERE telegram_id = ?"
    cursor.execute(select_query, (ID,))
    existing_user = cursor.fetchone()

    if existing_user is None:
        insert_query = '''
            INSERT INTO users (telegram_id, username, telegram_frist_name, telegram_second_name, company_name, phone, user_role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        cursor.execute(insert_query, (ID, name, telegram_frist_name, telegram_second_name, company_name, phone, user_role))
        conn.commit()
        conn.close()
    else:
        print("Пользователь с таким ID уже существует.")

    print("Пользователь добавлен в базу данных.")

async def get_user_role(ID: str):
    """
    Асинхронное получение роли пользователя по Telegram ID.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT user_role
        FROM users
        WHERE telegram_id = ?
        '''
        cursor = await db.execute(select_query, (ID,))
        result = await cursor.fetchone()
        return result

def get_user_role(ID):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select_query = '''
                SELECT user_role
                FROM users
                WHERE telegram_id = ?
            '''
    cursor.execute(select_query, (ID,))
    conn.commit()
    result = cursor.fetchone()
    conn.close()

    return result

async def get_all_users():
    """
    Получение всех пользователей с ролью 'user'.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
            SELECT telegram_id, username, company_name, phone
            FROM users
            WHERE user_role = 'user'
        '''
        cursor = await db.execute(select_query)
        all_users = await cursor.fetchall()
        return all_users

def get_user_data_by_id(ID):
    """
    Получает данные пользователя из базы данных по telegram_id.
    """
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()
    select_query = "SELECT * FROM users WHERE telegram_id = ?"
    cursor.execute(select_query, (ID,))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

async def get_user_company_by_id(user_id: int):
    """
    Получает название компании пользователя из таблицы users по telegram_id.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            query = '''
            SELECT company_name
            FROM users
            WHERE telegram_id = ?
            '''
            cursor = await db.execute(query, (user_id,))
            result = await cursor.fetchone()
            if result:
                return result[0]  # Возвращаем название компании
            else:
                return None  # Если пользователь не найден
        except Exception as e:
            print(f"Ошибка при выполнении запроса get_user_company_by_id: {e}")
            return None

async def update_user_name(new_user_name, ID):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE users SET username = ?
            WHERE telegram_id = ?
        ''', (new_user_name, ID))
        await db.commit()

def get_user_company_by_telegram_id(ID):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select = '''
    select company_name from users
    where telegram_id = ?
    limit 1
    '''

    cursor.execute(select, (ID,))
    company_name = cursor.fetchone()

    return company_name

async def get_all_telegram_ids():
    """
    Асинхронное получение всех Telegram ID пользователей.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT telegram_id
        FROM users
        '''
        cursor = await db.execute(select_query)
        all_ids = [row[0] for row in await cursor.fetchall()]
        return all_ids

async def get_admin_and_manager_ids():
    """
    Асинхронное получение Telegram ID администраторов и менеджеров.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT telegram_id
        FROM users
        WHERE user_role IN ('admin', 'manager')
        '''
        cursor = await db.execute(select_query)
        ids = [row[0] for row in await cursor.fetchall()]
        return ids
    
async def get_id_by_username(username_from_deactivation: str):
    """
    Асинхронное получение Telegram ID пользователя по имени пользователя.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT telegram_id
        FROM users
        WHERE username = ?
        '''
        cursor = await db.execute(select_query, (username_from_deactivation,))
        id = await cursor.fetchone()
        return id

async def remove_user(username: str):
    """
    Асинхронное удаление пользователя по имени.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        delete_query = '''
        DELETE FROM users
        WHERE username = ?
        '''
        await db.execute(delete_query, (username,))
        await db.commit()
        await db.close()
        print(f"Пользователь {username} был удален.")

async def check_user_exists_by_username(username: str):
    """
    Асинхронная проверка существования пользователя по имени.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT username
        FROM users
        WHERE username = ?
        '''
        cursor = await db.execute(select_query, (username,))
        result = await cursor.fetchone()
        return result is not None
    
async def remove_user_by_username(username: str):
    """
    Асинхронное удаление пользователя по имени.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        delete_query = '''
        DELETE FROM users
        WHERE username = ?
        '''
        await db.execute(delete_query, (username,))
        await db.commit()
        await db.close()
        print(f"Пользователь {username} был удален.")

async def get_user_role_username(username: str):
    """
    Асинхронное получение роли пользователя по имени пользователя.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT user_role
        FROM users
        WHERE username = ?
        '''
        cursor = await db.execute(select_query, (username,))
        result = await cursor.fetchone()
        return result
    
async def new_manager(user_new_role: str, new_manager_name: str):
    """
    Асинхронное обновление роли пользователя на 'manager'.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        update_query = '''
        UPDATE users
        SET user_role = ?
        WHERE username = ?
        '''
        await db.execute(update_query, (user_new_role, new_manager_name))
        await db.commit()
        await db.close()
        print(f"Добавлен новый менеджер: {new_manager_name}")

async def get_username_by_id(ID: str):
    """
    Асинхронное получение имени пользователя по Telegram ID.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT username
        FROM users
        WHERE telegram_id = ?
        '''
        cursor = await db.execute(select_query, (ID,))
        result = await cursor.fetchone()
        return result  # Возвращаем результат
    
async def get_managers():
    """
    Получает список всех менеджеров и администраторов.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            query = '''
            SELECT telegram_id, username, user_role
            FROM users
            WHERE user_role IN ('manager', 'admin')
            '''
            cursor = await db.execute(query)
            result = await cursor.fetchall()
            print(f"Результат запроса get_managers: {result}")  # Для отладки
            return result  # Возвращает список кортежей (telegram_id, username, role)
        except Exception as e:
            print(f"Ошибка при выполнении запроса get_managers: {e}")
            return []
    
async def update_company_name(new_company_name: str, ID: str):
    """
    Асинхронное обновление названия компании пользователя по Telegram ID.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        update_query = '''
        UPDATE users
        SET company_name = ?
        WHERE telegram_id = ?
        '''
        await db.execute(update_query, (new_company_name, ID))
        await db.commit()
        await db.close()
        print(f"Название компании обновлено на '{new_company_name}' для пользователя с ID {ID}.")

async def update_phone_number(new_number, ID):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE users SET phone = ?
            WHERE telegram_id = ?
        ''', (new_number, ID))
        await db.commit()
        await db.close()

async def delete_managers_role(new_user_role: str, rm_manager_name: str):
    """
    Асинхронное удаление роли менеджера у пользователя.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        update_query = '''
        UPDATE users
        SET user_role = ?
        WHERE username = ?
        '''
        await db.execute(update_query, (new_user_role, rm_manager_name))
        await db.commit()
        print(f"Пользователь {rm_manager_name} был удален из менеджеров.")

async def get_telegram_id_user(ID):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT id FROM users WHERE telegram_id = ?", (ID,)) as cursor:
            existing_user = await cursor.fetchone()
            if existing_user is None:
                print("None")
                return None
            else:
                return existing_user[0]
            
async def get_telegram_id_username(direction_winner_name: str):
    """
    Асинхронное получение Telegram ID пользователя по имени пользователя.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Проверяем, существует ли пользователь с таким именем
        select_query_check = "SELECT id FROM users WHERE username = ?"
        cursor = await db.execute(select_query_check, (direction_winner_name,))
        existing_user = await cursor.fetchone()

        if existing_user is None:
            print("None")
            return None

        # Получаем Telegram ID пользователя
        select_query = '''
        SELECT telegram_id
        FROM users
        WHERE username = ?
        '''
        cursor = await db.execute(select_query, (direction_winner_name,))
        result = await cursor.fetchone()
        return result  # Вернуть результат запроса
    
async def get_telegram_id_company(direction_winner_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT id FROM users WHERE username = ?", (direction_winner_name,)) as cursor:
            existing_user = await cursor.fetchone()
            if existing_user is None:
                print("None")
                return None

        async with db.execute("SELECT telegram_id FROM users WHERE company_name = ?", (direction_winner_name,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None
        
def get_admins_telegram_ids(admin_role):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select_query = '''
        SELECT telegram_id
        FROM users
        where user_role = ?
    '''

    cursor.execute(select_query, (admin_role,))
    admin_telegram_ids = [row[0] for row in cursor.fetchall()]

    conn.close()

    return admin_telegram_ids

def get_manager_telegram_ids(manager_role):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select_query = '''
        SELECT telegram_id
        FROM users
        where user_role = ?
    '''

    cursor.execute(select_query, (manager_role,))
    manager_telegram_ids = [row[0] for row in cursor.fetchall()]

    conn.close()

    return manager_telegram_ids

def get_users_telegram_ids(user_role):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select_query = '''
        SELECT telegram_id
        FROM users
        where user_role = ?
    '''

    cursor.execute(select_query, (user_role,))
    users_telegram_ids = [row[0] for row in cursor.fetchall()]

    conn.close()

    return users_telegram_ids
    
async def get_direction_winner():
    """
    Асинхронное получение списка уникальных названий компаний пользователей с ролью 'user'.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT DISTINCT company_name
        FROM users
        WHERE user_role = 'user'
        '''
        cursor = await db.execute(select_query)
        direction_winner = [row[0] for row in await cursor.fetchall()]
        return direction_winner
    
async def get_direction_username_winner():
    """
    Асинхронное получение списка имен пользователей с ролью 'user'.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT username
        FROM users
        WHERE user_role = 'user'
        '''
        cursor = await db.execute(select_query)
        direction_winner = [row[0] for row in await cursor.fetchall()]
        return direction_winner

async def get_telegram_id_by_comapny(direction_winner_name: str):
    """
    Асинхронное получение Telegram ID пользователей по названию компании.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT telegram_id
        FROM users
        WHERE company_name = ?
        '''
        cursor = await db.execute(select_query, (direction_winner_name,))
        company = [row[0] for row in await cursor.fetchall()]
        return company
    
async def get_admin_and_managers_ids():
    """
    Асинхронное получение Telegram ID администраторов и менеджеров.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT telegram_id
        FROM users
        WHERE user_role IN ('admin', 'manager')
        '''
        cursor = await db.execute(select_query)
        ids = [row[0] for row in await cursor.fetchall()]
        return ids


async def get_all_username_without_you_id(ID: str):
    """
    Асинхронное получение всех пользователей (telegram_id и username), кроме указанного Telegram ID.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT telegram_id, username
        FROM users
        WHERE telegram_id != ?
        '''
        cursor = await db.execute(select_query, (ID,))
        users = await cursor.fetchall()  # Возвращает список кортежей (telegram_id, username)
        return users

async def check_user_correct_username(username_from_deactivation: str):
    """
    Асинхронная проверка существования пользователя по имени.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        select_query = '''
        SELECT username
        FROM users
        WHERE username = ?
        '''
        cursor = await db.execute(select_query, (username_from_deactivation,))
        check_status = await cursor.fetchone()
        return check_status is not None
    
async def check_user_correct_username_manger(username_from_deactivation):
    async with aiosqlite.connect('telegram.db') as conn:
        async with conn.execute('''
            SELECT username FROM users WHERE username = ?
        ''', (username_from_deactivation,)) as cursor:
            check_status = await cursor.fetchone()
    return check_status is not None

async def update_user_role(new_role, telegram_id):
    """
    Обновляет роль пользователя в базе данных.
    """
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE users SET user_role = ?
            WHERE telegram_id = ?
        ''', (new_role, telegram_id))
        await db.commit()
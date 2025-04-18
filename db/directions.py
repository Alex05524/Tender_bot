import sqlite3

# Создаем соединение с базой данных
conn = sqlite3.connect('telegram.db')

# Создаем курсор
cursor = conn.cursor()


def add_direction_info(direction_id, users_id, summary, description, price, status):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    insert_query = '''
    INSERT INTO direction (direction_id, users_id, direction_name, direction_description, direction_price, direction_status)
    VALUES (?,?,?,?,?,?)
    '''
    cursor.execute(insert_query, (direction_id, users_id, summary, description, price, status))
    conn.commit()
    conn.close()
    print("Направление было успешно добавлено в БД")

def get_open_direction():
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select_query = '''
            SELECT direction_name
            FROM direction
            WHERE status = 'Open' 
        '''

    cursor.execute(select_query)
    #directions = [row for row in cursor.fetchall()]
    open_directions = [row[0] for row in cursor.fetchall()]
    conn.close()

    return open_directions

def chek_direction(direction_summary):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()


    select_query = '''
    select direction_name from direction
    where direction_name = ?
    and direction_status = 'Open'
    '''

    cursor.execute(select_query, (direction_summary,))
    result = cursor.fetchone()
    return result
    
def close_direction(direction_name_for_close):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    update_query1 = '''W
        update direction set direction_status = 'Close'
        where direction_name = ?
    '''

    update_query2 = '''
        update directionList set direction_status = 'Close'
        where direction = ?
    '''
    cursor.execute(update_query1, (direction_name_for_close,))
    cursor.execute(update_query2, (direction_name_for_close,))
    conn.commit()
    conn.close()
    print(f"Направление {direction_name_for_close} было закрыто")

def get_direction_info(direction_name):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select_query = '''
            SELECT *
            FROM direction
            WHERE direction_name = ?
            AND direction_status = 'Open'
        '''
    cursor.execute(select_query, (direction_name,))

    # Извлечь результат выполнения запроса
    direction_name = cursor.fetchone()

    conn.close()

    return direction_name  # Вернуть данные пользователя


def get_direction():
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    select_query = '''
            SELECT direction_name, direction_id
            FROM direction
            WHERE direction_status = 'Open'
        '''

    cursor.execute(select_query)
    #directions = [row for row in cursor.fetchall()]
    directions = [row[0] for row in cursor.fetchall()]
    conn.close()


    return directions

def set_who_close_direction_username(who_close_username, direction_name):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    update_query = '''
    update directionList set close_name = ?
    where direction = ?
    '''

    who_close_username = str(who_close_username)
    direction_name = str(direction_name)

    cursor.execute(update_query, (who_close_username, direction_name,))
    conn.commit()
    conn.close()

def set_winner_name(direction_winner_name, direction_name_for_close):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    update_query1 = '''
        update direction set winner = ?
        where direction_name = ?
    '''


    cursor.execute(update_query1, (direction_winner_name, direction_name_for_close,))
    conn.commit()
    conn.close()

def get_last_direction_id():
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()


    select_query = '''
    select direction_id from direction d 
    order by direction_id desc
    limit 1
    '''

    cursor.execute(select_query)

    result = cursor.fetchone()
    return result

def update_new_user_price(new_price, company_name, direction_name):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()

    update_query = '''
    update directionList set new_price = ?
    where company_name = ?
    and direction = ?
    '''
    cursor.execute(update_query, (new_price, company_name, direction_name))
    conn.commit()
    conn.close()

def update_price_new(price, direction_name_for_close, direction_winner_name):
    conn = sqlite3.connect('telegram.db')
    cursor = conn.cursor()



    update_query_company_price = '''
        update report set finish_price = ?
        where direction_name = ?
        and company_winner_name = ?
    '''

    cursor.execute(update_query_company_price, (price, direction_name_for_close, direction_winner_name))
    conn.commit()
    conn.close()
    print(f"Запись цены добавлена")    
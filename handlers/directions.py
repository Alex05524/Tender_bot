import os
import asyncio
import aiogram
from aiogram import Bot, Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.directions import (
    add_direction_info, get_direction, get_direction_info, set_winner_name, chek_direction,
    get_last_direction_id, set_who_close_direction_username, update_price_new
)
from db.direction_list import (
    close_direction_l, select_my_directionlist, chek_price_to_report,
    get_direction_list_direction_by_company, get_my_price_for_direction,
    insert_direction_list_info, select_my_direction, update_direction_price
)
from db.reports import (
    add_info_in_report, add_info_in_report_insert_direction_id, report_close_get_price,
    set_winner_name_report, close_direction_set_status, close_direction_set_who_close_direction,
    get_last_id_report
)
from db.users import (
    get_user_role, get_user_data_by_id, get_admin_and_managers_ids, get_direction_winner,
    get_username_by_id, get_telegram_id_company, get_user_company_by_telegram_id, get_telegram_id_user,
    get_admins_telegram_ids, get_users_telegram_ids, get_manager_telegram_ids, get_all_users, get_telegram_id_by_comapny
)
from aiogram.exceptions import TelegramBadRequest
from states.states import CreateLot, SentDirectionPrice, UpdateDirectionNewPrice, CloseDirection, SentDirectionPrice

ID = None
DATABASE_PATH = "telegram.db"

router = Router()

token=str(os.getenv('BOT_TOKEN'))
bot = Bot(token=token)

## Получаем список всех направлений
@router.callback_query(lambda c: c.data == "open_direction")
async def create_new_direction_summary(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для начала создания нового направления.
    """
    ID = callback_query.from_user.id
    user_id = callback_query.from_user.id
    user_role = get_user_role(ID)
    user_data = get_user_data_by_id(ID)
    if user_role and user_role[0] in ["manager", "admin"]:
        await callback_query.message.edit_text("✒ Введите название направления")
        await state.set_state(CreateLot.summary)  # Установка состояния
    else:
        print(f"Пользователь с ID {ID} имеет роль: {user_role}")
        await callback_query.message.edit_text("❌ У вас нет прав для выполнения этого действия.")

# Получаем данные из состояния
@router.callback_query(F.data == "open_direction_renew", StateFilter(CreateLot.price))
async def create_new_direction_summary(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для повторного ввода названия направления.
    """
    ID = callback_query.from_user.id

    # Получаем роль пользователя
    user_id = await get_telegram_id_user(ID)
    user_role = await get_user_role(ID)
    user_data = get_user_data_by_id(ID)
    if not user_role:
        await callback_query.message.edit_text("❌ Ошибка: роль пользователя не найдена.")
        return

    # Проверяем роль пользователя
    if user_role[0] in ['manager', 'admin']:
        await callback_query.message.edit_text("✒ Введите название направления")

        # Проверка на случай, если текст сообщения начинается с "/"
        if callback_query.message.text and callback_query.message.text.startswith("/"):
            await callback_query.message.answer("❌ Ошибка: название направления не может начинаться с '/'.")
        else:
            await state.set_state(CreateLot.summary)  # Устанавливаем состояние
    else:
        await callback_query.message.edit_text("❌ У вас нет прав для выполнения этого действия.")

# Получаем данные из состояния
@router.message(F.text & ~F.text.startswith('/'), StateFilter(CreateLot.summary))
async def create_new_direction_description(message: types.Message, state: FSMContext):
    """
    Обработчик для ввода названия направления.
    """
    direction_summary = message.text.strip()

    # Проверка на существование направления
    chek = chek_direction(direction_summary)
    print(f"Проверка существования направления: {chek}")

    if chek:
        await message.answer("❌ Такое направление уже открыто, пожалуйста введите другое название.")
    else:
        # Сохраняем название направления в состоянии
        await state.update_data(direction_summary=direction_summary)
        await state.set_state(CreateLot.description)  # Переход к следующему состоянию
        await message.answer("✒ Введите подробное описание направления.")

# Получаем данные из состояния
@router.message(F.text & ~F.text.startswith('/'), StateFilter(CreateLot.description))
async def create_new_direction_price(message: types.Message, state: FSMContext):
    """
    Обработчик для ввода описания направления.
    """
    # Сохраняем описание направления в состоянии
    await state.update_data(direction_description=message.text.strip())
    await message.answer("✒ Введите стартовую цену.")
    await state.set_state(CreateLot.price)

# Получаем данные из состояния
@router.message(F.text & ~F.text.startswith('/'), StateFilter(CreateLot.price))
async def create_new_direction_price_price(message: types.Message, state: FSMContext):
    """
    Обработчик для ввода стартовой цены направления.
    """
    # Сохраняем стартовую цену в состоянии
    await state.update_data(direction_price=message.text.strip())

    # Получаем данные из состояния
    data = await state.get_data()
    summary = data.get("direction_summary")
    description = data.get("direction_description")
    price = data.get("direction_price")

    print(f"Название: {summary}, Описание: {description}, Цена: {price}")

    # Создаем кнопки подтверждения
    create_direction = InlineKeyboardButton(text="✅ Да, все верно", callback_data="create_direction")
    dont_create_direction = InlineKeyboardButton(text="🔄 Нет, заполнить по новой", callback_data="open_direction_renew")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[create_direction], [dont_create_direction]])

    # Проверка длины названия
    if len(summary) > 25:
        await message.answer(
            f"⚠️ ВНИМАНИЕ!!!\nСлишком длинное название.\n"
            f"🗺 Вы точно хотите открыть следующее направление:\n"
            f"Название: {summary}\nДлина названия: {len(summary)} символов\n"
            f"📝 Описание: {description}\n💲 Начальная цена: {price} тг.",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            f"🗺 Вы точно хотите открыть следующее направление:\n"
            f"Название: {summary}\nДлина названия: {len(summary)} символов\n"
            f"📝 Описание: {description}\n💲 Начальная цена: {price} тг.",
            reply_markup=keyboard
        )

# Подтверждение создания нового направления
@router.callback_query(F.data == 'create_direction', StateFilter(CreateLot.price))
async def countine_crete_direction(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для завершения создания нового направления.
    """
    direction_status = 'Open'  # Статус направления для таблицы direction
    close_name = 'null'  # Поле close_name должно быть null
    new_price = 'null'  # Поле new_price должно быть null

    # Получаем данные из состояния
    data = await state.get_data()
    await state.clear()  # Завершаем состояние
    summary = data.get('direction_summary')
    description = data.get('direction_description')
    price = data.get('direction_price')
    ID = callback_query.from_user.id

    # Получаем роль пользователя
    user_role = get_user_role(ID)
    if not user_role or user_role[0] not in ['admin', 'manager']:
        await callback_query.message.edit_text('❌ У вас нет прав для выполнения этого действия.')
        return

    # Получаем имя пользователя, открывшего направление
    who_open_direction = await get_username_by_id(ID)

    # Получаем название компании пользователя
    user_data = get_user_data_by_id(ID)
    company_name = user_data[5] if user_data and len(user_data) > 5 else 'null'

    # Создаем клавиатуру для возврата на главную или создания нового направления
    get_to_main = InlineKeyboardButton(text='🔚 Вернуться на главную', callback_data='main')
    create_another_direction = InlineKeyboardButton(text='🔂 Зарегистрировать еще одно направление', callback_data='open_direction')
    k = InlineKeyboardMarkup(inline_keyboard=[[get_to_main], [create_another_direction]])

        # Генерация ID направления
    last_direction_id = get_last_direction_id()
    try:
        if last_direction_id is None or last_direction_id[0] is None:
            direction_id = 1  # Если таблица пуста или результат None, начинаем с ID = 1
        else:
            direction_id = last_direction_id[0] + 1  # Увеличиваем последний ID на 1
    except Exception as e:
        print(f"Ошибка при генерации ID направления: {e}")
        direction_id = 1  # Устанавливаем ID = 1 в случае ошибки

        # Генерация ID для отчета
    try:
        last_id = await get_last_id_report()  # Предполагается, что возвращается int или None
        if last_id is None:
            last_id = 1  # Если таблица пуста, начинаем с ID = 1
        else:
            last_id += 1  # Увеличиваем ID на 1
    except Exception as e:
        print(f"Ошибка при получении последнего ID отчета: {e}")
        await callback_query.message.edit_text("❌ Ошибка при создании направления. Попробуйте позже.")
        return

    # Добавление данных в таблицы direction и report
    try:
        # Добавляем данные в таблицу direction с корректным статусом Open
        add_direction_info(direction_id, ID, summary, description, price, direction_status)
        print(f"Направление {summary} успешно добавлено в таблицу direction с ID {direction_id}.")
    except Exception as e:
        print(f"Ошибка при добавлении направления в таблицу direction: {e}")
        
        await add_info_in_report(who_open_direction, summary, price, new_price, company_name, direction_status, close_name)
        await add_info_in_report_insert_direction_id(direction_id, last_id)

        # Добавление данных в таблицу directionList
        try:
            insert_direction_list_info(
                ID,  # Telegram ID
                company_name,  # Название компании
                summary,  # Название направления
                price,  # Старая цена
                new_price,  # Новая цена (null)
                'active',  # Статус направления для directionList
            )
            print(f"Направление {summary} успешно добавлено в таблицу directionList.")
        except Exception as e:
            print(f"Ошибка при добавлении направления в таблицу directionList: {e}")
            await callback_query.message.edit_text("❌ Ошибка при создании направления. Попробуйте позже.")
            return

    # Уведомление об успешном создании направления
    await callback_query.message.answer('✅ Направление было открыто', reply_markup=k)

    # Уведомляем пользователей
    user_role = 'user'
    user_telegram_ids = get_users_telegram_ids(user_role)
    direction_name = summary
    notification_text = f"📢 Было открыто новое направление:\nНазвание: {direction_name}\nНачальная цена: {price} тг."
    notification_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Перейти в направление', callback_data=f'direction_{direction_name}')]
    ])

    # Уведомляем администраторов и менеджеров
    admin_and_managers_ids = await get_admin_and_managers_ids()
    for admin_or_manager_id in admin_and_managers_ids:
        try:
            await bot.send_message(
                int(admin_or_manager_id),
                f"📢 Было открыто новое направление:\nНазвание: {direction_name}\nНачальная цена: {price} тг.",
                reply_markup=notification_keyboard
            )
        except TelegramBadRequest as e:
            print(f"Чат не найден для admin_or_manager_id: {admin_or_manager_id}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения администратору/менеджеру {admin_or_manager_id}: {e}")

    # Уведомляем пользователей
    for user_id in user_telegram_ids:
        try:
            await bot.send_message(
                int(user_id),
                f"📢 Было открыто новое направление:\nНазвание: {direction_name}\nНачальная цена: {price} тг.",
                reply_markup=notification_keyboard
            )
        except TelegramBadRequest as e:
            print(f"Чат не найден для user_id: {user_id}")
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

# Уведомляем компанию о создании направления
@router.callback_query(F.data == 'list_directionn', StateFilter('*'))
async def get_all_direction(callback_query: types.CallbackQuery):
    """
    Обработчик для отображения всех открытых направлений.
    """
    # Получаем список всех направлений
    all_directions = get_direction()
    print(f"Список всех направлений: {all_directions}")

    # Создаем клавиатуру
    buttons = []

    if not all_directions:
        # Если направлений нет, добавляем только кнопку возврата
        buttons.append([InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='main')])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback_query.message.edit_text(
            "❌ В данный момент нет открытых направлений.",
            reply_markup=keyboard
        )
    else:
        # Если направления есть, добавляем их в клавиатуру
        for direction_name in all_directions:
            buttons.append([InlineKeyboardButton(
                text=str(direction_name),  # Преобразуем значение в строку
                callback_data=f'direction_{direction_name}'
            )])
        # Добавляем кнопку возврата
        buttons.append([InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='main')])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Отправляем сообщение с клавиатурой
        await callback_query.message.edit_text(
            "📋 Выберите направление:",
            reply_markup=keyboard
        )

# Получаем информацию о направлении
@router.callback_query(F.data.startswith('direction_'), StateFilter('*'))
async def get_info_from_direction(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для получения информации о направлении.
    """
    ID = callback_query.from_user.id
    direction_name = callback_query.data.replace('direction_', '')

    # Получаем данные о пользователе и направлении
    user_role = get_user_role(ID)
    user_data = get_user_data_by_id(ID)
    direction_info = get_direction_info(direction_name)

    # Проверяем, существует ли информация о направлении
    if not direction_info:
        await callback_query.message.edit_text("❌ Ошибка: информация о направлении не найдена.")
        return

    # Проверяем, существует ли пользователь и его роль
    if not user_role or not user_data:
        await callback_query.message.edit_text("❌ Ошибка: данные пользователя не найдены.")
        return

    # Если пользователь администратор или менеджер
    if user_role[0] in ['admin', 'manager']:
        # Создаем клавиатуру для администраторов и менеджеров
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="list_directionn")]
        ])
        await callback_query.message.edit_text(
            f"⚠ Вот информация по данному направлению:\n"
            f"Название: {direction_info[3]}, ID: {direction_info[1]}\n"
            f"Подробное описание: {direction_info[4]}\n"
            f"Начальная цена: {direction_info[5]} тг.",
            reply_markup=keyboard
        )
    else:
        # Если пользователь обычный пользователь
        print(f"{user_data[2]} перешел в направление - {direction_info[1]}")

        # Сохраняем данные о направлении в состоянии
        await state.update_data(direction_all_info=direction_info)

        # Создаем клавиатуру для пользователей
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💵 Предложить свою цену", callback_data="sent_you_price")],
            [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="main")]
        ])

        await callback_query.message.edit_text(
            f"⚠ Вот информация по данному направлению:\n"
            f"Название: {direction_info[3]}, ID: {direction_info[1]}\n"
            f"Подробное описание: {direction_info[4]}\n"
            f"Начальная цена: {direction_info[5]} тг.",
            reply_markup=keyboard
        )

        # Устанавливаем состояние
        await state.set_state(SentDirectionPrice.getIdDirection)
        print("Состояние SentDirectionPrice.getIdDirection установлено.")

# Подтверждение новой цены 0
@router.callback_query(F.data == 'sent_you_price', StateFilter(SentDirectionPrice.getIdDirection))
async def sent_you_price(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для отклика пользователя на направление с предложением своей цены.
    """
    ID = callback_query.from_user.id

    # Получаем название компании пользователя
    company_name_tuple = get_user_company_by_telegram_id(ID)
    if not company_name_tuple:
        await callback_query.message.edit_text("❌ Ошибка: информация о компании не найдена.")
        return

    company_name = company_name_tuple[0]  # Извлекаем строку из кортежа
    print(f"Пользователь из компании - {company_name} хочет отправить цену")

    # Получаем данные о направлении из состояния
    data = await state.get_data()
    direction_all_info = data.get('direction_all_info')
    if not direction_all_info or len(direction_all_info) < 6:
        await callback_query.message.edit_text("❌ Ошибка: данные о направлении некорректны.")
        return

    direction_name = direction_all_info[3]
    direction_start_price = direction_all_info[5]

    print(f"Направление: {direction_name}, Начальная цена: {direction_start_price}")

    # Проверяем, отправляла ли компания цену для данного направления
    try:
        check = get_direction_list_direction_by_company(company_name, direction_name)
    except Exception as e:
        print(f"Ошибка при проверке отправки цены: {e}")
        await callback_query.message.edit_text("❌ Ошибка при проверке данных. Попробуйте позже.")
        return

    print(f"Проверка отправки цены: {check}")

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')]
    ])

    if check:
        # Если компания уже отправляла цену
        await callback_query.message.edit_text(
            "Вы уже отправляли цену для данного направления. "
            "Обновить цену можно в меню, доступном по кнопке ниже.",
            reply_markup=keyboard
        )
    else:
        # Если компания еще не отправляла цену
        await state.set_state(SentDirectionPrice.enterNewDirectionPrice)
        await callback_query.message.answer(
            f"💲 Пожалуйста, укажите вашу цену для данного направления. "
            f"Минимальная цена: {direction_start_price} тг."
        )
        print("Состояние SentDirectionPrice.enterNewDirectionPrice установлено.")

# Подтверждение новой цены 1
@router.message(StateFilter(SentDirectionPrice.enterNewDirectionPrice))
async def countine_setn_you_price(message: types.Message, state: FSMContext):
    """
    Обработчик для подтверждения новой цены, предложенной пользователем.
    """
    # Проверяем, является ли введенная цена числом
    if not message.text.isdigit():
        await message.answer("❌ Ошибка: цена должна быть числом. Попробуйте снова.")
        return

    # Получаем новую цену
    new_price = int(message.text)
    if new_price <= 0:
        await message.answer("❌ Ошибка: цена должна быть больше 0. Попробуйте снова.")
        return

    # Получаем данные о направлении из состояния
    data = await state.get_data()
    direction_all_info = data.get('direction_all_info')
    if not direction_all_info:
        await message.answer("❌ Ошибка: данные о направлении не найдены.")
        return

    # Получаем начальную цену направления
    direction_start_price = int(direction_all_info[5])

    # Проверяем, что новая цена не выше начальной
    if new_price > direction_start_price:
        await message.answer(
            f"❌ Ошибка: цена не может быть выше начальной ({direction_start_price} тг). Попробуйте снова."
        )
        return

    # Получаем название компании пользователя
    user_id = message.from_user.id
    user_data = get_user_data_by_id(user_id)
    if not user_data:
        await message.answer("❌ Ошибка: информация о пользователе не найдена.")
        return

    company_name = user_data[5]

    # Проверяем, не равна ли новая цена ранее предложенной
    previous_price = get_my_price_for_direction(company_name, direction_all_info[3])
    if previous_price and new_price == int(previous_price[0]):
        await message.answer(
            f"❌ Ошибка: новая цена не может быть равна ранее предложенной ({previous_price[0]} тг). Попробуйте снова."
        )
        return

    # Сохраняем новую цену в состоянии
    await state.update_data(direction_new_price=new_price)

    # Создаем клавиатуру для подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Да', callback_data='sent_my_new_price')],
        [InlineKeyboardButton(text='❌ Нет', callback_data='dont_sent_you_price')]
    ])

    # Отправляем сообщение с подтверждением
    await message.answer(
        f"Вы хотите предложить {new_price} тг?",
        reply_markup=keyboard
    )

# Подтверждение новой цены 2
@router.callback_query(F.data == 'sent_my_new_price', StateFilter(SentDirectionPrice.enterNewDirectionPrice))
async def create_new_direction_price(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для отправки новой цены на направление.
    """
    # Получаем данные из состояния
    data = await state.get_data()
    direction_all_info = data.get('direction_all_info')
    direction_new_price_str = data.get('direction_new_price')

    if not direction_all_info or not direction_new_price_str:
        await callback_query.message.edit_text("❌ Ошибка: данные о направлении или цене не найдены.")
        return

    try:
        direction_old_price = int(str(direction_all_info[5]).replace(' ', ''))
        direction_new_price = int(str(direction_new_price_str).replace(' ', ''))
        direction_name = direction_all_info[3]
        direction_id = direction_all_info[1]
    except (ValueError, IndexError) as e:
        print(f"Ошибка при обработке данных о направлении: {e}")
        await callback_query.message.edit_text("❌ Ошибка при обработке данных о направлении.")
        return

    # Получаем данные пользователя
    ID = callback_query.from_user.id
    user_data = get_user_data_by_id(ID)
    if not user_data:
        await callback_query.message.edit_text("❌ Ошибка: информация о пользователе не найдена.")
        return

    company_name = user_data[5]

    # Проверяем, что новая цена меньше начальной
    if direction_new_price >= direction_old_price:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔚 Вернуться в главное меню', callback_data='accept_user_data')]
        ])
        await callback_query.message.edit_text(
            "🚫 Новая цена не может быть больше или равна начальной!\n"
            "Введите /start и снова предложите цену в доступных направлениях.",
            reply_markup=keyboard
        )
        return

    # Проверяем, что новая цена не равна ранее предложенной
    previous_price = get_my_price_for_direction(company_name, direction_name)
    if previous_price and direction_new_price == int(previous_price[0]):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔚 Вернуться в главное меню', callback_data='accept_user_data')]
        ])
        await callback_query.message.edit_text(
            f"🚫 Новая цена не может быть равна ранее предложенной ({previous_price[0]} тг).",
            reply_markup=keyboard
        )
        return

    # Завершаем состояние
    await state.clear()

    # Вставляем данные в таблицу direction_list
    direction_status = 'active'
    try:
        insert_direction_list_info(ID, company_name, direction_name, direction_old_price, direction_new_price, direction_status)
        print(f"Данные успешно добавлены: {ID}, {company_name}, {direction_name}, {direction_old_price}, {direction_new_price}, {direction_status}")
    except Exception as e:
        print(f"Ошибка при добавлении данных в таблицу direction_list: {e}")
        await callback_query.message.edit_text("❌ Ошибка при добавлении данных. Попробуйте позже.")
        return

    # Уведомляем пользователя об успешной записи
    await callback_query.message.edit_text(
        "✅ Хорошо, мы добавили ваше предложение к остальным. Нажмите /start, чтобы вернуться в главное меню."
    )

    # Уведомляем администраторов, менеджеров и пользователей
    notification_text = (
        f"Поставщик предложил цену!\n"
        f"Название компании поставщика: {company_name}\n"
        f"Направление: {direction_name}\n"
        f"Цена: {direction_new_price} тг."
    )

    roles = {
        'admin': get_admins_telegram_ids('admin'),
        'manager': get_manager_telegram_ids('manager'),
        'user': get_users_telegram_ids('user')
    }

    for role, ids in roles.items():
        for user_id in ids:
            try:
                await bot.send_message(
                    int(user_id),
                    notification_text if role != 'user' else (
                        f"Была предложена новая цена\n"
                        f"Направление: {direction_name}\n"
                        f"Цена: {direction_new_price} тг."
                    )
                )
            except aiogram.utils.exceptions.ChatNotFound:
                print(f"Чат не найден для user_id: {user_id}")
            except Exception as e:
                print(f"Произошла ошибка при отправке сообщения пользователю {user_id}: {e}")

# Стейт для отмены отправки цены
@router.callback_query(F.data == 'dont_sent_you_price')
async def cancel_new_direction_price(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text('⛔ Отменено')

#### Закрытие направления ####

# Получаем список всех направлений для закрытия
@router.callback_query(F.data == 'close_direction')
async def close_direction(callback_query: types.CallbackQuery):
    """
    Обработчик для выбора направления для закрытия.
    """
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] in ['admin', 'manager']:
        all_directions = get_direction()
        print(all_directions)

        # Создаем клавиатуру
        buttons = []
        for direction_name in all_directions:
            button = InlineKeyboardButton(text=direction_name, callback_data=f'cdirection_{direction_name}')
            buttons.append([button])

        get_back_admin = InlineKeyboardButton(text="🔙 Вернуться назад", callback_data='main')
        buttons.append([get_back_admin])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await callback_query.message.edit_text('Выберите направление:', reply_markup=keyboard)
    else:
        await callback_query.message.answer('❌ У вас нет доступа для выполнения этого действия.')

# Получаем информацию о направлении для закрытия
@router.callback_query(F.data.startswith('cdirection_'))
async def get_info_from_direction(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для получения информации о направлении перед закрытием.
    """
    direction_name_for_close = callback_query.data.replace('cdirection_', '')
    print(f"Попытка закрыть направление - {direction_name_for_close}")

    # Обновляем данные состояния
    await state.update_data(direction_name_for_close=direction_name_for_close)

    print(f"Состояние установлено: {direction_name_for_close}")
    await state.set_state(CloseDirection.chooseDirectionForClose)

    all_users = await get_direction_winner()
    print(f"Список возможных победителей: {all_users}")

    # Создаем клавиатуру
    buttons = []
    for winner in all_users:
        button = InlineKeyboardButton(text=winner, callback_data=f"winners_{winner}")
        buttons.append([button])

    get_back_admin = InlineKeyboardButton(text="🔙 Вернуться назад", callback_data='main')
    buttons.append([get_back_admin])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback_query.message.edit_text("Выберите победителя направления:", reply_markup=keyboard)

# Получаем информацию о победителе направления
@router.callback_query(F.data.startswith("winners_"), StateFilter(CloseDirection.chooseDirectionForClose))
async def accept_direction_winner(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для выбора победителя направления.
    """
    winner_name = callback_query.data.replace("winners_", "")

    # Обновляем данные состояния
    await state.update_data(direction_winner_name=winner_name)

    # Получаем данные из состояния
    data = await state.get_data()
    direction_name = data.get("direction_name_for_close")

    if not direction_name:
        await callback_query.message.edit_text("❌ Ошибка: данные направления не найдены.")
        return

    # Создание клавиатуры
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, закрыть данное направление", callback_data="yes_close_direction")],
        [InlineKeyboardButton(text="❌ Нет, не закрывать", callback_data="main")]
    ])

    # Отправка сообщения с подтверждением
    await callback_query.message.edit_text(
        f"Вы хотите закрыть направление:\nНазвание: {direction_name}\nПобедитель: {winner_name}\nВсе верно?",
        reply_markup=keyboard
    )

    # Устанавливаем состояние
    await state.set_state(CloseDirection.chooseDirectionWinner)

# Подтверждение закрытия направления
@router.callback_query(F.data == 'yes_close_direction', StateFilter(CloseDirection.chooseDirectionWinner))
async def accept_close_direction(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для закрытия направления.
    """
    ID = callback_query.from_user.id
    user_data = get_user_data_by_id(ID)
    username_who_close = user_data[2]

    # Получаем данные из состояния
    data = await state.get_data()
    direction_name_for_close = data.get('direction_name_for_close')
    direction_winner_name = data.get('direction_winner_name')

    # Очищаем состояние
    await state.clear()

    # Получаем цену для закрытия
    print(f"Проверка цены для направления: {direction_name_for_close}, компании: {direction_winner_name}")
    price_mass = chek_price_to_report(direction_name_for_close, direction_winner_name)
    print(f"Проверка цены для отчета: direction={direction_name_for_close}, company_name={direction_winner_name}")

    if price_mass:
        price = ''.join(filter(str.isdigit, price_mass[0]))
        try:
            print(f"Вызов update_price с аргументами: price={price}, direction_name={direction_name_for_close}, winner_name={direction_winner_name}")
            update_price_new(str(price), direction_name_for_close, direction_winner_name)
            print(price, 'ЦЕНА ЗАКРЫТИЯ НАПРАВЛЕНИЯ')
        except Exception as e:
            print(f"Ошибка при обновлении цены: {e}")
            await callback_query.message.edit_text("❌ Ошибка при обновлении цены.")
            return
    else:
        print(f"Компания {direction_winner_name} не предлагала цену для направления {direction_name_for_close}")

    # Закрытие направления
    await close_direction_set_status(direction_name_for_close)
    await close_direction_set_who_close_direction(username_who_close, direction_name_for_close)
    set_winner_name(direction_winner_name, direction_name_for_close)
    await set_winner_name_report(direction_winner_name, direction_name_for_close)

    # Устанавливаем, кто закрыл направление
    set_who_close_direction_username(username_who_close, direction_name_for_close)

    # Получаем финальную цену для отчета
    price_for_close = await report_close_get_price(direction_name_for_close, direction_winner_name)
    print(price_for_close, 'цена для закрытия направления')

    # Закрываем направление в базе
    close_direction_l(direction_name_for_close)

    # Уведомляем победителя
    winner_id = await get_telegram_id_company(direction_winner_name)
    winners = await get_telegram_id_by_comapny(direction_winner_name)
    print(f"ID победителя: {winner_id}, Telegram ID победителей: {winners}")
        # Уведомляем победителя
    if winner_id:
        try:
            await bot.send_message(
                int(winner_id),
                f"Поздравляем, Вы выиграли следующее направление - {direction_name_for_close}"
            )
        except TelegramBadRequest as e:
            print(f"Ошибка при отправке сообщения победителю {winner_id}: {e}")
    else:
        print(f"Ошибка: ID победителя для компании {direction_winner_name} не найден.")

    # Уведомление о закрытии
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data='main')]
    ])
    await callback_query.message.edit_text(f"✅ Направление {direction_name_for_close} было закрыто.", reply_markup=keyboard)

    # Уведомление победителя
    for winner in winners:
        try:
            await bot.send_message(
                int(winner),
                f"Поздравляем, Вы выиграли следующее направление - {direction_name_for_close}"
            )
        except TelegramBadRequest as e:
            print(f"Ошибка при отправке сообщения победителю {winner}: {e}")

    # Уведомление администраторов и менеджеров
    admin_and_manager_ids = await get_admin_and_managers_ids()
    for admin_id in admin_and_manager_ids:
        try:
            await bot.send_message(
                int(admin_id),
                f"Было закрыто следующее направление:\n"
                f"Название: {direction_name_for_close}\n"
                f"Победитель: {direction_winner_name}\n"
                f"Цена закрытия: {price_for_close if price_for_close else 'не указана'}"
            )
        except TelegramBadRequest as e:
            print(f"Ошибка при отправке сообщения администратору/менеджеру {admin_id}: {e}")

    # Уведомление всех пользователей
    user_role = 'user'
    user_telegram_ids = get_users_telegram_ids(user_role)
    for user_id in user_telegram_ids:
        try:
            await bot.send_message(
                int(user_id),
                f"Было закрыто следующее направление:\n{direction_name_for_close}"
            )
        except TelegramBadRequest as e:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    # Уведомление всех пользователей
    direction_description = "Описание направления отсутствует"
    direction_info = get_direction_info(direction_name_for_close)
    if direction_info:
        direction_description = direction_info[4]  # Предположительно, описание находится в 5-м элементе

    await notify_users_about_direction_closure(
        direction_name_for_close,
        direction_description,
        int(price_for_close) if price_for_close else 0,
        direction_winner_name
    )
# Уведомление пользователей о закрытии направления
async def notify_users_about_direction_closure(direction_name: str, direction_description: str, final_price: int, winner_name: str):
    """
    Уведомляет пользователей с ролью user о закрытии направления.
    """
    user_ids = get_users_telegram_ids('user')

    notification_text = (
        f"📢 Направление закрыто!\n"
        f"Название: {direction_name}\n"
        f"Описание: {direction_description}\n"
        f"Победитель: {winner_name}\n"
        f"Финальная цена: {final_price} тг."
    )

    # Отправляем уведомления асинхронно
    tasks = []
    for user_id in user_ids:
        tasks.append(bot.send_message(user_id, notification_text))

    # Запускаем все задачи параллельно
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Логируем ошибки, если они есть
    for user_id, result in zip(user_ids, results):
        if isinstance(result, Exception):
            print(f"Ошибка при отправке сообщения пользователю {user_id}: {result}")

#### Получение списка направлений, на которые я откликнулся ####

@router.callback_query(F.data == 'list_my_direction', StateFilter('*'))
async def get_list_my_direvtion(callback_query: types.CallbackQuery):
    """
    Обработчик для отображения списка направлений, на которые откликнулся пользователь,
    с возможностью обновления цены.
    """
    ID = callback_query.from_user.id

    # Получаем информацию о компании пользователя
    company_info = get_user_data_by_id(ID)
    if not company_info or len(company_info) < 6:
        await callback_query.message.edit_text("❌ Ошибка: информация о компании не найдена.")
        return

    company_name = company_info[5]  # Название компании
    print(f"Информация о компании: {company_info}")
    print(f"Название компании: {company_name}")

    # Получаем направления пользователя
    try:
        my_directions = select_my_direction(company_name)
        print(f"Направления компании {company_name}: {my_directions}")
    except Exception as e:
        print(f"Ошибка при выполнении select_my_direction: {e}")
        await callback_query.message.edit_text("❌ Ошибка при получении направлений. Попробуйте позже.")
        return

    # Проверяем, есть ли направления
    if not my_directions:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='main')]
        ])
        await callback_query.message.edit_text(
            "❌ У вас пока нет активных направлений, на которые вы откликнулись.",
            reply_markup=keyboard
        )
        return

    # Создаем клавиатуру с направлениями и текущими ценами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for direction_name in my_directions:
        # Получаем текущую цену для направления
        direction_info = select_my_directionlist(direction_name, ID)
        if direction_info:
            current_price = direction_info[0][1]  # Извлекаем текущую цену
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{direction_name} - {current_price} тг",
                    callback_data=f'update_price_{direction_name}'
                )
            ])

    # Добавляем кнопку возврата
    keyboard.inline_keyboard.append(
        [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='main')]
    )

    # Отправляем сообщение с клавиатурой
    await callback_query.message.edit_text(
        "🗺 Вот список направлений, на которые вы откликнулись (с текущими ценами):",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith('update_price_'), StateFilter('*'))
async def update_price(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для выбора направления и отображения клавиатуры с кнопкой обновления цены.
    """
    ID = callback_query.from_user.id
    data = callback_query.data.split('_')  # Пример callback_data: update_price_НазваниеНаправления
    direction_name = '_'.join(data[2:])  # Извлекаем название направления

    # Получаем текущую цену
    direction_info = select_my_directionlist(direction_name, ID)
    if not direction_info:
        await callback_query.message.edit_text("❌ Ошибка: направление не найдено или у вас нет доступа.")
        return

    current_price = direction_info[0][1]  # Извлекаем текущую цену
    await state.update_data(direction_name=direction_name)

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💵 Обновить цену', callback_data='update_you_price')],
        [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='main')]
    ])

    # Отправляем сообщение с клавиатурой
    await callback_query.message.edit_text(
        f"Текущая цена для направления '{direction_name}': {current_price} тг.",
        reply_markup=keyboard
    )

# Запрос новой цены
@router.callback_query(F.data == 'update_you_price', StateFilter('*'))
async def update_you_price(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для запроса новой цены на направление.
    """
    # Получаем данные из состояния
    data = await state.get_data()
    direction_name = data.get('direction_name')

    if not direction_name:
        await callback_query.message.edit_text("❌ Ошибка: данные о направлении не найдены.")
        return

    # Устанавливаем состояние для ввода новой цены
    await state.set_state("awaiting_new_price")

    # Запрашиваем новую цену у пользователя
    await callback_query.message.edit_text(
        f"💲 Введите новую цену для направления: {direction_name}"
    )

# Подтверждение новой цены
@router.message(StateFilter("awaiting_new_price"))
async def set_new_price(message: types.Message, state: FSMContext):
    """
    Обработчик для ввода новой цены и отображения клавиатуры для подтверждения.
    """
    if not message.text.isdigit():
        await message.answer("❌ Ошибка: цена должна быть числом. Попробуйте снова.")
        return

    new_price = int(message.text)
    if new_price <= 0:
        await message.answer("❌ Ошибка: цена должна быть больше 0. Попробуйте снова.")
        return

    # Получаем данные о направлении из состояния
    data = await state.get_data()
    direction_name = data.get('direction_name')

    if not direction_name:
        await message.answer("❌ Ошибка: данные о направлении не найдены.")
        return

    # Получаем текущую цену для направления
    user_id = message.from_user.id
    direction_info = select_my_directionlist(direction_name, user_id)
    if not direction_info:
        await message.answer("❌ Ошибка: информация о направлении не найдена.")
        return

    current_price = int(direction_info[0][1])  # Текущая цена

    # Проверяем, что новая цена меньше текущей
    if new_price >= current_price:
        await message.answer(
            f"❌ Ошибка: новая цена должна быть меньше текущей ({current_price} тг). Попробуйте снова."
        )
        return

    # Сохраняем новую цену в состоянии
    await state.update_data(new_price=new_price)

    # Создаем клавиатуру для подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='yes_update_user_price')],
        [InlineKeyboardButton(text='❌ Отмена', callback_data='main')]
    ])

    # Отправляем сообщение с подтверждением
    await message.answer(
        f"Вы хотите подтвердить новую цену {new_price} тг?",
        reply_markup=keyboard
    )

# Подтверждение новой цены
@router.callback_query(F.data.startswith('mydirection_'), StateFilter('*'))
async def get_list_my_direvtion(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для отображения деталей направления, на которое откликнулся пользователь.
    """
    ID = callback_query.from_user.id

    # Получаем данные пользователя
    user_data = get_user_data_by_id(ID)
    if not user_data:
        await callback_query.message.edit_text("❌ Ошибка: данные пользователя не найдены.")
        return

    # Получаем название направления из callback_data
    direction_name = callback_query.data.replace('mydirection_', '').strip()
    print(f"Название направления: {direction_name}")

    # Получаем информацию о направлении
    direction_info = get_direction_info(direction_name)
    if not direction_info:
        await callback_query.message.edit_text("❌ Ошибка: информация о направлении не найдена.")
        return

    # Получаем информацию о компании пользователя
    company_name = user_data[5]  # Название компании
    direction_price_new = get_my_price_for_direction(company_name, direction_info[3])
    direction_price_new = direction_price_new[0] if direction_price_new else "не указана"

    print(f"{user_data[2]} перешел в направление - {direction_info[3]}")

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💵 Обновить цену', callback_data='update_you_price')],
        [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='main')]
    ])

    # Сохраняем данные в состоянии
    await state.update_data(
        direction_name_for_update=direction_info[3],
        direction_direction_id=direction_info[1]
    )

    # Отправляем сообщение с информацией о направлении
    await callback_query.message.edit_text(
        f"⚠ Вот информация по данному направлению:\n"
        f"Название: {direction_info[3]}, ID: {direction_info[1]}\n"
        f"Подробное описание: {direction_info[4]}\n"
        f"Начальная цена: {direction_info[5]}\n"
        f"Цена, которую вы предложили: {direction_price_new}",
        reply_markup=keyboard
    )

    # Устанавливаем состояние
    await state.set_state(UpdateDirectionNewPrice.getDirectionInfo)
    print("Состояние UpdateDirectionNewPrice.getDirectionInfo установлено.")


@router.callback_query(F.data == 'update_you_price', StateFilter(UpdateDirectionNewPrice.getDirectionInfo))
async def update_you_price(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для запроса новой цены на направление.
    """
    ID = callback_query.from_user.id

    # Получаем данные из состояния
    data = await state.get_data()
    direction_name = data.get('direction_name_for_update')

    if not direction_name:
        await callback_query.message.edit_text("❌ Ошибка: данные о направлении не найдены.")
        return

    print(f"Пользователь {ID} обновляет цену для направления: {direction_name}")

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='list_my_direction')]
    ])

    # Устанавливаем состояние для следующего шага
    await state.set_state(SentDirectionPrice.enterNewDirectionPrice)
    current_state = await state.get_state()
    print(f"Состояние установлено: {current_state}")

    # Запрашиваем новую цену у пользователя
    await callback_query.message.edit_text(
        f"💲 Введите новую цену для направления: {direction_name}",
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'yes_update_user_price', StateFilter('*'))
async def confirm_new_price(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для подтверждения новой цены и уведомления пользователей.
    """
    # Получаем данные из состояния
    data = await state.get_data()
    new_price = data.get('new_price')
    direction_name = data.get('direction_name')

    if not new_price or not direction_name:
        await callback_query.message.edit_text("❌ Ошибка: данные о направлении или цене не найдены.")
        return

    # Обновляем цену в базе данных
    telegram_id = callback_query.from_user.id
    try:
        update_direction_price(direction_name, telegram_id, new_price)
        print(f"Цена для направления '{direction_name}' успешно обновлена на {new_price} тг.")
    except Exception as e:
        print(f"Ошибка при обновлении цены: {e}")
        await callback_query.message.edit_text("❌ Ошибка при обновлении цены. Попробуйте позже.")
        return

    # Уведомляем пользователя об успешном обновлении
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Вернуться к списку направлений', callback_data='list_my_direction')],
        [InlineKeyboardButton(text='🔝 В главное меню', callback_data='main')]
    ])
    await callback_query.message.edit_text(
        f"✅ Цена для направления '{direction_name}' успешно обновлена на {new_price} тг.",
        reply_markup=keyboard
    )

    # Уведомляем администраторов, менеджеров и пользователей
    try:
        company_name = get_user_data_by_id(telegram_id)[5]  # Получаем название компании
        notification_text_admin_manager = (
            f"📢 Поставщик обновил цену на направление:\n"
            f"Компания: {company_name}\n"
            f"Направление: {direction_name}\n"
            f"Новая цена: {new_price} тг."
        )
        notification_text_user = (
            f"📢 Один из поставщиков обновил цену:\n"
            f"Направление: {direction_name}\n"
            f"Новая цена: {new_price} тг."
        )

        admins_id = get_admins_telegram_ids('admin')
        managers_id = get_manager_telegram_ids('manager')
        users_id = get_users_telegram_ids('user')

        # Уведомляем администраторов
        for admin_id in admins_id:
            try:
                await bot.send_message(admin_id, notification_text_admin_manager)
            except Exception as e:
                print(f"Ошибка при отправке сообщения администратору {admin_id}: {e}")

        # Уведомляем менеджеров
        for manager_id in managers_id:
            try:
                await bot.send_message(manager_id, notification_text_admin_manager)
            except Exception as e:
                print(f"Ошибка при отправке сообщения менеджеру {manager_id}: {e}")

        # Уведомляем пользователей
        for user_id in users_id:
            try:
                await bot.send_message(user_id, notification_text_user)
            except Exception as e:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    except Exception as e:
        print(f"Ошибка при отправке уведомлений: {e}")

    # Завершаем состояние
    await state.clear()

@router.callback_query(F.data == 'list_of_suppliers')
async def get_all_username(callback_query: types.CallbackQuery):
    """
    Обработчик для отображения списка поставщиков.
    """
    ID = callback_query.from_user.id

    # Получаем данные пользователя
    user_id = await get_telegram_id_user(ID)
    user_role = get_user_role(ID)
    user_data = get_user_data_by_id(ID)
    if not user_role:
        await callback_query.message.edit_text("Ошибка: роль пользователя не найдена.")
        return

    # Проверяем роль пользователя
    if user_role[0] in ['admin', 'manager']:
        # Создаем клавиатуру для возврата
        get_main = InlineKeyboardButton(text='🔙 Вернуться назад', callback_data='main')
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[get_main]])

        # Получаем список всех пользователей
        all_usernames = await get_all_users()
        if not all_usernames:
            await callback_query.message.edit_text("Список поставщиков пуст.", reply_markup=keyboard)
            return

        # Форматируем данные для отображения
        formatted_data = "\n\n".join([
            f"👤 Имя: {name}\n"
            f"🆔 ID: {telegram_id}\n"
            f"🏢 Компания: {company}\n"
            f"📞 Телефон: {phone}"
            for telegram_id, name, company, phone in all_usernames
        ])

        # Отправляем сообщение с данными
        await callback_query.message.edit_text(
            f"📜 Список поставщиков:\n\n{formatted_data}",
            reply_markup=keyboard
        )
        print(f"Отформатированный список поставщиков:\n{formatted_data}")
    else:
        await callback_query.message.edit_text("У вас нет прав для выполнения этого действия.")
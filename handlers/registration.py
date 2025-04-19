from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states.states import RegistrationState
from db.users import (
    add_user, get_user_role, get_user_data_by_id
)
from db.ban_list import get_ban_ids

ID = None

router = Router()

async def chek_ban():
    ban_list = await get_ban_ids()
    for cheked_ids in ban_list:
        print(f"all banned ids {cheked_ids}")
        return cheked_ids


@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    """
    Обработчик команды /start.
    """
    ID = message.from_user.id

    # Получаем данные пользователя и бан-лист
    user_data = get_user_data_by_id(ID)  # Проверяем наличие пользователя в базе данных
    user_role = get_user_role(ID)  # Получаем роль пользователя
    ban_list = await get_ban_ids()  # Получаем список заблокированных пользователей

    print(f"Пользователь ID: {ID}, Роль: {user_role}, Данные: {user_data}, Бан-лист: {ban_list}")

    await state.clear()

    # Проверяем, находится ли пользователь в бан-листе
    if ID in ban_list:
        await message.answer("❌ Ты забанен админом.")
        return

    # Если пользователь не найден в базе данных, начинаем регистрацию
    if not user_data:
        print("Пользователь не зарегистрирован. Начинаем регистрацию.")
        await message.answer("✒ Введите ваше ФИО:")
        await state.set_state(RegistrationState.WaitingForName)
        return

    # Если пользователь найден, определяем его роль
    if user_role[0] == 'admin':
        # Меню для администратора
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📜 Список поставщиков', callback_data='list_of_suppliers')],
            [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
            [InlineKeyboardButton(text='📖 Открыть направление', callback_data='open_direction')],
            [InlineKeyboardButton(text='📕 Закрыть направление', callback_data='close_direction')],
            [InlineKeyboardButton(text='🖊 Управление пользователями', callback_data='user_settings')],
            [InlineKeyboardButton(text='📑 Сформировать отчет', callback_data='get_report')]
        ])
        await message.answer("👋 Привет, админ!", reply_markup=keyboard)
        print(f"Админ {user_data[2]} авторизовался.")  # Предполагается, что имя пользователя хранится во 2-м столбце

    elif user_role[0] == 'manager':
        # Меню для менеджера
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📜 Список поставщиков', callback_data='list_of_suppliers')],
            [InlineKeyboardButton(text='📖 Открыть направление', callback_data='open_direction')],
            [InlineKeyboardButton(text='📕 Закрыть направление', callback_data='close_direction')],
            [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
            [InlineKeyboardButton(text='📑 Сформировать отчет', callback_data='get_report')]
        ])
        await message.answer("👋 Привет, Менеджер!", reply_markup=keyboard)
        print(f"Менеджер {user_data[2]} авторизовался.")  # Предполагается, что имя пользователя хранится во 2-м столбце

    else:
        # Меню для обычного пользователя
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🚹 Мой профиль', callback_data='my_profile')],
            [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
            [InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')],
        ])
        await message.answer(f"👋 Здравствуйте, {user_data[2]}!", reply_markup=keyboard)  # Имя пользователя во 2-м столбце


@router.message(F.text.startswith('/') == False, StateFilter(RegistrationState.WaitingForName))
async def get_name(message: types.Message, state: FSMContext):
    """
    Обработчик для получения имени пользователя.
    """
    await state.update_data(name=message.text.strip())
    await message.answer('✒ Введите название компании:')
    await state.set_state(RegistrationState.WaitingForCompanyName)


@router.message(F.text.startswith('/') == False, StateFilter(RegistrationState.WaitingForCompanyName))
async def get_company(message: types.Message, state: FSMContext):
    """
    Обработчик для получения названия компании.
    """
    await state.update_data(company=message.text.strip())
    await message.answer("✒ Отлично! Теперь введите ваш номер телефона:")
    await state.set_state(RegistrationState.WaitingForPhone)


@router.message(F.text.startswith('/') == False, StateFilter(RegistrationState.WaitingForPhone))
async def get_phone(message: types.Message, state: FSMContext):
    """
    Обработчик для получения номера телефона и завершения регистрации.
    """
    await state.update_data(phone=message.text.strip())

    # Получаем данные из состояния
    data = await state.get_data()
    ID = message.from_user.id
    name = data['name']
    company_name = data['company']
    phone = data['phone']
    telegram_frist_name = message.from_user.first_name or "Не указано"
    telegram_second_name = message.from_user.last_name or "Не указано"

    print(f"📗 ID: {ID}\nName: {name}\nCompany name: {company_name}\nPhone number: {phone}\n"
          f"Telegram First Name: {telegram_frist_name}\nTelegram Last Name: {telegram_second_name}")

    # Клавиатура для подтверждения данных
    accept = InlineKeyboardButton(text='✅ Продолжить', callback_data='accept_user_data')
    not_accept = InlineKeyboardButton(text='🔄 Нет, заполнить данные сначала', callback_data='renew_user_data')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[accept, not_accept]])

    user_info = f"Имя: {name}\nКомпания: {company_name}\nНомер телефона: {phone}"
    await message.answer(f"Подтвердите корректность данных:\n\n{user_info}", reply_markup=keyboard)

    print('Добавляем пользователя в БД')
    user_role = 'user'

    # Добавление пользователя в базу данных
    try:
        add_user(ID, name, telegram_frist_name, telegram_second_name, company_name, phone, user_role)
        print(f"Пользователь {name} успешно добавлен в базу данных.")
    except Exception as e:
        print(f"Ошибка при добавлении пользователя в базу данных: {e}")

    await state.clear()


@router.callback_query(F.data == "accept_user_data")
async def accept_registration(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для подтверждения регистрации.
    """
    # Получаем данные из состояния
    data = await state.get_data()
    ID = callback_query.from_user.id
    name = data.get("name", "Не указано")
    company_name = data.get("company", "Не указано")
    phone = data.get("phone", "Не указано")
    telegram_frist_name = callback_query.from_user.first_name or "Не указано"
    telegram_second_name = callback_query.from_user.last_name or "Не указано"

    # Добавление пользователя в базу данных
    try:
        add_user(ID, name, telegram_frist_name, telegram_second_name, company_name, phone, "user")
        print(f"Пользователь {name} успешно зарегистрирован.")
    except Exception as e:
        print(f"Ошибка при добавлении пользователя в базу данных: {e}")
        await callback_query.message.edit_text("❌ Ошибка при регистрации. Попробуйте позже.")
        return

    # Создаём клавиатуру для завершения регистрации
    my_profile = InlineKeyboardButton(text='🚹 Мой профиль', callback_data='my_profile')
    list_my_direction = InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')
    list_direction = InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [my_profile],
        [list_direction],
        [list_my_direction]
    ])

    # Завершаем регистрацию
    await callback_query.message.edit_text("✅ Регистрация успешно завершена!", reply_markup=keyboard)
    await state.clear()
from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from db.users import (
    get_user_role, get_all_username_without_you_id, check_user_correct_username,
    get_id_by_username, remove_user, update_user_name,
    check_user_correct_username_manger, update_company_name,
    get_telegram_id_user, get_user_data_by_id, get_managers, update_user_role,
    delete_managers_role, get_user_role_username, new_manager, update_phone_number
)
from db.ban_list import insert_id_to_ban_list
from states.states import CreateNewManager, ChangeUserNmae, ChangeUserCompany, ChnageUserPhone
from os import getenv
from dotenv import load_dotenv

load_dotenv()

ADMINS = getenv("ADMINS").split(',')

ID = None

router = Router()

@router.callback_query(F.data == 'user_settings')
async def user_settings(callback_query: types.CallbackQuery):
    """
    Обработчик для управления пользователями.
    Доступен только для администраторов.
    """
    ID = callback_query.from_user.id
    user_id = get_telegram_id_user(ID)  # Добавлено await
    user_role = get_user_role(ID)  # Добавлено await
    user_data = get_user_data_by_id(ID)  # Добавлено await

    if user_role and user_role[0] == 'admin':
        # Создаем кнопки для меню управления пользователями
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🚻 Список поставщиков', callback_data='list_of_suppliers')],
            [InlineKeyboardButton(text='🛂 Показать список всех менеджеров и админов', callback_data='get_all_managers_list')],
            [InlineKeyboardButton(text='🛄 Добавить пользователя в менеджеры', callback_data='add_new_manager')],
            [InlineKeyboardButton(text='⛔ Удалить менеджера', callback_data='rm_old_manager')],
            [InlineKeyboardButton(text='❗️ Удалить пользователя', callback_data='deactivate_user')],
            [InlineKeyboardButton(text='🔚 Вернуться в главное меню', callback_data='main')]
        ])

        # Отправляем сообщение с меню
        await callback_query.message.edit_text('📝 Выберите нужный вариант', reply_markup=keyboard)
    else:
        # Если пользователь не администратор
        await callback_query.message.edit_text('❌ У вас нет прав')

@router.callback_query(F.data == 'user_settings')
async def return_to_user_settings(callback_query: types.CallbackQuery):
    """
    Возврат в меню управления пользователями.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton('🚻 Список поставщиков', callback_data='list_of_suppliers'),
        types.InlineKeyboardButton('🛂 Показать список всех менеджеров и админов', callback_data='get_all_managers_list'),
        types.InlineKeyboardButton('🛄 Добавить пользователя в менеджеры', callback_data='add_new_manager'),
        types.InlineKeyboardButton('⛔ Удалить менеджера', callback_data='rm_old_manager'),
        types.InlineKeyboardButton('❗️ Удалить пользователя', callback_data='deactivate_user'),
        types.InlineKeyboardButton('🔚 Вернуться в главное меню', callback_data='user_settings')
    )
    await callback_query.message.edit_text("Выберите нужный вариант:", reply_markup=keyboard)

# Обработчик: Удаление пользователя
@router.callback_query(F.data == 'deactivate_user')
async def show_users_for_removal(callback_query: types.CallbackQuery):
    """
    Отображение списка пользователей для удаления.
    """
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        # Получаем список пользователей
        users = await get_all_username_without_you_id(ID)
        if not users:
            await callback_query.message.edit_text("❌ Список пользователей пуст.")
            return

        # Создаём список кнопок
        buttons = [
            [InlineKeyboardButton(text=f"{name}", callback_data=f"confirm_remove_user:{name}")]
            for name in users
        ]

        # Добавляем кнопку для возврата
        buttons.append([InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="user_settings")])

        # Создаём клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Отправляем сообщение с клавиатурой
        await callback_query.message.edit_text("📝 Выберите пользователя для удаления:", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

@router.callback_query(F.data.startswith("confirm_remove_user:"))
async def confirm_remove_user(callback_query: types.CallbackQuery):
    """
    Подтверждение удаления пользователя.
    """
    username = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        # Создаём кнопки подтверждения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Да, удалить {username}", callback_data=f"delete_user:{username}")],
            [InlineKeyboardButton(text="❌ Нет, вернуться назад", callback_data="deactivate_user")]
        ])
        await callback_query.message.edit_text(f"🛂 Вы хотите удалить пользователя {username}?", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

@router.callback_query(F.data.startswith("delete_user:"))
async def delete_user(callback_query: types.CallbackQuery):
    """
    Удаление пользователя.
    """
    username = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        try:
            # Удаляем пользователя
            
            user_id = await get_id_by_username(username)
            await insert_id_to_ban_list(user_id[0])  # Добавляем в бан-лист
            await remove_user(username)  # Удаляем из базы
            await callback_query.message.edit_text(f"✅ Пользователь {username} успешно удалён.")
        except Exception as e:
            await callback_query.message.edit_text(f"❌ Ошибка при удалении пользователя: {e}")
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

# Обработчик: Подтверждение удаления менеджера
@router.callback_query(F.data.startswith("delete_user:"))
async def delete_user(callback_query: types.CallbackQuery):
    """
    Удаление пользователя.
    """
    username = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        try:
            # Проверяем корректность имени пользователя
            is_valid_user = await check_user_correct_username(username)
            if not is_valid_user:
                await callback_query.message.edit_text(f"❌ Пользователь с именем {username} не найден.")
                return

            # Удаляем пользователя
            user_id = await get_id_by_username(username)
            await insert_id_to_ban_list(user_id[0])  # Добавляем в бан-лист
            await remove_user(username)  # Удаляем из базы
            await callback_query.message.edit_text(f"✅ Пользователь {username} успешно удалён.")
        except Exception as e:
            await callback_query.message.edit_text(f"❌ Ошибка при удалении пользователя: {e}")
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

# Обработчик: Отображение списка менеджеров для удаления
@router.callback_query(F.data == 'rm_old_manager')
async def show_managers_for_removal(callback_query: types.CallbackQuery):
    """
    Отображение списка менеджеров для удаления.
    """
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        managers = await get_managers()
        if not managers:
            await callback_query.message.edit_text("❌ Список менеджеров пуст.")
            return

        # Создаём список кнопок
        buttons = [
            [InlineKeyboardButton(text=f"{name} (ID: {telegram_id})", callback_data=f"confirm_remove:{name}")]
            for telegram_id, name, role in managers
        ]

        # Добавляем кнопку для возврата
        buttons.append([InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="user_settings")])

        # Создаём клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Отправляем сообщение с клавиатурой
        await callback_query.message.edit_text("📝 Выберите менеджера для удаления:", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

@router.callback_query(F.data.startswith("delete_manager:"))
async def delete_manager(callback_query: types.CallbackQuery):
    """
    Удаление менеджера.
    """
    manager_name = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        try:
            # Проверяем корректность имени менеджера
            is_valid_manager = await check_user_correct_username_manger(manager_name)
            if not is_valid_manager:
                await callback_query.message.edit_text(f"❌ Менеджер с именем {manager_name} не найден.")
                return

            # Удаляем менеджера
            await delete_managers_role('user', manager_name)
            await callback_query.message.edit_text(f"✅ Менеджер {manager_name} успешно удалён.")
        except Exception as e:
            await callback_query.message.edit_text(f"❌ Ошибка при удалении менеджера: {e}")
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

# Обработчик: Завершение удаления менеджера
@router.callback_query(F.data.startswith("confirm_remove:"))
async def confirm_remove_manager(callback_query: types.CallbackQuery):
    """
    Подтверждение удаления менеджера.
    """
    manager_name = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        # Создаём кнопки подтверждения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Да, удалить {manager_name}", callback_data=f"delete_manager:{manager_name}")],
            [InlineKeyboardButton(text="❌ Нет, вернуться назад", callback_data="rm_old_manager")]
        ])
        await callback_query.message.edit_text(f"🛂 Вы хотите удалить менеджера {manager_name}?", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

# Обработчик: Список менеджеров и администраторов
@router.callback_query(F.data == 'get_all_managers_list')
async def list_managers(callback_query: types.CallbackQuery):
    """
    Отображение списка всех менеджеров и администраторов.
    """
    ID = callback_query.from_user.id
    user_id = await get_telegram_id_user(ID)
    user_role = get_user_role(ID)
    user_data = get_user_data_by_id(ID)

    if user_role and user_role[0] == 'admin':
        # Получаем список менеджеров и администраторов
        all_managers = await get_managers()
        if not all_managers:
            await callback_query.message.edit_text("❌ Список менеджеров и администраторов пуст.")
            return

        # Форматируем список для красивого вывода
        formatted_data = "\n".join([
            f"👤 <b>{username}</b>\n🆔 ID: <code>{telegram_id}</code>\n🔖 Роль: <i>{role}</i>\n"
            for telegram_id, username, role in all_managers
        ])

        # Создаём кнопки для возврата
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="user_settings")]
        ])

        # Отправляем сообщение с форматированным текстом
        await callback_query.message.edit_text(
            f"<b>Список менеджеров и администраторов:</b>\n\n{formatted_data}",
            reply_markup=keyboard,
            parse_mode="HTML"  # Используем HTML для форматирования текста
        )
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")


@router.callback_query(F.data == 'main')
async def get_to_main(callback_query: types.CallbackQuery):
    """
    Обработчик для возврата в главное меню.
    Меню зависит от роли пользователя: администратор, менеджер или пользователь.
    """
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        # Меню для администратора
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📜 Список поставщиков', callback_data='list_of_suppliers')],
            [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
            [InlineKeyboardButton(text='📖 Открыть направление', callback_data='open_direction')],
            [InlineKeyboardButton(text='📕 Закрыть направление', callback_data='close_direction')],
            [InlineKeyboardButton(text='🖊 Управление пользователями', callback_data='user_settings')],
            [InlineKeyboardButton(text='📑 Сформировать отчет', callback_data='get_report')]
        ])
        await callback_query.message.edit_text("Выбери нужный вариант!", reply_markup=keyboard)
        print('Возврат в главное меню администратора')

    elif user_role and user_role[0] == 'manager':
        # Меню для менеджера
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📜 Список поставщиков', callback_data='list_of_suppliers')],
            [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
            [InlineKeyboardButton(text='📖 Открыть направление', callback_data='open_direction')],
            [InlineKeyboardButton(text='📕 Закрыть направление', callback_data='close_direction')],
            [InlineKeyboardButton(text='📑 Сформировать отчет', callback_data='get_report')]
        ])
        await callback_query.message.edit_text("Выбери нужный вариант!", reply_markup=keyboard)
        print('Возврат в главное меню менеджера')

    else:
        # Меню для обычного пользователя
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🚹 Мой профиль', callback_data='my_profile')],
            [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
            [InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')]
        ])
        await callback_query.message.edit_text("Выберите нужный вариант", reply_markup=keyboard)
        print(f"Возврат в главное меню пользователя с ролью: {user_role[0] if user_role else 'неизвестно'}")

# Обработчик: Возврат в главное меню администратора
@router.callback_query(F.data == 'get_back_to_admin_menu')
async def get_back_to_admin_menu(callback_query: types.CallbackQuery):
    """
    Возвращает администратора в главное меню.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📜 Список поставщиков', callback_data='list_of_suppliers')],
        [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
        [InlineKeyboardButton(text='📖 Открыть направление', callback_data='open_direction')],
        [InlineKeyboardButton(text='📕 Закрыть направление', callback_data='close_direction')],
        [InlineKeyboardButton(text='🖊 Управление пользователями', callback_data='user_settings')]
    ])
    await callback_query.message.edit_text("Выбери нужный вариант!", reply_markup=keyboard)
    print('Возврат в главное меню администратора')

# Обработчик: Добавление нового менеджера (ввод имени)
@router.callback_query(F.data == 'add_new_manager')
async def show_users_for_manager_addition(callback_query: types.CallbackQuery):
    """
    Отображение списка пользователей с ролью 'user' для назначения менеджером.
    """
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        # Получаем список пользователей с ролью 'user'
        usernames = await get_all_username_without_you_id(ID)  # Возвращает список username
        if not usernames:
            await callback_query.message.edit_text("🚹 Список пользователей с ролью 'user' пуст.")
            return

        # Создаём список кнопок
        buttons = [
            [InlineKeyboardButton(text=username, callback_data=f"confirm_add_manager:{username}")]
            for username in usernames
        ]

        # Добавляем кнопку для возврата
        buttons.append([InlineKeyboardButton(text="🔙 Вернуться назад", callback_data="user_settings")])

        # Создаём клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        # Отправляем сообщение с клавиатурой
        await callback_query.message.edit_text("🚹 Выберите пользователя для назначения менеджером:", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

@router.callback_query(F.data.startswith("confirm_add_manager:"))
async def confirm_add_manager(callback_query: types.CallbackQuery):
    """
    Подтверждение назначения пользователя менеджером.
    """
    telegram_id = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        # Создаём кнопки подтверждения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, назначить менеджером", callback_data=f"add_manager:{telegram_id}")],
            [InlineKeyboardButton(text="❌ Нет, вернуться назад", callback_data="add_new_manager")]
        ])
        await callback_query.message.edit_text(f"🚹 Вы хотите назначить пользователя с ID {telegram_id} менеджером?", reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

@router.callback_query(F.data.startswith("add_manager:"))
async def add_manager(callback_query: types.CallbackQuery):
    """
    Завершение процесса назначения менеджера.
    """
    telegram_id = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        try:
            # Назначаем пользователя менеджером
            await new_manager('manager', telegram_id)
            await callback_query.message.edit_text(f"✅ Пользователь с ID {telegram_id} успешно назначен менеджером.")
        except Exception as e:
            await callback_query.message.edit_text(f"❌ Ошибка при назначении менеджера: {e}")
    else:
        await callback_query.message.edit_text("❌ У вас нет прав.")

# Обработчик: Проверка имени нового менеджера
@router.message(StateFilter(CreateNewManager.enterName))
async def create_new_manager_name(message: types.Message, state: FSMContext):
    """
    Проверяет, можно ли назначить пользователя менеджером.
    """
    # Проверка на команды, начинающиеся с '/'
    if message.text.startswith('/'):
        await message.answer("Имя не должно начинаться с '/', пожалуйста введите корректное имя!")
        await state.set_state(CreateNewManager.enterName)
        return

    # Сохраняем введенное имя в состоянии
    await state.update_data(manager_name=message.text.strip())
    data = await state.get_data()
    username = data['manager_name']

    # Получаем роль пользователя
    old_user_role = await get_user_role_username(username)
    if not old_user_role:
        await message.answer("❌ Пользователь не найден. Проверьте введенные данные.")
        return

    print(f"Роль пользователя: {old_user_role[0]}")
    if old_user_role[0] == 'user':
        new_manager_name = data['manager_name']
        # Создаем кнопки
        yes_create_new_manager = InlineKeyboardButton(
            text=f"Да, сделать {new_manager_name} менеджером",
            callback_data=f"yes_create_new_manager:{new_manager_name}"
        )
        cancel_create_new_manager = InlineKeyboardButton(
            text="Отмена", 
            callback_data="cancel_create_new_manager"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [yes_create_new_manager],
            [cancel_create_new_manager]
        ])

        await message.answer(f"🚹 Вы хотите сделать {new_manager_name} менеджером?", reply_markup=keyboard)
    elif old_user_role[0] == 'manager':
        await message.answer("⚠ Пользователь уже является менеджером.")
    else:
        await message.answer("❌ Ошибка: пользователь не найден или имеет некорректную роль.")

# Обработчик: Подтверждение назначения менеджера
@router.callback_query(F.data.startswith("yes_create_new_manager"))
async def continue_create_new_manager(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Завершает процесс назначения нового менеджера.
    """
    # Извлекаем имя менеджера из callback_data
    new_manager_name = callback_query.data.split(":")[1]
    ID = callback_query.from_user.id
    user_role = get_user_role(ID)

    if user_role and user_role[0] == 'admin':
        await new_manager('manager', new_manager_name)
        print(f"{new_manager_name} стал менеджером")
        await callback_query.message.edit_text(f"✅ {new_manager_name} успешно назначен менеджером.")
        await state.clear()
    else:
        await callback_query.message.edit_text('❌ У вас нет прав.')

# Обработчик: Отмена назначения менеджера
@router.callback_query(F.data == "cancel_create_new_manager")
async def cancel_create_manager(callback_query: types.CallbackQuery):
    """
    Отменяет процесс назначения нового менеджера.
    """
    await callback_query.message.edit_text("❌ Процесс назначения менеджера отменен.")

# Обработчик: Завершение регистрации
@router.callback_query(F.data == 'accept_user_data')
async def accept_registration(callback_query: types.CallbackQuery):
    """
    Завершение регистрации пользователя.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚹 Мой профиль', callback_data='my_profile')],
        [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
        [InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')]
    ])
    await callback_query.message.edit_text("✅ Регистрация успешно завершена!", reply_markup=keyboard)

# Обработчик: Просмотр профиля пользователя
@router.callback_query(F.data == 'my_profile')
async def get_my_profile(callback_query: types.CallbackQuery):
    """
    Отображение профиля пользователя.
    """
    ID = callback_query.from_user.id
    user_data = get_user_data_by_id(ID)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Редактировать данные', callback_data='change_user_data')],
        [InlineKeyboardButton(text='🔚 Вернуться в начало', callback_data='accept_user_data')]
    ])
    await callback_query.message.edit_text(
        f"🚹 Твое ФИО: {user_data[2]}\n🏢 Твоя компания: {user_data[5]}\n📞 Твой номер телефона: {user_data[6]}",
        reply_markup=keyboard
    )

# Обработчик: Меню изменения данных пользователя
@router.callback_query(F.data == 'change_user_data')
async def change_user_data(callback_query: types.CallbackQuery):
    """
    Меню для изменения данных пользователя.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🖊 Изменить ФИО', callback_data='change_user_name')],
        [InlineKeyboardButton(text='🖊 Изменить название компании', callback_data='change_company')],
        [InlineKeyboardButton(text='🖊 Изменить номер телефона', callback_data='change_phone')],
        [InlineKeyboardButton(text='🔚 Вернуться в начало', callback_data='accept_user_data')]
    ])
    await callback_query.message.edit_text("❓ Что нужно изменить?", reply_markup=keyboard)

# Обработчик: Изменение ФИО
@router.callback_query(F.data == 'change_user_name')
async def change_user_name(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Начало процесса изменения ФИО.
    """
    await callback_query.message.edit_text("✒ Введите новое ФИО")
    await state.set_state(ChangeUserNmae.enterNewUsername)

# Обработчик: Подтверждение нового ФИО
@router.message(StateFilter(ChangeUserNmae.enterNewUsername))
async def create_new_username(message: types.Message, state: FSMContext):
    """
    Подтверждение нового ФИО пользователя.
    """
    # Сохраняем новое ФИО в состоянии
    await state.update_data(new_username=message.text)

    # Создаем клавиатуру для подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, изменить ФИО", callback_data='change_new_username')],
        [InlineKeyboardButton(text="⛔ Нет", callback_data='dont_change_')]
    ])

    # Получаем данные из состояния
    data = await state.get_data()
    new_username = data['new_username']

    # Отправляем сообщение с подтверждением
    await message.answer(f"🗂 Вы хотите изменить ваше ФИО на - {new_username}?", reply_markup=keyboard)

# Обработчик: Завершение изменения ФИО
@router.callback_query(F.data == 'change_new_username', StateFilter(ChangeUserNmae.enterNewUsername))
async def continue_create_new_username(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Завершение изменения ФИО пользователя.
    """
    data = await state.get_data()
    new_user_name = data['new_username']
    ID = callback_query.from_user.id

    # Асинхронное обновление имени пользователя
    await update_user_name(new_user_name, ID)

    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚹 Мой профиль', callback_data='my_profile')],
        [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
        [InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')]
    ])
    await callback_query.message.edit_text(f"✅ Ваше ФИО было успешно изменено на: {new_user_name}", reply_markup=keyboard)

# Обработчик: Изменение названия компании
@router.callback_query(F.data == 'change_company')
async def change_company(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Начало процесса изменения названия компании.
    """
    await callback_query.message.edit_text('✒ Введите название компании')
    await state.set_state(ChangeUserCompany.enterNewUserCompany)

@router.message(StateFilter(ChangeUserCompany.enterNewUserCompany))
async def change_company_name(message: types.Message, state: FSMContext):
    """
    Подтверждение нового названия компании.
    """
    # Сохраняем новое название компании в состоянии
    await state.update_data(new_company_name=message.text)

    # Создаем клавиатуру для подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, изменить название компании", callback_data='change_new_company_name')],
        [InlineKeyboardButton(text="⛔ Нет", callback_data='dont_change_')]
    ])
    await message.answer(f"🏢 Вы хотите изменить название компании на {message.text}?", reply_markup=keyboard)

@router.callback_query(F.data == 'change_new_company_name', StateFilter(ChangeUserCompany.enterNewUserCompany))
async def continue_change_new_company_name(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Завершение изменения названия компании.
    """
    data = await state.get_data()
    new_company_name = data['new_company_name']
    ID = callback_query.from_user.id

    # Асинхронное обновление названия компании
    await update_company_name(new_company_name, ID)

    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚹 Мой профиль', callback_data='my_profile')],
        [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
        [InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')]
    ])
    await callback_query.message.edit_text(f"✅ Название Вашей компании было изменено на {new_company_name}", reply_markup=keyboard)

# Обработчик: Изменение номера телефона
@router.callback_query(F.data == 'change_phone')
async def change_phone(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Начало процесса изменения номера телефона.
    """
    await callback_query.message.edit_text('✒ Введите новый номер телефона')
    await state.set_state(ChnageUserPhone.enterNewUserPhone)

@router.message(StateFilter(ChnageUserPhone.enterNewUserPhone))
async def change_phone_number(message: types.Message, state: FSMContext):
    """
    Подтверждение нового номера телефона.
    """
    # Сохраняем новый номер телефона в состоянии
    await state.update_data(new_phone=message.text)

    # Создаем клавиатуру для подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, изменить номер телефона", callback_data='change_new_phone_number')],
        [InlineKeyboardButton(text="⛔ Нет", callback_data='dont_change_')]
    ])
    await message.answer(f"📞 Вы хотите изменить номер телефона на {message.text}?", reply_markup=keyboard)

@router.callback_query(F.data == 'change_new_phone_number', StateFilter(ChnageUserPhone.enterNewUserPhone))
async def continue_change_new_phone_number(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Завершение изменения номера телефона.
    """
    # Извлекаем данные из состояния
    data = await state.get_data()
    new_number = data['new_phone']
    ID = callback_query.from_user.id

    # Асинхронное обновление номера телефона
    await update_phone_number(new_number, ID)

    # Очищаем состояние
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🚹 Мой профиль', callback_data='my_profile')],
        [InlineKeyboardButton(text='📃 Список направлений', callback_data='list_directionn')],
        [InlineKeyboardButton(text='📋 Список направлений, на которые я откликнулся', callback_data='list_my_direction')]
    ])

    # Отправляем подтверждение
    await callback_query.message.edit_text(f"✅ Ваш номер телефона был изменен на {new_number}", reply_markup=keyboard)

@router.message(F.text.startswith('/set_role'))
async def set_role_command(message: types.Message):
    """
    Обработчик команды /set_role для изменения роли пользователя.
    Формат команды: /set_role <telegram_id> <role>
    """
    # Проверяем, является ли пользователь администратором
    ID = str(message.from_user.id)  # Преобразуем ID в строку для сравнения
    if ID not in ADMINS:
        await message.reply("❌ У вас нет прав для выполнения этой команды.")
        return

    # Разбиваем текст команды на части
    parts = message.text.split()
    if len(parts) != 3:
        await message.reply("❌ Неверный формат команды. Используйте: /set_role <telegram_id> <role>")
        return

    telegram_id, new_role = parts[1], parts[2].lower()

    # Проверяем, что роль корректна
    if new_role not in ['user', 'manager', 'admin']:
        await message.reply("❌ Некорректная роль. Доступные роли: user, manager, admin.")
        return

    # Проверяем, существует ли пользователь с указанным ID
    user_data = get_user_data_by_id(telegram_id)
    if not user_data:
        await message.reply(f"❌ Пользователь с ID {telegram_id} не найден.")
        return

    # Обновляем роль пользователя
    try:
        await update_user_role(new_role, telegram_id)
        await message.reply(f"✅ Роль пользователя с ID {telegram_id} успешно изменена на {new_role}.")
    except Exception as e:
        await message.reply(f"❌ Произошла ошибка при обновлении роли: {e}")

@router.callback_query(F.data.startswith('dont_change_'))
async def cancel_action(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Универсальный обработчик для отмены действий.
    """
    # Очищаем состояние
    await state.clear()

    ID = callback_query.from_user.id
    user_data = get_user_data_by_id(ID)

    # Проверяем, что данные пользователя существуют
    if not user_data:
        await callback_query.message.edit_text(
            "❌ Ошибка: информация о пользователе не найдена. Попробуйте снова."
        )
        return

    # Определяем действие, которое отменяется
    action = callback_query.data.split('_')[-1]  # Извлекаем часть после "dont_change_"
    action_mapping = {
        "new_username": "изменение ФИО",
        "new_company_name": "изменение названия компании",
        "new_phone_number": "изменение номера телефона"
    }

    # Получаем описание действия
    action_description = action_mapping.get(action, "действие")

    # Отправляем сообщение об отмене
    await callback_query.message.edit_text(
        f"⛔ {action_description.capitalize()} отменено."
    )

    # Создаем клавиатуру для возврата в профиль
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Редактировать данные', callback_data='change_user_data')],
        [InlineKeyboardButton(text='🔚 Вернуться в начало', callback_data='accept_user_data')]
    ])

    # Отправляем сообщение с профилем пользователя
    await callback_query.message.edit_text(
        f"🚹 Твое ФИО: {user_data[2]}\n🏢 Твоя компания: {user_data[5]}\n📞 Твой номер телефона: {user_data[6]}",
        reply_markup=keyboard
    )
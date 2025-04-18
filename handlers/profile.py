from aiogram import Router, types, F
from states.states import ChangeUserNmae, ChangeUserCompany, ChnageUserPhone
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.users import get_user_data_by_id, update_user_name, update_company_name, update_phone_number

ID = None

router = Router()


@router.callback_query(F.data == "my_profile")
async def get_my_profile(callback_query: types.CallbackQuery):
    """
    Обработчик для отображения профиля пользователя.
    """
    ID = callback_query.from_user.id
    user_data = get_user_data_by_id(ID)

    change_user_data = InlineKeyboardButton('📝 Редактировать данные', callback_data='change_user_data')
    get_back_to_main = InlineKeyboardButton('🔚 Вернуться в начало', callback_data='accept_user_data')
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.row(change_user_data)
    keyboard.row(get_back_to_main)

    await callback_query.message.edit_text(
        f"Твое ФИО: {user_data[2]}\n"
        f"Твоя компания: {user_data[5]}\n"
        f"Твой номер телефона: {user_data[6]}",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "change_user_data")
async def change_user_data(callback_query: types.CallbackQuery):
    """
    Обработчик для выбора изменения данных пользователя.
    """
    change_user_name = InlineKeyboardButton('🖊 Изменить ФИО', callback_data='change_user_name')
    change_company = InlineKeyboardButton('🖊 Изменить название компании', callback_data='change_company')
    change_phone = InlineKeyboardButton('🖊 Изменить номер телефона', callback_data='change_phone')
    get_back_to_main = InlineKeyboardButton('🔚 Вернуться в начало', callback_data='accept_user_data')
    keyboard = InlineKeyboardMarkup(row_width=4)
    keyboard.row(change_user_name)
    keyboard.row(change_company)
    keyboard.row(change_phone)
    keyboard.row(get_back_to_main)

    await callback_query.message.edit_text('Что нужно изменить?', reply_markup=keyboard)


@router.callback_query(F.data == "change_user_name")
async def change_user_name(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для изменения ФИО пользователя.
    """
    await callback_query.message.edit_text('✒ Введите новое ФИО')
    await state.set_state(ChangeUserNmae.enterNewUsername)  # Исправлено


@router.callback_query(F.text, StateFilter(ChangeUserNmae.enterNewUsername))
async def create_new_username(message: types.Message, state: FSMContext):
    """
    Обработчик для подтверждения изменения ФИО.
    """
    async with state.update_data() as data:
        data['new_username'] = message.text

    yes = InlineKeyboardButton(f"✅ Да, изменить ФИО", callback_data='change_new_username')
    no = InlineKeyboardButton(f"⛔ Нет", callback_data='dont_change_new_username')
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.row(yes, no)

    await message.answer(f"Вы хотите изменить ваше ФИО на - {data['new_username']}?", reply_markup=keyboard)


@router.callback_query(F.data == "change_new_username", StateFilter(ChangeUserNmae.enterNewUsername))
async def continue_create_new_usernmae(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для сохранения нового ФИО.
    """
    async with state.update_data() as data:
        new_user_name = data['new_username']

    ID = callback_query.from_user.id
    update_user_name(new_user_name, ID)
    await state.clear()

    await callback_query.message.edit_text(f"Ваше ФИО было изменено на {new_user_name}")


@router.callback_query(F.data == "change_company")
async def change_company(callback_query: types.CallbackQuery):
    """
    Обработчик для изменения названия компании.
    """
    await callback_query.message.edit_text('✒ Введите название компании')
    await ChangeUserCompany.enterNewUserCompany.set()


@router.callback_query(F.text, StateFilter(ChangeUserCompany.enterNewUserCompany))
async def change_company_name(message: types.Message, state: FSMContext):
    """
    Обработчик для подтверждения изменения названия компании.
    """
    async with state.update_data() as data:
        data['new_company_name'] = message.text

    yes = InlineKeyboardButton(f"✅ Да, изменить название компании", callback_data='change_new_company_name')
    no = InlineKeyboardButton(f"⛔ Нет", callback_data='dont_change_new_company_name')
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.row(yes, no)

    await message.answer(f"Вы хотите изменить название компании на {data['new_company_name']}?", reply_markup=keyboard)


@router.callback_query(F.data == "change_new_company_name", StateFilter(ChangeUserCompany.enterNewUserCompany))
async def continue_change_new_company_name(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для сохранения нового названия компании.
    """
    async with state.update_data() as data:
        new_company_name = data['new_company_name']

    ID = callback_query.from_user.id
    update_company_name(new_company_name, ID)
    await state.clear()

    await callback_query.message.edit_text(f"Название Вашей компании было изменено на {new_company_name}")


@router.callback_query(F.data == "change_phone")
async def change_phone(callback_query: types.CallbackQuery):
    """
    Обработчик для изменения номера телефона.
    """
    await callback_query.message.edit_text('✒ Введите новый номер телефона')
    await ChnageUserPhone.enterNewUserPhone.set()


@router.callback_query(F.text, StateFilter(ChnageUserPhone.enterNewUserPhone))
async def change_phone_number(message: types.Message, state: FSMContext):
    """
    Обработчик для подтверждения изменения номера телефона.
    """
    async with state.update_data() as data:
        data['new_phone'] = message.text

    yes = InlineKeyboardButton(f"✅ Да, изменить номер телефона", callback_data='change_new_phone_number')
    no = InlineKeyboardButton(f"⛔ Нет", callback_data='dont_change_new_phone_number')
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.row(yes, no)

    await message.answer(f"Вы хотите изменить номер телефона на {data['new_phone']}?", reply_markup=keyboard)


@router.callback_query(F.data == "change_new_phone_number", StateFilter(ChnageUserPhone.enterNewUserPhone))
async def countine_change_new_phone_number(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для сохранения нового номера телефона.
    """
    async with state.update_data() as data:
        new_number = data['new_phone']

    ID = callback_query.from_user.id
    update_phone_number(new_number, ID)
    await state.clear()

    await callback_query.message.edit_text(f"Ваш номер телефона был изменен на {new_number}")
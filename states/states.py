from aiogram.fsm.state import State, StatesGroup

class RegistrationState(StatesGroup):
    WaitingForName = State()   # Ожидание имени
    WaitingForCompanyName = State() # Ожидание названия команиии
    WaitingForPhone = State()  # Ожидание номера телефона

class CreateLot(StatesGroup):
    summary = State() # Ожидание темы
    description = State() # Ожидание описания
    price = State() # Ожидание цены
    accept = State() # Ожидание подтверждения

class CreateNewManager(StatesGroup):
    enterName = State() # Ожидание ввода имени

class ChangeUserNmae(StatesGroup):
    enterNewUsername = State()
class ChangeUserCompany(StatesGroup):
    enterNewUserCompany = State()
class ChnageUserPhone(StatesGroup):
    enterNewUserPhone = State()

class CloseDirection(StatesGroup):
    chooseDirectionForClose = State()
    chooseDirectionWinner = State()

class UpdateDirectionNewPrice(StatesGroup):
    getDirectionInfo = State()
    getNewPrice = State()
    acceptNewDirectionPrice = State()

class SentDirectionPrice(StatesGroup):
    getIdDirection = State()
    enterNewDirectionPrice = State()
    acceptNewDirectionPrice = State()
    confirmNewPrice = State()
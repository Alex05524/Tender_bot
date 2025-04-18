from aiogram import Dispatcher
from .user_management import router as user_management_router
from .directions import router as user_profile_router
from .profile import router as admin_panel_router
from .registration import router as common_router
from .reports import router as reports_router

def register_handlers(dp: Dispatcher):
    """
    Регистрация всех обработчиков.
    """
    dp.include_router(user_management_router)
    dp.include_router(user_profile_router)
    dp.include_router(admin_panel_router)
    dp.include_router(common_router)
    dp.include_router(reports_router)
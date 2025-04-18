import os
from aiogram import Router, types, F
from db.reports import report_direction
from db.users import get_user_role

ID = None

router = Router()

@router.callback_query(F.data == 'get_report')
async def get_report(callback_query: types.CallbackQuery):
    """
    Обработчик для генерации и отправки отчета.
    Доступен только для администраторов и менеджеров.
    """
    try:
        # Проверка роли пользователя
        user_role = get_user_role(callback_query.from_user.id)
        if not user_role or user_role[0] not in ["admin", "manager"]:
            await callback_query.message.edit_text("❌ У вас нет прав для генерации отчета.")
            return

        # Генерация отчета
        await report_direction()
        report_file_path = "report_direction.xlsx"

        # Проверка существования файла
        if not os.path.exists(report_file_path):
            await callback_query.message.edit_text("❌ Ошибка: файл отчета не найден. Попробуйте снова.")
            return

        # Отправка файла отчета
        await callback_query.message.answer_document(
            types.FSInputFile(report_file_path),
            caption="📑 Ваш отчет готов."
        )
        print(f"Отчет успешно отправлен пользователю {callback_query.from_user.id}")

        # Удаление файла после отправки
        if os.path.exists(report_file_path):
            os.remove(report_file_path)

    except Exception as e:
        # Обработка ошибок
        print(f"Ошибка при генерации или отправке отчета: {e}")
        await callback_query.message.edit_text("❌ Произошла ошибка при формировании отчета. Попробуйте позже.")
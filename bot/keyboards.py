from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .storage import list_groups
from .admin_auth import is_admin
from .parser_site import download_schedule_by_link_text, admin_notify, bot_instance


def get_main_menu(user_id: int = None) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="📅 Показать расписание")],
    ]
    
    if user_id and is_admin(user_id):
        keyboard.append([KeyboardButton(text="⚙️ Админ-панель")])
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Показать расписание")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие",
)


ADMIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📤 Загрузить расписание")],
        [KeyboardButton(text="📋 Управление расписанием")],
        [KeyboardButton(text="🔙 Назад в главное меню")],
        [KeyboardButton(text="🔄 Проверить расписание")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


def groups_keyboard(page: int = 0, per_page: int = 8) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    all_groups = list_groups()
    start = page * per_page
    names = all_groups[start:start + per_page]

    for name in names:
        label = f"🧩 {name}"
        builder.button(text=label, callback_data=f"group:{name}")
    builder.adjust(2)

    total = len(all_groups)
    pages = max(1, (total + per_page - 1) // per_page)
    prev_page = (page - 1) % pages
    next_page = (page + 1) % pages

    nav = [
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"groups:page:{prev_page}"),
        InlineKeyboardButton(text=f"Стр. {page+1}/{pages}", callback_data="noop"),
        InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"groups:page:{next_page}"),
    ]

    builder.row(*nav)
    return builder.as_markup()


def schedule_management_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📅 Просмотр дат", callback_data="admin:view_dates"),
        InlineKeyboardButton(text="🗑️ Очистить старые", callback_data="admin:cleanup_old")
    )
    
    builder.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
        InlineKeyboardButton(text="🔄 Перезагрузить БД", callback_data="admin:reload_db")
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin:back")
    )   
    
    return builder.as_markup()


def dates_keyboard(dates: list[str], selected: str = None, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = (len(dates) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(dates))
    for i in range(start, end, 2):
        row = []
        for j in range(2):
            idx = i + j
            if idx < end:
                date = dates[idx]
                text = f"📅 {date}"
                if selected and date == selected:
                    text = f"✅ {date}"
                row.append(InlineKeyboardButton(text=text, callback_data=f"date:{date}"))
        builder.row(*row)
    nav = []
    if total_pages > 1:
        if page > 0:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"dates_page:{page-1}"))
        nav.append(InlineKeyboardButton(text=f"Стр. {page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"dates_page:{page+1}"))
        builder.row(*nav)
    return builder.as_markup()

def groups_for_date_keyboard(groups: list[str], date: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(text=f"🧩 {group}", callback_data=f"group_on_date:{date}:{group}")
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="🔙 К датам", callback_data="back_to_dates"))
    return builder.as_markup()

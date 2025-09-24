import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiohttp import ClientTimeout, TCPConnector, ClientSession

from .config import load_token
from .keyboards import MAIN_MENU, ADMIN_MENU, groups_keyboard, schedule_management_keyboard, get_main_menu, dates_keyboard, groups_for_date_keyboard
from .storage import init_storage, get_schedule_for_group
from .parser import init_db, save_table_to_db, WordParser, get_all_dates, get_all_groups, get_schedule_for_group
from .file_manager import save_schedule_file, get_schedule_files, cleanup_old_schedules, get_schedule_stats
from .admin_auth import is_admin
from .parser_site import download_schedule_by_link_text, admin_notify, bot_instance 


async def on_start(message: Message):
    menu = get_main_menu(message.from_user.id)
    
    await message.answer(
        "Привет! Я бот расписания. Выберите действие ниже:",
        reply_markup=menu,
    )


async def on_get_id(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "не указан"
    first_name = message.from_user.first_name or "не указано"
    
    text = f"""🆔 <b>Ваш Telegram ID:</b>

👤 <b>ID:</b> <code>{user_id}</code>
📝 <b>Имя:</b> {first_name}
🏷️ <b>Username:</b> @{username}

<b>Для добавления в админы:</b>
Добавьте этот ID в переменную ADMIN_IDS в файле .env:
<code>ADMIN_IDS={user_id}</code>

<b>Или для нескольких админов:</b>
<code>ADMIN_IDS={user_id},123456789,987654321</code>"""
    
    await message.answer(text, parse_mode="HTML")


async def on_admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        menu = get_main_menu(message.from_user.id)
        await message.answer(
            "❌ У вас нет прав доступа к админ-панели.\n\n"
            "Обратитесь к администратору для получения доступа.",
            reply_markup=menu
        )
        return
    
    await message.answer(
        "⚙️ <b>Админ-панель</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=ADMIN_MENU
    )


async def on_upload_schedule(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет прав доступа")
        return
    
    await message.answer(
        "📤 <b>Загрузка расписания</b>\n\n"
        "Отправьте DOCX файл с расписанием.\n"
        "Файл будет автоматически переименован по дате.",
        parse_mode="HTML"
    )


async def on_schedule_management(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет прав доступа")
        return
    
    await message.answer(
        "📋 <b>Управление расписанием</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=schedule_management_keyboard()
    )

async def on_check_schedule(message: Message):
    date_str = datetime.now().strftime("%d %B")
    await message.answer("🔄 Проверяю расписание...")
    await download_schedule_by_link_text(
        "http://egorlyk-college.ru/%d1%80%d0%b0%d1%81%d0%bf%d0%b8%d1%81%d0%b0%d0%bd%d0%b8%d0%b5/",
        save_schedule_file,
        admin_notify,
        bot_instance,
        date_str
    )
    await message.answer("✅ Расписание проверено")

async def on_back_to_main(message: Message):
    menu = get_main_menu(message.from_user.id)
    
    await message.answer(
        "🏠 <b>Главное меню</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=menu
    )


async def on_show_schedule(message: Message):
    dates = get_all_dates()
    if not dates:
        await message.answer("❌ Нет доступных дат в расписании.")
        return
    await message.answer("Выберите дату:", reply_markup=dates_keyboard(dates))


async def on_groups_pagination(callback: CallbackQuery):
    try:
        _, _, page_str = callback.data.split(":", 2)
        page = int(page_str)
    except Exception:
        page = 0
    await callback.message.edit_reply_markup(reply_markup=groups_keyboard(page=page))
    await callback.answer()


def extract_pair_number(pair: str) -> int:
    if not pair:
        return 999
    match = re.match(r"(\d+)-(\d+)", pair)
    if match:
        start = int(match.group(1))
        return (start + 1) // 2
    return 999


def format_time(time_str: str) -> str:
    if not time_str:
        return "—"
    
    match = re.match(r"(\d{4})\s*–\s*(\d{4})", time_str)
    if match:
        start, end = match.groups()
        try:
            start_h = int(start[:2])
            start_m = int(start[2:])
            end_h = int(end[:2])
            end_m = int(end[2:])
            
            if 0 <= start_h <= 23 and 0 <= start_m <= 59 and 0 <= end_h <= 23 and 0 <= end_m <= 59:
                return f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
        except (ValueError, IndexError):
            pass
    
    return time_str


async def on_group_selected(callback: CallbackQuery):
    group_name = callback.data.split(":", 1)[1]
    await callback.answer()
    items = get_schedule_for_group(group_name)
    if not items:
        await callback.message.answer(
            f"❌ Для группы <b>{group_name}</b> расписание не найдено.\n\n"
            f"Загрузите DOCX файл и перезапустите бота.",
            parse_mode="HTML",
        )
        return

    from collections import defaultdict
    by_date = defaultdict(list)
    for it in items:
        by_date[(it.get("date"), it.get("weekday"))].append(it)

    lines = []
    
    lines.append(f"🎓 <b>РАСПИСАНИЕ ГРУППЫ {group_name}</b>")
    lines.append("━" * 30)
    
    for (date, weekday), arr in by_date.items():
        lines.append(f"\n📅 <b>{date or ''} {weekday or ''}</b>")
        lines.append("─" * 25)
        
        arr_sorted = sorted(arr, key=lambda x: extract_pair_number(x.get("pair", "")))
        
        for it in arr_sorted:
            pair = it.get("pair") or "—"
            time = format_time(it.get("time", ""))
            subj = it.get("subject") or ""
            teacher = it.get("teacher") or ""
            room = it.get("room") or ""
            
            pair_num = extract_pair_number(pair)
            if pair_num != 999:
                pair_display = f"🔢 {pair_num} пара"
            else:
                pair_display = f"🔢 {pair}"
            
            if room:
                room_text = f"🏢 ауд. {room}"
            else:
                room_text = "🏢 ауд. не указана"
            
            if teacher:
                teacher_text = f"👨‍🏫 {teacher}"
            else:
                teacher_text = "👨‍🏫 не указан"
            
            lines.append(f"{pair_display}")
            lines.append(f"⏰ {time}")
            lines.append(f"📚 <b>{subj}</b>")
            lines.append(f"{teacher_text}")
            lines.append(f"{room_text}")
            lines.append("")

    text = "\n".join(lines) if lines else "📝 Нет занятий"
    await callback.message.answer(text, parse_mode="HTML")


async def on_date_selected(callback: CallbackQuery):
    date = callback.data.split(":", 1)[1]
    all_groups = get_all_groups()
    groups = []
    for group in all_groups:
        lessons = [l for l in get_schedule_for_group(group) if l['date'] == date]
        if lessons:
            groups.append(group)
    if not groups:
        await callback.message.answer(f"❌ Нет расписания на {date}")
        return
    await callback.message.edit_text(f"Выберите группу на <b>{date}</b>:", parse_mode="HTML", reply_markup=groups_for_date_keyboard(groups, date))
    await callback.answer()


async def on_group_on_date(callback: CallbackQuery):
    _, date, group = callback.data.split(":", 2)
    lessons = [l for l in get_schedule_for_group(group) if l['date'] == date]
    if not lessons:
        await callback.message.answer(f"❌ Для группы <b>{group}</b> на {date} расписание не найдено.", parse_mode="HTML")
        return
    dates = get_all_dates()
    idx = dates.index(date) if date in dates else 0
    prev_date = dates[idx-1] if idx > 0 else None
    next_date = dates[idx+1] if idx < len(dates)-1 else None
    lines = [f"📅 <b>{date}</b> | 🧩 <b>{group}</b>", "━"*30]
    for l in sorted(lessons, key=lambda x: (x['pair'] or '999')):
        lines.append(f"🔢 <b>{l['pair'] or '—'}</b>  ⏰ {l['time'] or '—'}")
        lines.append(f"📚 <b>{l['subject']}</b>")
        if l['teacher']:
            lines.append(f"👨‍🏫 {l['teacher']}")
        if l['room']:
            lines.append(f"🏢 {l['room']}")
        lines.append("─"*15)
    nav = []
    if prev_date:
        nav.append(InlineKeyboardButton(text="⬅️ Пред. дата", callback_data=f"group_on_date:{prev_date}:{group}"))
    nav.append(InlineKeyboardButton(text="🔙 К датам", callback_data="back_to_dates"))
    if next_date:
        nav.append(InlineKeyboardButton(text="След. дата ➡️", callback_data=f"group_on_date:{next_date}:{group}"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[nav])
    await callback.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


async def on_dates_page(callback: CallbackQuery):
    page = int(callback.data.split(":", 1)[1])
    dates = get_all_dates()
    await callback.message.edit_text("Выберите дату:", reply_markup=dates_keyboard(dates, page=page))
    await callback.answer()


async def on_back_to_dates(callback: CallbackQuery):
    dates = get_all_dates()
    await callback.message.edit_text("Выберите дату:", reply_markup=dates_keyboard(dates))
    await callback.answer()


async def on_admin_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет прав доступа")
        return
    
    action = callback.data.split(":", 1)[1]
    await callback.answer()
    
    if action == "view_dates":
        files = get_schedule_files()
        if files:
            text = "📅 <b>Файлы расписания:</b>\n\n"
            for filename, create_time in files[:10]:
                text += f"📄 {filename}\n"
                text += f"🕒 {create_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        else:
            text = "📝 Файлы расписания не найдены"
        
        await callback.message.answer(text, parse_mode="HTML")
    
    elif action == "cleanup_old":
        deleted_count, message = cleanup_old_schedules()
        await callback.message.answer(message)
    
    elif action == "stats":
        stats = get_schedule_stats()
        text = f"""📊 <b>Статистика расписания:</b>

📁 Всего файлов: {stats['total_files']}
📅 Текущая неделя: {stats['current_week_files']}
🗑️ Старых файлов: {stats['old_files']}

<b>Последние файлы:</b>"""
        
        for filename, create_time in stats['files']:
            text += f"\n📄 {filename}"
            text += f"\n🕒 {create_time.strftime('%d.%m.%Y %H:%M')}"
        
        await callback.message.answer(text, parse_mode="HTML")
    
    elif action == "reload_db":
        await callback.message.answer("🔄 Перезагружаем базу данных...")
        try:
            init_db()
            await callback.message.answer("✅ База данных перезагружена")
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка при перезагрузке: {e}")
    
    elif action == "back":
        await callback.message.answer(
            "⚙️ <b>Админ-панель</b>\n\n"
            "Выберите действие:",
            parse_mode="HTML",
            reply_markup=ADMIN_MENU
        )


async def on_document_received(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет прав доступа")
        return
    
    if not message.document:
        await message.answer("❌ Файл не найден")
        return
    
    if not message.document.file_name.lower().endswith('.docx'):
        await message.answer("❌ Поддерживаются только DOCX файлы")
        return
    
    await message.answer("📥 Загружаю файл...")
    
    try:
        file_info = await bot.get_file(message.document.file_id)
        file_path = Path(__file__).parent / "temp_schedule.docx"
        
        await bot.download_file(file_info.file_path, file_path)
        
        # TODO: Реализовать извлечение даты из файла
        current_date = datetime.now().strftime("%d %B").replace("January", "января").replace("February", "февраля").replace("March", "марта").replace("April", "апреля").replace("May", "мая").replace("June", "июня").replace("July", "июля").replace("August", "августа").replace("September", "сентября").replace("October", "октября").replace("November", "ноября").replace("December", "декабря")
        
        success, message_text = await save_schedule_file(file_path, current_date)

        
        if success:
            await message.answer("🔄 Парсирую расписание...")
            try:
                with WordParser(str(file_path)) as doc:
                    tables = doc.get_tables()
                    count = 0
                    for table in tables:
                        if save_table_to_db(table):
                            count += 1
                await message.answer(f"✅ Загружено и обработано {count} таблиц!")
            except Exception as e:
                await message.answer(f"⚠️ Файл сохранен, но ошибка при парсинге: {e}")
        else:
            await message.answer(f"❌ {message_text}")
        
        if file_path.exists():
            file_path.unlink()
            
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке файла: {e}")
        logging.error(f"Ошибка при обработке файла: {e}")


async def preload_from_docx_if_present() -> None:
    docx_path = Path(__file__).with_name("file.docx")
    if docx_path.exists():
        logging.info(f"Найден DOCX файл: {docx_path}")
        init_db()
        
        from .parser import main as parse_main
        parse_main()
        logging.info("Данные из DOCX загружены в БД")
    else:
        logging.info("DOCX файл не найден, используем существующие данные в БД")


async def document_handler(message: Message, bot: Bot):
    await on_document_received(message, bot)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    logging.info("Запуск бота расписания...")
    
    token = load_token()
    init_storage()
    await preload_from_docx_if_present()

    timeout = ClientTimeout(total=30, connect=10)

    dp = Dispatcher(storage=MemoryStorage())
    bot = Bot(
        token=token, 
        default=DefaultBotProperties(parse_mode="HTML"),
        session_timeout=timeout,
        connector=TCPConnector(family=2)
    )

    # Регистрация хендлеров
    dp.message.register(on_start, CommandStart())
    dp.message.register(on_get_id, Command("id"))
    dp.message.register(on_show_schedule, F.text == "📅 Показать расписание")
    dp.message.register(on_admin_panel, F.text == "⚙️ Админ-панель")
    dp.message.register(on_upload_schedule, F.text == "📤 Загрузить расписание")
    dp.message.register(on_schedule_management, F.text == "📋 Управление расписанием")
    dp.message.register(on_check_schedule, F.text == "🔄 Проверить расписание")
    dp.message.register(on_back_to_main, F.text == "🔙 Назад в главное меню")
    dp.message.register(document_handler, F.document)

    dp.callback_query.register(on_groups_pagination, F.data.startswith("groups:page:"))
    dp.callback_query.register(on_group_selected, F.data.startswith("group:"))
    dp.callback_query.register(on_admin_callback, F.data.startswith("admin:"))
    dp.callback_query.register(on_date_selected, F.data.startswith("date:"))
    dp.callback_query.register(on_group_on_date, F.data.startswith("group_on_date:"))
    dp.callback_query.register(on_dates_page, F.data.startswith("dates_page:"))
    dp.callback_query.register(on_back_to_dates, F.data == "back_to_dates")

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Бот успешно запущен и готов к работе!")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

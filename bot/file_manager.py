import os
import shutil
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
import logging
from .parser_site import download_schedule_by_link_text, admin_notify, bot_instance

# Путь к папке с файлами расписания
SCHEDULE_FILES_DIR = Path(__file__).parent / "schedule_files"


def init_schedule_files_dir() -> None:
    SCHEDULE_FILES_DIR.mkdir(exist_ok=True)
    logging.info(f"Папка для файлов расписания: {SCHEDULE_FILES_DIR}")


def get_week_start(date: datetime) -> datetime:     
    return date - timedelta(days=date.weekday())


def get_week_end(date: datetime) -> datetime:
    week_start = get_week_start(date)
    return week_start + timedelta(days=6)


async def save_schedule_file(file_path: Path, date_str: str) -> Tuple[bool, str]:
    try:
        init_schedule_files_dir()

        safe_date = date_str.replace(" ", "_").lower()
        filename = f"schedule_{safe_date}.docx"
        target_path = SCHEDULE_FILES_DIR / filename

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, shutil.copy2, file_path, target_path)

        logging.info(f"Файл расписания сохранен: {target_path}")
        return True, f"✅ Файл расписания сохранен как: {filename}"

    except Exception as e:
        logging.error(f"Ошибка при сохранении файла: {e}")
        return False, f"❌ Ошибка при сохранении файла: {e}"

def get_schedule_files() -> List[Tuple[str, datetime]]:

    try:
        init_schedule_files_dir()
        
        files = []
        for file_path in SCHEDULE_FILES_DIR.glob("schedule_*.docx"):
            stat = file_path.stat()
            create_time = datetime.fromtimestamp(stat.st_ctime)
            files.append((file_path.name, create_time))
        
        files.sort(key=lambda x: x[1], reverse=True)
        return files
        
    except Exception as e:
        logging.error(f"Ошибка при получении списка файлов: {e}")
        return []


def cleanup_old_schedules() -> Tuple[int, str]:

    try:
        init_schedule_files_dir()
        
        current_week_start = get_week_start(datetime.now())
        deleted_count = 0
        
        for file_path in SCHEDULE_FILES_DIR.glob("schedule_*.docx"):
            stat = file_path.stat()
            file_time = datetime.fromtimestamp(stat.st_ctime)
            
            if file_time < current_week_start:
                file_path.unlink()
                deleted_count += 1
                logging.info(f"Удален старый файл: {file_path.name}")
        
        if deleted_count > 0:
            message = f"🗑️ Удалено {deleted_count} старых файлов расписания"
        else:
            message = "✅ Старых файлов не найдено"
            
        return deleted_count, message
        
    except Exception as e:
        logging.error(f"Ошибка при очистке старых файлов: {e}")
        return 0, f"❌ Ошибка при очистке: {e}"


def get_schedule_file_for_date(date_str: str) -> Optional[Path]:

    try:
        init_schedule_files_dir()
        
        safe_date = date_str.replace(" ", "_").lower()
        filename = f"schedule_{safe_date}.docx"
        file_path = SCHEDULE_FILES_DIR / filename
        
        if file_path.exists():
            return file_path
        else:
            return None
            
    except Exception as e:
        logging.error(f"Ошибка при поиске файла для даты {date_str}: {e}")
        return None


def get_schedule_stats() -> dict:

    try:
        files = get_schedule_files()
        current_week_start = get_week_start(datetime.now())
        
        total_files = len(files)
        current_week_files = sum(1 for _, create_time in files if create_time >= current_week_start)
        old_files = total_files - current_week_files
        
        return {
            "total_files": total_files,
            "current_week_files": current_week_files,
            "old_files": old_files,
            "files": files[:5]
        }
        
    except Exception as e:
        logging.error(f"Ошибка при получении статистики: {e}")
        return {
            "total_files": 0,
            "current_week_files": 0,
            "old_files": 0,
            "files": []
        }

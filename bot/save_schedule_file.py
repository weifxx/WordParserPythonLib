import shutil
import logging
import asyncio
from pathlib import Path
from typing import Tuple

# Папка для сохранённых расписаний
SCHEDULE_FILES_DIR = Path("schedules")  # укажи свою папку

def init_schedule_files_dir():
    """Создаёт папку для файлов расписаний, если её нет."""
    SCHEDULE_FILES_DIR.mkdir(parents=True, exist_ok=True)


async def save_schedule_file(file_path: Path, date_str: str) -> Tuple[bool, str]:
    """
    Асинхронно сохраняет файл расписания в SCHEDULE_FILES_DIR
    и удаляет исходный временный файл.
    """
    try:
        init_schedule_files_dir()

        safe_date = date_str.replace(" ", "_").lower()
        filename = f"schedule_{safe_date}.docx"
        target_path = SCHEDULE_FILES_DIR / filename

        # Асинхронное копирование через executor, чтобы не блокировать loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, shutil.copy2, file_path, target_path)

        # Удаляем временный файл
        if file_path.exists():
            await loop.run_in_executor(None, file_path.unlink)

        logging.info(f"Файл расписания сохранен: {target_path}")
        return True, f"✅ Файл расписания сохранен как: {filename}"

    except Exception as e:
        logging.error(f"Ошибка при сохранении файла: {e}")
        return False, f"❌ Ошибка при сохранении файла: {e}"

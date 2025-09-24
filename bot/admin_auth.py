import os
from typing import Set
import logging
from pathlib import Path

ADMIN_IDS: Set[int] = set()

def load_admin_ids() -> None:

    global ADMIN_IDS
    
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    
    if not admin_ids_str:
        env_path = Path(__file__).with_name(".env")
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("ADMIN_IDS="):
                    admin_ids_str = line.split("=", 1)[1].strip().strip('"\'')
                    break
    
    if admin_ids_str:
        try:
            ADMIN_IDS = {int(id_str.strip()) for id_str in admin_ids_str.split(",") if id_str.strip()}
            logging.info(f"Загружены ID администраторов: {ADMIN_IDS}")
        except ValueError as e:
            logging.error(f"Ошибка при загрузке ID администраторов: {e}")


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def add_admin(user_id: int) -> bool:
    if user_id not in ADMIN_IDS:
        ADMIN_IDS.add(user_id)
        logging.info(f"Добавлен администратор: {user_id}")
        return True
    return False


def remove_admin(user_id: int) -> bool:
    if user_id in ADMIN_IDS:
        ADMIN_IDS.remove(user_id)
        logging.info(f"Удален администратор: {user_id}")
        return True
    return False


def get_admin_list() -> Set[int]:
    return ADMIN_IDS.copy()


load_admin_ids()

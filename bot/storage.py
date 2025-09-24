from __future__ import annotations

import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .parser import get_all_groups, get_schedule_for_group as parser_get_schedule, init_db

DB_PATH = Path(__file__).with_name("schedule.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_storage() -> None:
    """Инициализация хранилища"""
    init_db()


def list_groups() -> List[str]:
    """Список всех групп"""
    return get_all_groups()


def get_schedule_for_group_db(code: str) -> List[Dict[str, Any]]:
    """Расписание для группы"""
    return parser_get_schedule(code)


def save_schedules(schedules: List[Dict[str, Any]]) -> None:
    """Заглушка - данные уже сохранены через parser.py"""
    logging.info("Данные уже сохранены в БД через parser.py")

def get_schedule_for_group(code: str) -> List[Dict[str, Any]]:
    """Получаем расписание для конкретной группы (совместимость)"""
    return get_schedule_for_group_db(code)

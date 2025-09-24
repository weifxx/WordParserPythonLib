#!/usr/bin/env python3
"""Тестируем функции работы с БД"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "wordparsers"))

from parser import get_all_groups, get_schedule_for_group, init_db

def test_db():
    print("=== Тест БД ===")
    
    init_db()
    
    groups = get_all_groups()
    print(f"Найдено групп: {len(groups)}")
    print(f"Группы: {groups}")
    
    if groups:
        first_group = groups[0]
        print(f"\n=== Расписание для {first_group} ===")
        schedule = get_schedule_for_group(first_group)
        print(f"Найдено занятий: {len(schedule)}")
        
        for lesson in schedule[:3]:
            print(f"  {lesson}")
    
    print("\n=== Тест завершен ===")

if __name__ == "__main__":
    test_db()

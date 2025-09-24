#!/usr/bin/env python3
"""Тестируем загрузку админов"""

from admin_auth import ADMIN_IDS, load_admin_ids, is_admin

def test_admin_loading():
    print("=== Тест загрузки админов ===")
    
    load_admin_ids()
    
    print(f"Загруженные ID админов: {ADMIN_IDS}")
    
    test_id = 123456789
    print(f"Тест ID {test_id}: {'✅ Админ' if is_admin(test_id) else '❌ Не админ'}")
    
    print(f"Все админы: {list(ADMIN_IDS)}")

if __name__ == "__main__":
    test_admin_loading()

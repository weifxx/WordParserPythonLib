import sys
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "wordparsers"))

from wordparser import WordParser

DB_PATH = Path(__file__).with_name("schedule.db")

PAIR_NAMES = ["1 пара", "2 пара", "3 пара", "4 пара", "5 пара", "6 пара"]
PAIR_TIMES = [
    "08:30 - 10:05",
    "10:15 - 11:50",
    "12:00 - 13:35",
    "13:45 - 15:20",
    "15:40 - 17:15",
    "17:25 - 19:00"
]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            weekday TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            schedule_id INTEGER,
            FOREIGN KEY(schedule_id) REFERENCES schedules(id)
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            pair_number TEXT,
            time_slot TEXT,
            subject TEXT,
            teacher TEXT,
            room TEXT,
            FOREIGN KEY(group_id) REFERENCES groups(id)
        );
    """)
    conn.commit()
    conn.close()
    print("БД проверена/создана (данные не удалялись)")


def parse_date_from_row(row: List[str]) -> Tuple[Optional[str], Optional[str]]:
    if not row or not row[0]:
        return None, None
    
    text = row[0].strip()
    match = re.match(r"(\d{1,2}\s+[А-Яа-я]+)\s+([А-ЯЁ]+)", text)
    if match:
        return match.group(1), match.group(2)
    
    return None, None

def parse_pairs_from_row(row: List[str]) -> List[str]:
    return PAIR_NAMES.copy()

def parse_times_from_row(row: List[str]) -> List[str]:
    return PAIR_TIMES.copy()

def parse_group_row(row: List[str], pairs: List[str], times: List[str]) -> Optional[Dict[str, Any]]:
    if not row or not row[0]:
        return None
    
    group_code = row[0].strip()
    if not group_code:
        return None
    
    group_data = {
        "code": group_code,
        "lessons": []
    }
    
    for i, cell in enumerate(row[1:], 1):
        if i > len(pairs) or i > len(times):
            break

        if not cell or not cell.strip():
            continue
        
        pair = pairs[i-1] if i-1 < len(pairs) else None
        time = times[i-1] if i-1 < len(times) else None
        
        lesson_text = cell.strip()
        lines = lesson_text.split('\n')
        subject = lines[0].strip() if lines else ""
        
        teacher = ""
        room = ""
        
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("преп."):
                teacher = line.replace("преп.", "").strip()
            elif line.startswith("ауд."):
                room = line.replace("ауд.", "").strip()
        
        if subject:
            group_data["lessons"].append({
                "pair": pair,
                "time": time,
                "subject": subject,
                "teacher": teacher,
                "room": room
            })
    
    def lesson_sort_key(lesson):
        try:
            start = lesson["time"].split("-")[0].strip()
            h, m = map(int, start.split(":"))
            return h * 60 + m
        except Exception:
            return 9999

    group_data["lessons"].sort(key=lesson_sort_key)
    
    return group_data if group_data["lessons"] else None

def save_table_to_db(table: List[List[str]]) -> bool:
    if len(table) < 3:
        return False
    
    date, weekday = parse_date_from_row(table[0])
    if not date:
        print(f"Не удалось извлечь дату из: {table[0]}")
        return False
    
    print(f"Обрабатываем дату: {date} {weekday}")
    
    pairs = parse_pairs_from_row(table[1])
    times = parse_times_from_row(table[2])
    
    print(f"Пары: {pairs}")
    print(f"Время: {times}")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id FROM schedules WHERE date = ?", (date,))
        existing = cur.fetchone()
        
        if existing:
            schedule_id = existing[0]
        else:
            cur.execute("INSERT INTO schedules (date, weekday) VALUES (?, ?)", (date, weekday))
            schedule_id = cur.lastrowid
        
        for row in table[3:]:
            group_data = parse_group_row(row, pairs, times)
            if not group_data:
                continue
            
            print(f"  Группа: {group_data['code']} ({len(group_data['lessons'])} занятий)")
            
            cur.execute("SELECT id FROM groups WHERE code = ? AND schedule_id = ?", (group_data['code'], schedule_id))
            existing_group = cur.fetchone()
            
            if existing_group:
                group_id = existing_group[0]
                cur.execute("DELETE FROM lessons WHERE group_id = ?", (group_id,))
            else:
                cur.execute("INSERT INTO groups (code, schedule_id) VALUES (?, ?)", (group_data['code'], schedule_id))
                group_id = cur.lastrowid
            
            for lesson in group_data['lessons']:
                cur.execute("""
                    INSERT INTO lessons (group_id, pair_number, time_slot, subject, teacher, room)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    group_id,
                    lesson['pair'],
                    lesson['time'],
                    lesson['subject'],
                    lesson['teacher'],
                    lesson['room']
                ))
        
        conn.commit()
        print(f"✓ Сохранено расписание для {date}")
        return True
        
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_all_groups() -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT DISTINCT code FROM groups ORDER BY code")
    groups = [row[0] for row in cur.fetchall()]
    
    conn.close()
    return groups


def get_schedule_for_group(group_code: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            s.date, s.weekday,
            l.pair_number, l.time_slot, l.subject, l.teacher, l.room
        FROM lessons l
        JOIN groups g ON g.id = l.group_id
        JOIN schedules s ON s.id = g.schedule_id
        WHERE g.code = ?
        ORDER BY s.date, l.time_slot
    """, (group_code,))
    
    lessons = []
    for row in cur.fetchall():
        lessons.append({
            "date": row[0],
            "weekday": row[1],
            "pair": row[2],
            "time": row[3],
            "subject": row[4],
            "teacher": row[5],
            "room": row[6]
        })
    
    conn.close()
    return lessons


def get_all_dates() -> List[str]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT date FROM schedules ORDER BY date")
    dates = [row[0] for row in cur.fetchall()]
    
    conn.close()
    return dates


def main():
    init_db()
    
    docx_path = Path(__file__).with_name("file.docx")
    if not docx_path.exists():
        print(f"Файл не найден: {docx_path}")
        return
    
    print("Парсинг DOCX")
    
    with WordParser(str(docx_path)) as doc:
        tables = doc.get_tables()
        print(f"Найдено таблиц: {len(tables)}")
        
        for i, table in enumerate(tables):
            print(f"\nТаблица {i+1} ")
            success = save_table_to_db(table)
            if success:
                print(f"✓ Таблица {i+1} обработана")
            else:
                print(f"✗ Ошибка в таблице {i+1}")
    
    print("\n Парсинг завершен ")
    
    print(f"\nПроверка БД")
    groups = get_all_groups()
    dates = get_all_dates()
    print(f"Даты: {dates}")
    print(f"Группы ({len(groups)}): {groups}")


if __name__ == "__main__":
    main()
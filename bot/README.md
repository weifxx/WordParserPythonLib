# Telegram-бот расписания

Кнопка "Показать расписание" выводит красивые кнопки групп с пагинацией.

## Запуск

1) Установите зависимости:
```powershell
cd bot
python -m pip install -r requirements.txt
```

2) Укажите токен бота:
- В переменной окружения `BOT_TOKEN`, или
- Файл `bot/.env` со строкой `BOT_TOKEN=123:ABC`, или
- Файл `bot/token.txt` с токеном.

3) Запустите:
```powershell
python -m bot.main
```

## Где задаются группы
Редактируйте список в `bot/groups.py` (массив `GROUPS`).

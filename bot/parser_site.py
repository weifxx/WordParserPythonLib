import aiohttp
import asyncio
import os
import shutil
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin
from aiogram import Bot
from typing import Tuple

from .admin_auth import ADMIN_IDS
from .config import load_token

bot_instance = Bot(token=load_token())

async def download_schedule_by_link_text(url, callback, admin_notify, bot_instance, date_str):
    tomorrow = datetime.now() + timedelta(days=1)
    tomorrow_day_str = str(tomorrow.day)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                await admin_notify(f"Ошибка при загрузке страницы: {resp.status}", bot_instance)
                return
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    link_tag = None
    for a in soup.find_all("a", href=True):
        if a.get_text(strip=True) == tomorrow_day_str:
            link_tag = a
            break

    if not link_tag:
        await admin_notify(f"Ссылка с текстом '{tomorrow_day_str}' не найдена на странице", bot_instance)
        return

    href = link_tag["href"]
    file_url = href if href.startswith("http") else urljoin(url, href)

    filename = os.path.basename(file_url)
    file_path = Path(filename)

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status != 200:
                await admin_notify(f"Ошибка загрузки файла: {resp.status}", bot_instance)
                return
            content = await resp.read()

    with open(file_path, "wb") as f:
        f.write(content)

    print(f"Файл {filename} ({tomorrow.strftime('%d %B %Y')}) успешно скачан ✅")

    success, msg = await callback(file_path, date_str)
    await admin_notify(msg, bot_instance)

async def admin_notify(message: str, bot: Bot = bot_instance):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            print(f"Failed to send message to {admin_id}: {e}")


async def some_func():
    await admin_notify("test", bot_instance)

async def main():
    await some_func()

if __name__ == "__main__":
    asyncio.run(main())

import os
from pathlib import Path

from typing import Optional


def load_token() -> str:

    env_path = Path(__file__).with_name(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"\'')

    raise RuntimeError(
        "Не найден BOT_TOKEN. Добавьте .env (BOT_TOKEN=...)"
    )

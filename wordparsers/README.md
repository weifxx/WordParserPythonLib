## Установка

Локальная установка из исходников:

```
pip install -e .
```

## Быстрый старт

```
from wordparser import WordParser

# Использование с контекст-менеджером
with WordParser("example.docx") as doc:
    print(doc.get_text())  # Весь текст из документа

    for table in doc.get_tables():
        for row in table:
            print(row)

    core = doc.get_core_properties()
    print(core.get("creator"), core.get("title"))

    images = doc.list_images()
    if images:
        data = doc.read_image((images[0], 0))
        with open("extracted.png", "wb") as f:
            f.write(data)
```

## API

- `WordParser(list_files)` — список файлов в архиве.
- `WordParser(get_text)` — весь текст `word/document.xml`.
- `WordParser(iter_tables)` / `WordParser(get_tables)` — таблицы как списки строк и ячеек.
- `WordParser(get_core_properties)` — свойства из `docProps/core.xml`.
- `WordParser(list_images)` — список путей изображений `word/media/*`.
- `WordParser(read_image)` — чтение изображения по имени или индексу.

# Liveinternet Parser
Асинхронный парсер рейтинга сайтов Liveinternet.ru с сохранением данных в SQLite.

## Описание
Парсер собирает данные о сайтах из рейтинга Liveinternet (название, URL, описание, 
трафик)

## Стек
- Python 3.11
- aiohttp — асинхронные HTTP-запросы
- aiosqlite — асинхронная запись в SQLite
- asyncio — управление конкурентностью

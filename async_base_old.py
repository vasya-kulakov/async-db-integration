import aiohttp
import asyncio
import aiosqlite
import time

def check_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Функция {func.__name__} выполнилась за {end - start:.4f} секунд")
        return result
    return wrapper


DB_PATH = 'liveinternet.db'


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT,
                url_site  TEXT UNIQUE,
                description TEXT,
                traffic   TEXT,
                percent   TEXT,
                parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await db.commit()


async def write_to_db(db, data):
    try:
        await db.execute(
            '''INSERT OR IGNORE INTO sites (name, url_site, description, traffic, percent)
               VALUES (:name, :url_site, :description, :traffic, :percent)''',
            data
        )
    except aiosqlite.Error as e:
        print(f'DB error: {e}')


async def fetch_text(session, url):
    async with session.get(url) as resp:
        return await resp.text(encoding='utf-8')


async def parse_site(session, db, url):
    text = await fetch_text(session, url)
    data = text.strip().split('\n')[1:]
    if not data:
        return
    for row in data:
        columns = row.strip().split('\t')
        keys = ['name', 'url_site', 'description', 'traffic', 'percent']
        if len(columns) < len(keys):
            continue
        info = {key: columns[i] for i, key in enumerate(keys)}
        await write_to_db(db, info)
    await db.commit()


async def main():
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        async with aiohttp.ClientSession() as session:
            base_url = 'https://www.liveinternet.ru/rating/ru//today.tsv?page={}'
            tasks = [
                asyncio.create_task(parse_site(session, db, base_url.format(p)))
                for p in range(1, 1000)
            ]
            await asyncio.gather(*tasks)


@check_time
def async_function():
    asyncio.run(main())


if __name__ == '__main__':
    async_function()

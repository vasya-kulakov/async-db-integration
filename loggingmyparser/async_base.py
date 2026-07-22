import aiohttp
import asyncio
import aiosqlite
import logging.config
import yaml
from pathlib import Path
import os
import time

def check_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Функция {func.__name__} выполнилась за {end - start:.4f} секунд")
        return result
    return wrapper

NUM_PAGE = 1000
BASE_PATH = Path(__file__).parent
EXPORTDIRNAME = f"{BASE_PATH}/MyLog"
os.makedirs(EXPORTDIRNAME, exist_ok=True)
config_file = BASE_PATH / 'config' / 'log_config.yaml'
DB_PATH = 'liveinternet.db'


with open(config_file) as f:
    yaml_text = f.read()
yaml_text = yaml_text.replace('CHOICEDIR_PLEASE', EXPORTDIRNAME)
config = yaml.safe_load(yaml_text)
logging.config.dictConfig(config)


LOGGER = logging.getLogger('parse_logger')
LOGGER.debug('Logger work successful')
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
        LOGGER.debug('db was created')
        await db.commit()


async def write_to_db(db, data):
    try:
        await db.execute(
            '''INSERT OR IGNORE INTO sites (name, url_site, description, traffic, percent)
               VALUES (:name, :url_site, :description, :traffic, :percent)''',
            data
        )
    except aiosqlite.Error as e:
        LOGGER.exception(f'{e}')
        print(f'DB error: {e}')


async def fetch_text(session, url):
    try:
        async with session.get(url) as resp:
            return await resp.text(encoding='utf-8')
    except aiohttp.ClientError as e:
        LOGGER.exception(f'Network error: {url}')
        return ''


async def parse_site(session, db, url, p):
    LOGGER.debug(f'{p} page: parsing...')
    text = await fetch_text(session, url)
    data = text.strip().split('\n')[1:]
    if not data:
        LOGGER.warning(f'{p} page: no data err')
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
    LOGGER.info('Start parser')
    await init_db()
    async with aiosqlite.connect(DB_PATH) as db:
        async with aiohttp.ClientSession() as session:
            base_url = 'https://www.liveinternet.ru/rating/ru//today.tsv?page={}'
            tasks = [
                asyncio.create_task(parse_site(session, db, base_url.format(p), p))
                for p in range(1, NUM_PAGE)
            ]
            await asyncio.gather(*tasks)

    LOGGER.info(f'End Parser, he worked on {NUM_PAGE} pages')


@check_time
def async_function():
    asyncio.run(main())


if __name__ == '__main__':
    async_function()
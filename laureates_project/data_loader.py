"""
Здесь загружаем и сохраняем исходные данные Нобелевской премии.

Данные получаем через официальный Nobel Prize API. Поскольку API может 
возвращать записи несколькими страницами, делаю последовательную 
загрузку всех страниц с проверкой их количества.

Сохраняю все полученные результаты в JSON-файл.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

URL_LAUREATES = 'https://api.nobelprize.org/2.1/laureates'
DATA_FILE = Path(__file__).resolve().parent / 'data' / 'laureates.json'


def download_laureates(page_size: int = 1200) -> dict:
    """
Скачиваем полный список лауреатов через Nobel Prize API.

Функция отправляет GET-запросы к API и загружает данные постранично. 
После каждого запроса проверяется HTTP-статус, а полученные записи 
добавляются к общему списку.

Если в ответе есть ссылка на следующую страницу, загрузка продолжается. 
Когда страницы заканчиваются, функция сравнивает количество полученных 
записей с общим числом лауреатов из meta.count.

Args:
    page_size: Максимальное количество записей,
        запрашиваемых за одну страницу.

Returns:
    Словарь с полным списком лауреатов, метаданными API,
    адресом источника и датой загрузки в UTC.

Raises:
    ValueError: Если page_size меньше 1, API вернул
        пустую промежуточную страницу или количество
        записей не совпало с meta.count.
    requests.HTTPError: Если сервер вернул ошибочный
        HTTP-статус.
"""
    if page_size < 1:
        raise ValueError('Размер страницы должен быть положительным.')
    laureates = []
    offset = 0
    while True:
        response = requests.get(
            URL_LAUREATES,
            params={'limit': page_size, 'offset': offset},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        page = payload['laureates']
        laureates.extend(page)
        if not payload.get('links', {}).get('next'):
            break
        if not page:
            raise ValueError('API вернул пустую страницу перед концом данных.')
        offset += len(page)

    if len(laureates) != int(payload['meta']['count']):
        raise ValueError('Число записей не совпало с meta.count в ответе API.')
    return {
        'laureates': laureates,
        'meta': payload['meta'],
        'source': URL_LAUREATES,
        'downloaded_at': datetime.now(timezone.utc).isoformat(),
    }


def load_laureates(file_path=DATA_FILE, refresh: bool = False) -> dict:
    """
Загружаем данные из локального файла или обновляем их через API.

Сначала функция проверяет, существует ли JSON-файл с ранее загруженными 
данными.

Если файл найден и refresh=False, данные читаются непосредственно из 
него, что позволяет запускать проект повторно без обращения к интернету.

Если файла нет или refresh=True, функция скачивает актуальный набор 
данных через download_laureates, создаёт нужную папку и сохраняет 
результат в JSON.

Args:
    file_path: Путь к файлу с данными. По умолчанию
        используется data/laureates.json.
    refresh: Нужно ли принудительно скачать данные заново.

Returns:
    Словарь с данными лауреатов и метаданными загрузки.
"""
    file_path = Path(file_path)
    if file_path.exists() and not refresh:
        with open(file_path, encoding='utf-8') as source_file:
            return json.load(source_file)

    payload = download_laureates()
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as destination_file:
        json.dump(payload, destination_file, ensure_ascii=False, indent=2)
        destination_file.write('\n')
    return payload

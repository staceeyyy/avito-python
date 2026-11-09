"""
Конфигурации для обработки людей и организаций.

Nobel Prize API хранит сведения о лауреатах-людях и организациях немного 
по-разному. Например, у человека есть дата и место рождения, а у 
организации есть дата и место основания.

Поэтому для каждого типа лауреатов используется отдельная конфигурация. 
Она задаёт, какие поля нужно извлечь из JSON и как их преобразовать.

В результате получаются словари с удобными названиями полей, которые 
дальше будем использовать в анализе.
"""

from core import create_processor
from prizes_configs import prize_processor


def process_year(year_string):
    """
Извлекаем год из даты, полученной от Nobel Prize API.

В исходных данных даты представлены строками, например
'1970-05-12' или '1917-00-00'. При этом день и месяц могут быть 
неизвестны, но год всё равно можно использовать.

Функция берёт часть строки до первого дефиса и проверяет, что она 
состоит из цифр и не равна нулю.

Args:
    year_string: Строка с датой или другое значение,
        если дата отсутствует.

Returns:
    Год в формате int, если его удалось определить.
    В остальных случаях возвращается None.
"""
    if not isinstance(year_string, str):
        return None
    year = year_string.split('-')[0]
    if not year.isdigit() or int(year) == 0:
        return None
    return int(year)


CONFIG_PERSON = {
    'id': (['id'], int),
    'name': ['knownName', 'en'],
    'gender': ['gender'],
    'birth_year': (['birth', 'date'], process_year),
    'country_birth': ['birth', 'place', 'country', 'en'],
    'country_now': ['birth', 'place', 'countryNow', 'en'],
    'prizes_relevant': (['nobelPrizes'], prize_processor()),
}

CONFIG_ORG = {
    'id': (['id'], int),
    'name': ['orgName', 'en'],
    'founded_year': (['founded', 'date'], process_year),
    'country_founded': ['founded', 'place', 'country', 'en'],
    'country_now': ['founded', 'place', 'countryNow', 'en'],
    'prizes_relevant': (['nobelPrizes'], prize_processor()),
}


def person_processor():
    """
Создаем обработчик данных о лауреате-человеке.

Функция использует CONFIG_PERSON, где указаны поля, нужные для 
дальнейшего анализа: ID, имя, пол, год рождения, страна рождения, 
современная страна и информация о полученных премиях.

В результате у нас получается функция, которая может преобразовать 
исходный JSON одного человека в более удобный для анализа словарь.
"""
    return create_processor(CONFIG_PERSON)


def org_processor():
    """
Создаем обработчик данных об организации-лауреате.

Для организаций используется отдельная конфигурация CONFIG_ORG. 
В отличие от людей, здесь извлекаются год и страна основания, а не 
рождения.

Остальные поля, например ID, название, современная страна и информация о 
премиях, нужны для общего анализа всех лауреатов.
"""
    return create_processor(CONFIG_ORG)



process_persons = person_processor()
process_orgs = org_processor()

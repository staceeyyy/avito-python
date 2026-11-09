"""
Тут дополняем уже существующие записи результатами наших расчётов.
"""


def add_attribute(records: list, attribute: str, value_function) -> list:
    """
Добавляем новое поле в каждый словарь переданного списка.

Функция проходит по всем записям и для каждой вызывает value_function. 
Полученный результат записываем в новое поле с названием attribute.

Для каждой записи создаётся копия словаря, поэтому добавление поля не 
меняет исходный список данных. Копирование поверхностное.

Args:
    records: Список словарей, которые нужно дополнить.
    attribute: Название нового поля.
    value_function: Функция, которая получает один словарь
        и возвращает значение нового поля.

Returns:
    Новый список словарей с добавленным или обновлённым
    полем attribute.
"""
    updated_records = []
    for record in records:
        updated_record = record.copy()
        updated_record[attribute] = value_function(record)
        updated_records.append(updated_record)
    return updated_records

"""Запишем вспомогательные функции для анализа списков словарей."""


def filter_records(records: list, condition) -> list:
    """
Отберем записи, которые удовлетворяют заданному условию.

Функция проходит по списку словарей и применяет condition к каждой 
записи. Если условие возвращает True, запись добавляется в 
итоговый список.

Args:
    records: Исходный список словарей.
    condition: Функция, которая принимает один словарь
        и возвращает True или False.

Returns:
    Новый список записей, прошедших фильтрацию.
"""
    return [record for record in records if condition(record)]


def group_by_attributes(records: list, attributes: list) -> dict:
    """
Сгруппирую записи по значениям одного или нескольких полей.

Для каждой записи функция составляет ключ группы из значений полей, 
перечисленных в attributes. Ключ всегда хранится в виде кортежа, 
даже если группировка выполняется только по одному полю.

Записи с одинаковыми значениями выбранных полей попадают в одну группу.

Если нужного поля в записи нет, вместо его значения в ключ группы 
попадает None.

Args:
    records: Список словарей для группировки.
    attributes: Названия полей, определяющих группы.

Returns:
    Словарь, где ключ - это кортеж значений полей,
    а значение - это список записей соответствующей группы.
""" 
    groups = {}
    for record in records:
        key = tuple(record.get(attribute) for attribute in attributes)
        groups.setdefault(key, []).append(record)
    return groups


def apply_aggregations(records: list, aggregations: dict) -> dict:
    """
Рассчитываем несколько агрегированных показателей для записей.

Функция получает словарь aggregations, в котором каждому названию 
показателя соответствует функция расчёта.

Каждая из этих функций применяется к одному и тому же списку records. 
Результаты отправляются в общий словарь.

Args:
    records: Список записей, по которым считаем показатели.
    aggregations: Словарь вида {название: функция расчёта}.

Returns:
    Словарь с рассчитанными показателями и их названиями.
"""
    return {
        name: aggregation(records)
        for name, aggregation in aggregations.items()
    }


def summarize_groups(records: list, attributes: list,
                     aggregations: dict) -> list:
    """
Посчитаем агрегированные показатели отдельно для каждой группы.

Функция объединяет две операции: сначала группирует записи по указанным
полям, а затем рассчитывает переданные агрегаты внутри каждой группы.

Для каждой группы создаётся отдельный словарь. В нём сохраняются 
значения полей группировки и рассчитанные показатели.

Args:
    records: Исходный список словарей.
    attributes: Поля, по которым группируем записи.
    aggregations: Словарь функций для расчёта показателей.

Returns:
    Список словарей, где каждая запись содержит
    значения полей группировки и результаты агрегации.
"""
    summary = []
    for key, group in group_by_attributes(records, attributes).items():
        row = dict(zip(attributes, key))
        row.update(apply_aggregations(group, aggregations))
        summary.append(row)
    return summary


def is_missing(value) -> bool:
    """
Проверим, считается ли переданное значение пропуском.

Args:
    value: Значение, которое нужно проверить.

Returns:
    True, если значение считается пропущенным,
    и False в остальных случаях.
"""
    if value is None:
        return True
    return isinstance(value, (str, list, dict, tuple, set)) and not value


def count_missing(records: list) -> dict:
    """
Посчитаем количество пропусков в каждом поле датасета.

Сначала функция собирает все названия полей, которые встречаются 
хотя бы в одном словаре исходного списка.

Затем для каждого поля считает количество записей, в которых значение 
отсутствует или считается пустым по правилам is_missing.

Args:
    records: Список словарей с данными.

Returns:
    Словарь, где каждому полю соответствует количество
    пропущенных значений. Для пустого списка возвращается
    пустой словарь.
"""
    attributes = sorted({key for record in records for key in record})
    missing = dict.fromkeys(attributes, 0)
    for record in records:
        for attribute in attributes:
            if is_missing(record.get(attribute)):
                missing[attribute] += 1
    return missing

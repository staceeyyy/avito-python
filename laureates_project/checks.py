"""
Здесь будем проверять корректность качества данных, чтобы убедиться, что 
наши основные функции работают правильно, а загруженные данные подходят 
для дальнейшего анализа.

Сначала проверяем универсальные функции на небольших искусственных 
примерах, где заранее известен правильный результат. Затем будем 
отдельно проверять реальный датасет: количество записей, 
уникальность ID, обязательные поля и корректность дат.

Для проверок используются assert. Если какое-то условие не выполняется, 
программа останавливается с ошибкой.
"""

from aggregations import (
    count_records,
    max_value,
    mean_value,
    median_value,
    top_n,
)
from attribute_manager import add_attribute
from core import (
    create_processor,
    extract_nested_value,
    process_dictionary_with_config,
    process_list_of_dicts_with_config,
)
from dataset_helpers import (
    apply_aggregations,
    count_missing,
    filter_records,
    group_by_attributes,
    is_missing,
    summarize_groups,
)
from laureates_configs import process_orgs, process_persons, process_year


def run_checks() -> None:
    """
Функция создаёт небольшие примеры словарей и списков, у которых 
заранее известны ожидаемые результаты.

Затем проверяю извлечение вложенных значений, применение конфигураций, 
обработку дат, фильтрацию, группировки, расчёт статистик и работу с 
пропусками.

Отдельно проверю отсутствие нужного поля, пустые списки, 
нулевые значения, False и попытку обратиться к несуществующему элементу 
JSON.

Также проверяется, что добавление новых полей не меняет
исходные словари.

Все проверки выполняются через assert. Если хотя бы одна из них не 
проходит, возникает AssertionError.

Returns:
    None. При успешном выполнении все проверки
    завершаются без ошибок.
"""
    nested = {'outer': {'number': '12'}, 'items': [{'name': 'Alice'}]}
    config = {'number': (['outer', 'number'], int), 'missing': ['absent']}
    expected = {'number': 12, 'missing': None}
    assert extract_nested_value(nested, ['outer', 'number']) == '12'
    assert extract_nested_value(nested, ['outer', 'absent']) is None
    assert extract_nested_value(nested, ['absent', 'child']) is None
    assert extract_nested_value(nested, ['items', 0, 'name']) == 'Alice'
    assert extract_nested_value(nested, ['items', 2]) is None
    assert extract_nested_value(nested, ['outer', 'number', 'child']) is None
    assert extract_nested_value(nested, []) == nested
    assert process_dictionary_with_config(nested, config) == expected
    assert process_dictionary_with_config({}, config)['number'] is None
    assert process_list_of_dicts_with_config([nested], config) == [expected]
    assert process_list_of_dicts_with_config(None, config) == []
    assert create_processor(config)(nested) == expected
    list_processor = create_processor(config, list_processor=True)
    assert list_processor([nested]) == [expected]
    assert nested['outer']['number'] == '12'

    assert process_year('1917-00-00') == 1917
    assert process_year('2001-12-10') == 2001
    assert process_year('0000-00-00') is None
    assert process_year('unknown') is None
    assert process_year('') is None
    assert process_year(None) is None
    sample_person = process_persons({
        'id': '7', 'knownName': {'en': 'Alice'},
        'birth': {'date': '1970-01-01'},
        'nobelPrizes': [{'awardYear': '2000', 'category': {'en': 'Physics'}}],
    })
    assert sample_person['id'] == 7
    assert sample_person['birth_year'] == 1970
    assert sample_person['country_now'] is None
    assert sample_person['prizes_relevant'][0]['award_year'] == 2000
    assert sample_person['prizes_relevant'][0]['motivation'] is None
    sample_org = process_orgs({'id': '8', 'orgName': {'en': 'Example'}})
    assert sample_org['name'] == 'Example'
    assert sample_org['founded_year'] is None
    assert 'birth_year' not in sample_org

    records = [
        {'name': 'Alice', 'country': 'USA', 'age': 0},
        {'name': 'Bob', 'country': 'UK', 'age': 30},
        {'name': 'Charlie', 'country': 'USA', 'age': 0},
        {'name': 'Unknown', 'country': None, 'age': None},
    ]
    assert len(filter_records(records, lambda row: row['age'] == 0)) == 2
    groups = group_by_attributes(records, ['country', 'age'])
    assert groups[('USA', 0)] == [records[0], records[2]]
    assert groups[(None, None)] == [records[3]]
    assert count_records(records) == 4
    assert mean_value(records, 'age') == 10
    assert median_value(records, 'age') == 0
    assert max_value(records, 'age') == 30
    assert mean_value([], 'age') is None
    assert median_value([], 'age') is None
    assert max_value([], 'age') is None
    assert mean_value([{'age': False}, {'age': 4}], 'age') == 4
    assert top_n(records, 'age', 1)[0]['name'] == 'Bob'
    assert top_n(records, 'age', 1, reverse=False)[0]['age'] == 0
    assert top_n(records, 'age', 0) == []
    assert apply_aggregations(records, {'n': count_records}) == {'n': 4}
    summary = summarize_groups(records, ['country'], {'count': count_records})
    usa_summary = next(row for row in summary if row['country'] == 'USA')
    assert usa_summary['count'] == 2
    updated = add_attribute(
        records, 'name_length', lambda row: len(row['name']),
    )
    assert updated[0]['name_length'] == 5
    assert 'name_length' not in records[0]
    assert count_missing([{'a': 0, 'b': ''}, {'a': None}]) == {'a': 1, 'b': 2}
    assert count_missing([]) == {}
    assert not is_missing(0)
    assert not is_missing(False)
    assert is_missing([])
    assert is_missing({})


def validate_dataset(laureates: list, payload: dict) -> None:
    """
Проверяем, что загруженный датасет корректен и полон.

Функция выполняет проверки уже на реальных данных Нобелевских лауреатов 
после их обработки.

Сначала проверяется, что список не пустой, количество записей совпадает 
с meta.count из ответа API, а идентификаторы представлены целыми числами
и не повторяются.

Затем для каждого лауреата проверяются наличие имени, корректность типа
и наличие хотя бы одной премии.

Для наград дополнительно проверяются год вручения, категория, статус и 
положительные денежные суммы. Год премии должен находиться между 1901
годом и годом загрузки данных.

Если известен год рождения человека или основания организации, он должен 
быть положительным и не превышать год первой премии.

Args:
    laureates: Список уже обработанных лауреатов.
    payload: Исходный ответ API с метаданными
        и информацией о дате загрузки.

Returns:
    None. Функция ничего не возвращает, а проверяет
    выполнение заданных условий.

Raises:
    AssertionError: Если найдены некорректные значения,
        дубликаты ID или несоответствие количества записей.
"""
    assert laureates, 'Датасет пуст.'
    assert len(laureates) == int(payload['meta']['count']), 'Не все записи.'
    ids = [row['id'] for row in laureates]
    assert all(type(laureate_id) is int for laureate_id in ids), 'ID не числа.'
    assert len(ids) == len(set(ids)), 'Обнаружены повторяющиеся ID.'
    snapshot_year = int(payload['downloaded_at'][:4])
    for laureate in laureates:
        assert laureate['name'], 'У лауреата нет имени или названия.'
        assert laureate['type_'] in ('person', 'org'), 'Неизвестный тип.'
        prizes = laureate['prizes_relevant']
        assert prizes, 'У лауреата нет наград.'
        for prize in prizes:
            assert type(prize['award_year']) is int, 'Год премии не число.'
            assert 1901 <= prize['award_year'] <= snapshot_year, 'Неверный год'
            assert prize['category_en'], 'Нет категории награды.'
            assert prize['prize_status'], 'Нет статуса награды.'
            assert prize['prize_amount'] > 0, 'Некорректная сумма премии.'
            assert prize['prize_amount_adjusted'] > 0, 'Неверная сумма.'
        start_field = (
            'birth_year' if laureate['type_'] == 'person' else 'founded_year'
        )
        start_year = laureate[start_field]
        first_year = min(prize['award_year'] for prize in prizes)
        if start_year is not None:
            assert 0 < start_year <= first_year, 'Неверная дата начала жизни.'


if __name__ == '__main__':
    run_checks()
    print('Проверки на маленьких примерах пройдены.')

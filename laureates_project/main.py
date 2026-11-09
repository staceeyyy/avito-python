"""
Здесь будет проходить основной анализ данных о Нобелевских лауреатах.

В этом файле я объединила все этапы исследования: подготовка исходных 
данных, техническая проверка датасета, расчёт статистик и визуализация 
результатов.

Анализ был проведен по трём основным направлениям:
1. Страны рождения людей и основания организаций.
2. Возраст людей при получении первой Нобелевской премии.
3. Гендерное распределение лауреатов.

Дополнительно выполняю анализ английских текстов мотиваций вручения 
премий (подсчёт частот слов, очистка от стоп-слов и сравнение категорий).

Для расчётов использую вспомогательные модули проекта. 
Результаты выводятся в консоль, а графики и итоговые данные сохраняются 
в папку results/.
"""

import json
from pathlib import Path

from aggregations import (
    count_records,
    max_value,
    mean_value,
    median_value,
    top_n,
)
from attribute_manager import add_attribute
from checks import run_checks, validate_dataset
from data_loader import load_laureates
from dataset_helpers import (
    apply_aggregations,
    count_missing,
    filter_records,
    group_by_attributes,
    summarize_groups,
)
from laureates_configs import process_orgs, process_persons
from presentation import CATEGORY_LABELS, plot_bars, plot_lines, print_table
from stopwords import STOPWORDS


def get_laureate_data(laureate: dict) -> dict:
    """
Определяем тип лауреата и преобразовываем его данные.

В Nobel Prize API лауреатами могут быть как отдельные люди, так и 
организации. Т.к. структура их данных различается, сначала нужно 
определить тип записи.

Если в исходном словаре есть поле knownName, лауреат считается 
человеком и обрабатывается через process_persons. Если есть orgName, 
то он является организацией, для которой используется process_orgs.

После обработки в словарь добавляется поле type_, чтобы в дальнейшем 
можно было легко разделять людей и организации при расчёте статистик.

Args:
    laureate: Исходный словарь одного лауреата из API.

Returns:
    Обработанный словарь с нужными полями и типом лауреата.

Raises:
    ValueError: Если по структуре записи невозможно
        определить, человек это или организация.
"""
    if 'knownName' in laureate:
        processed = process_persons(laureate)
        processed['type_'] = 'person'
    elif 'orgName' in laureate:
        processed = process_orgs(laureate)
        processed['type_'] = 'org'
    else:
        raise ValueError('Не удалось определить тип лауреата.')
    return processed


def make_prize_rows(laureates: list) -> list:
    """
Создаем отдельную запись для каждого награждения.

В исходных данных один лауреат представлен одним словарём, внутри 
которого хранится список всех его Нобелевских премий.

Для некоторых задач удобнее анализировать не лауреатов, а сами 
награждения, поэтому функция будет разворачивать вложенный список 
prizes_relevant в отдельные записи.

К каждой награде добавляются ID и имя лауреата, его тип, пол, 
современная страна и десятилетие получения премии.

Args:
    laureates: Список обработанных лауреатов.

Returns:
    Список словарей, где одна запись соответствует
    одной премии конкретного лауреата.
"""
    prize_rows = []
    for laureate in laureates:
        for prize in laureate['prizes_relevant'] or []:
            row = prize.copy()
            row.update({
                'laureate_id': laureate['id'],
                'name': laureate['name'],
                'type_': laureate['type_'],
                'gender': laureate.get('gender'),
                'country_now': laureate['country_now'],
                'award_decade': prize['award_year'] // 10 * 10,
            })
            prize_rows.append(row)
    return prize_rows


def prepare_analysis_data(laureates: list) -> list:
    """
Подготавливаем дополнительные признаки для основного анализа.

Функция последовательно добавляет три новых поля.

first_award_year - год самой ранней Нобелевской премии конкретного 
лауреата.

first_decade - десятилетие этой премии, например 1990 для награждения 
в 1995 году.

age_first_prize - приблизительный возраст человека при получении первой 
премии. Он рассчитывается как разница между годом награждения и годом 
рождения, без учёта дня и месяца.

Очевидно, что организаций возраст не рассчитывается. Если год рождения
неизвестен, значение также остаётся None.

Новые поля добавляются через add_attribute, поэтому исходные словари не 
изменяются.

Args:
    laureates: Список обработанных людей и организаций.

Returns:
    Новый список словарей с тремя дополнительными полями.
"""
    prepared = add_attribute(
        laureates, 'first_award_year',
        lambda row: min(prize['award_year']
                        for prize in row['prizes_relevant']),
    )
    prepared = add_attribute(
        prepared, 'first_decade',
        lambda row: row['first_award_year'] // 10 * 10,
    )
    prepared = add_attribute(
        prepared, 'age_first_prize',
        lambda row: row['first_award_year'] - row['birth_year']
        if row['type_'] == 'person' and row['birth_year'] is not None
        else None,
    )
    return prepared


def make_category_rows(laureates: list) -> list:
    """
Создаю записи для анализа лауреатов по категориям премии.

Один лауреат может получать Нобелевскую премию несколько раз, в том 
числе в одной и той же категории.

Если просто считать все награждения, такой лауреат будет учитываться 
несколько раз. Так, функция создаёт отдельную запись для каждой 
уникальной пары «лауреат - категория».

Для этого премии одного лауреата группируются по категории. Если в одной 
категории было несколько наград, они объединяются в одну запись.

Дополнительно рассчитывается category_first_year - год первой премии 
лауреата именно в этой категории.

Args:
    laureates: Список подготовленных лауреатов
        с информацией обо всех премиях.

Returns:
    Список словарей, в котором каждый лауреат
    встречается не более одного раза в каждой категории.
"""
    category_rows = []
    for laureate in laureates:
        groups = group_by_attributes(laureate['prizes_relevant'],
                                     ['category_en'])
        for (category,), prizes in groups.items():
            row = laureate.copy()
            row['category_en'] = category
            row['category_first_year'] = min(
                prize['award_year'] for prize in prizes
            )
            category_rows.append(row)
    return category_rows


def technical_analysis(laureates: list, prize_rows: list) -> dict:
    """
Проводим технический анализ качества исходных данных.

Сначала функция выводит общее количество лауреатов и отдельных записей о 
награждениях.

Затем рассчитывают количество и доля пропусков по всем полям. 
Отдельно анализирую людей, организации и вложенные данные о премиях,
т.к. наборы их полей различаются.

После этого проверяются идентификаторы лауреатов: ищутся повторяющиеся 
ID, определяются минимальный и максимальный ID, а также промежутки между 
соседними ID, в которых есть пропущенные номера.

Args:
    laureates: Список обработанных лауреатов.
    prize_rows: Список отдельных записей о награждениях.

Returns:
    Словарь с количеством и долями пропусков,
    повторяющимися ID, промежутками между ID
    и информацией о крайних идентификаторах.
"""
    print('\nТехнический анализ:')
    print('Всего лауреатов:', len(laureates))
    print('Записей о награждении:', len(prize_rows))
    missing = count_missing(laureates)
    print('Пропуски по всем полям:', missing)
    shares = {
        field: round(count / len(laureates), 4)
        for field, count in missing.items()
    }
    print('Доли пропусков от 0 до 1:', shares)
    for laureate_type in ['person', 'org']:
        selected = filter_records(
            laureates, lambda row: row['type_'] == laureate_type,
        )
        print(laureate_type, '— записей:', len(selected),
              'пропуски:', count_missing(selected))

    prize_fields = [
        prize for laureate in laureates
        for prize in laureate['prizes_relevant'] or []
    ]
    print('Пропуски в полях наград:', count_missing(prize_fields))
    print('Доли пропусков в наградах:', {
        field: round(count / len(prize_fields), 4)
        for field, count in count_missing(prize_fields).items()
    })
    id_groups = group_by_attributes(laureates, ['id'])
    duplicates = sorted(key[0] for key, rows in id_groups.items()
                        if len(rows) > 1)
    sorted_ids = sorted(key[0] for key in id_groups)
    extremes = []
    for laureate_id in [sorted_ids[0], sorted_ids[-1]]:
        laureate = id_groups[(laureate_id,)][0]
        extremes.append({
            'id': laureate_id,
            'name': laureate['name'],
            'years': sorted(prize['award_year']
                            for prize in laureate['prizes_relevant']),
        })
    print_table(extremes, {'id': 'ID', 'name': 'Лауреат', 'years': 'Годы'})
    gaps = [
        (left, right) for left, right in zip(sorted_ids, sorted_ids[1:])
        if right - left > 1
    ]
    print('Повторяющиеся ID:', duplicates)
    print('Соседние ID с разницей больше 1:', gaps)
    print('Все значения заполнены:', not any(missing.values()))
    return {'missing': missing, 'missing_shares': shares,
            'duplicates': duplicates, 'gaps': gaps, 'extremes': extremes}


def analyze_countries(laureates: list, category_rows: list,
                      decades: list, figures_dir, show: bool = False) -> dict:
    """
Проанализируем распределение лауреатов по странам.

Для анализа используется поле country_now (современная страна места 
рождения человека или основания организации).

Сначала исключаются записи, для которых страна неизвестна. 
Затем рассчитывается количество уникальных лауреатов в каждой стране 
и определяется общий топ-5.

Далее для каждой категории Нобелевской премии строится отдельный рейтинг 
стран. Здесь используются category_rows, чтобы повторные награждения 
одного лауреата в одной категории не увеличивали счётчик.

Последним этапом здесь будет анализ динамики по десятилетия.
Для пяти ведущих стран считаем, сколько лауреатов впервые получили 
премию в каждом десятилетии.

В результате строятся два графика: общий рейтинг стран и динамика первых 
награждений по десятилетиям.

Args:
    laureates: Подготовленный список уникальных лауреатов.
    category_rows: Записи уникальных пар
        «лауреат - категория».
    decades: Список десятилетий для анализа.
    figures_dir: Папка для сохранения графиков.
    show: Нужно ли отображать графики на экране.

Returns:
    Словарь с общим топ-5 стран, рейтингами по категориям,
    динамикой по десятилетиям и количеством лауреатов
    с известной страной.
"""
    print('\n1. СТРАНЫ РОЖДЕНИЯ И ОСНОВАНИЯ')
    with_country = filter_records(
        laureates, lambda row: row['country_now'] is not None,
    )
    ranking = top_n(summarize_groups(
        with_country, ['country_now'], {'count': count_records},
    ), 'count')
    print('Страна известна:', len(with_country), 'из', len(laureates))
    print_table(ranking, {'country_now': 'Страна', 'count': 'Лауреатов'})

    by_category = []
    category_groups = group_by_attributes(category_rows, ['category_en'])
    for (category,), members in sorted(category_groups.items()):
        filled_members = filter_records(
            members, lambda row: row['country_now'] is not None,
        )
        leaders = top_n(summarize_groups(
            filled_members, ['country_now'], {'count': count_records},
        ), 'count')
        for leader in leaders:
            by_category.append({'category': category, **leader})
    print('\nТоп-5 в каждой категории (уникальные лауреаты внутри категории):')
    print_table(by_category, {'category': 'Категория', 'country_now': 'Страна',
                              'count': 'Лауреатов'})

    countries = [row['country_now'] for row in ranking]
    groups = group_by_attributes(with_country, ['first_decade', 'country_now'])
    by_decade = []
    for decade in decades:
        row = {'decade': decade}
        for country in countries:
            row[country] = len(groups.get((decade, country), []))
        by_decade.append(row)
    plot_bars(ranking, 'country_now', 'count',
              'Топ-5 стран: уникальные люди и организации', 'Лауреатов',
              Path(figures_dir) / 'countries_top5.png', show)
    plot_lines(by_decade, 'decade', dict(zip(countries, countries)),
               'Когда лауреаты стран топ-5 получили первую премию',
               'Лауреатов с первой премией в десятилетии',
               Path(figures_dir) / 'countries_decades.png', show)
    return {'top5': ranking, 'by_category': by_category,
            'by_decade': by_decade, 'known_country_count': len(with_country)}


def analyze_age(laureates: list, category_rows: list,
                decades: list, figures_dir, show: bool = False) -> dict:
    """
Исследую возраст лауреатов при получении первой премии.

В анализ включаются только люди, ведь возраст организаций здесь не
рассматривается.

Сначала отбираются лауреаты, для которых удалось рассчитать возраст при 
первой премии. Затем вычисляются основные статистики: количество людей,
средний возраст, медиана и максимальное значение.

Далее возраст сравнивается между категориями. Для этого учитываются 
только те категории, в которых человек получил свою самую первую премию.
Таким образом, повторное награждение в более позднем возрасте не влияет 
на результат.

После этого рассчитывается динамика возраста по десятилетиям первой 
премии, а также определяются пять самых молодых и пять самых старших 
лауреатов.

В конце строятся графики среднего возраста по категориям и изменения 
среднего и медианного возраста во времени.

Args:
    laureates: Подготовленный список лауреатов.
    category_rows: Записи по уникальным категориям лауреатов.
    decades: Список десятилетий для анализа.
    figures_dir: Папка для сохранения графиков.
    show: Нужно ли выводить графики на экран.

Returns:
    Словарь с общими статистиками возраста,
    результатами по категориям и десятилетиям,
    а также списками самых молодых и старших лауреатов.
"""
    print('\n2. ВОЗРАСТ ПРИ ПЕРВОЙ ПРЕМИИ')
    people = filter_records(laureates, lambda row: row['type_'] == 'person')
    with_age = filter_records(
        people, lambda row: row['age_first_prize'] is not None,
    )
    first_categories = filter_records(
        category_rows,
        lambda row: row['type_'] == 'person'
        and row['age_first_prize'] is not None
        and row['category_first_year'] == row['first_award_year'],
    )
    metrics = {
        'count': count_records,
        'mean_age': lambda rows: mean_value(rows, 'age_first_prize'),
        'median_age': lambda rows: median_value(rows, 'age_first_prize'),
        'max_age': lambda rows: max_value(rows, 'age_first_prize'),
    }
    total = apply_aggregations(with_age, metrics)
    print('Возраст известен:', len(with_age), 'из', len(people), 'людей')
    print_table([total], {'count': 'Людей', 'mean_age': 'Средний возраст',
                          'median_age': 'Медиана', 'max_age': 'Максимум'})
    by_category = sorted(
        summarize_groups(first_categories, ['category_en'], metrics),
        key=lambda row: row['mean_age'],
    )
    print_table(by_category, {'category_en': 'Первая категория',
                              'count': 'Людей', 'mean_age': 'Среднее',
                              'median_age': 'Медиана', 'max_age': 'Максимум'})
    groups = group_by_attributes(with_age, ['first_decade'])
    by_decade = []
    for decade in decades:
        summary = apply_aggregations(groups.get((decade,), []), metrics)
        by_decade.append({'decade': decade, **summary})
    print_table(by_decade, {'decade': 'Десятилетие', 'count': 'Людей',
                            'mean_age': 'Среднее', 'median_age': 'Медиана'})
    age_extremes = {}
    for title, reverse in [('Самые молодые', False), ('Самые старшие', True)]:
        leaders = top_n(with_age, 'age_first_prize', reverse=reverse)
        age_extremes[title] = leaders
        print('\n' + title)
        print_table(leaders, {'name': 'Лауреат', 'age_first_prize': 'Возраст',
                              'first_award_year': 'Год первой премии'})
    plot_bars(by_category, 'category_en', 'mean_age',
              'Средний возраст при первой премии по категориям',
              'Лет: год премии минус год рождения',
              Path(figures_dir) / 'age_categories.png', show)
    plot_lines(by_decade, 'decade',
               {'mean_age': 'Среднее', 'median_age': 'Медиана'},
               'Возраст при первой премии по десятилетиям', 'Лет',
               Path(figures_dir) / 'age_decades.png', show)
    return {'total': total, 'by_category': by_category,
            'by_decade': by_decade, 'extremes': age_extremes}


def gender_statistics(people: list) -> dict:
    """
Рассчитаем гендерное распределение среди лауреатов-людей.

Функция считает количество женщин и мужчин по значениям поля gender. 
Дополнительно определяется количество людей, у которых пол не указан как 
male или female.

Долю женщин будем рассчитывать только среди людей с известным полом, а 
не от общего количества записей, чтобы пропущенные или неизвестные 
значения не искажали полученный процент.

Args:
    people: Список словарей с данными о людях.

Returns:
    Словарь с общим количеством записей,
    количеством женщин, мужчин, неизвестных значений
    и процентом женщин среди людей с известным полом.

    Если пол неизвестен у всех, вместо процента
    возвращается None.
"""
    women = len(filter_records(
        people, lambda row: row.get('gender') == 'female',
    ))
    men = len(filter_records(people, lambda row: row.get('gender') == 'male'))
    known = women + men
    return {'count': len(people), 'women': women, 'men': men,
            'unknown': len(people) - known,
            'women_pct': 100 * women / known if known else None}


def analyze_gender(laureates: list, category_rows: list, prize_rows: list,
                   decades: list, figures_dir, show: bool = False) -> dict:
    """
Исследую гендерное распределение Нобелевских лауреатов.
(в анализ включаются только люди)

Сначала рассчитывается общее количество женщин и мужчин, а также доля 
женщин среди лауреатов с известным полом.

Затем гендерное распределение рассматривается отдельно по категориям 
премии. Для этого используются category_rows: если человек дважды 
получал премию в одной категории, он всё равно учитывается в ней 
только один раз.

Для анализа по десятилетиям применяю другой подход.Каждый человек 
учитывается один раз в каждом десятилетии, когда он получал хотя бы одну 
премию. Так, один лауреат может попасть в несколько десятилетий, но не 
будет повторно посчитан внутри одного.

Отдельно рассчитывается количество уникальных женщин по сочетаниям 
категории и десятилетия.

Также сравниваются первые и последние 20 лет в доступных данных. 
Учтем, что повторные награждения одной женщины в одной категории внутри 
периода не увеличивают количество лауреаток.

В конце строятся графики количества женщин по категориям и динамики по 
десятилетиям.

Args:
    laureates: Список уникальных лауреатов.
    category_rows: Записи уникальных пар
        «лауреат - категория».
    prize_rows: Список отдельных награждений.
    decades: Список десятилетий для анализа.
    figures_dir: Папка для сохранения графиков.
    show: Нужно ли отображать графики на экране.

Returns:
    Словарь с общим гендерным распределением,
    статистиками по категориям и десятилетиям,
    количеством женщин в категориях по десятилетиям
    и сравнением первых и последних 20 лет.
"""
    print('\n3. ГЕНДЕРНОЕ РАСПРЕДЕЛЕНИЕ')
    people = filter_records(laureates, lambda row: row['type_'] == 'person')
    category_people = filter_records(
        category_rows, lambda row: row['type_'] == 'person',
    )
    total = gender_statistics(people)
    print_table([total], {'count': 'Людей', 'women': 'Женщин', 'men': 'Мужчин',
                          'unknown': 'Пол неизвестен',
                          'women_pct': 'Женщин, %'})
    by_category = []
    category_groups = group_by_attributes(category_people, ['category_en'])
    for (category,), members in sorted(category_groups.items()):
        by_category.append({'category_en': category,
                            **gender_statistics(members)})
    print_table(by_category, {'category_en': 'Категория', 'women': 'Женщин',
                              'count': 'Людей', 'women_pct': 'Женщин, %'})
    person_prizes = filter_records(
        prize_rows, lambda row: row['type_'] == 'person',
    )
    unique_per_decade = [members[0] for members in group_by_attributes(
        person_prizes, ['laureate_id', 'award_decade'],
    ).values()]
    decade_groups = group_by_attributes(unique_per_decade, ['award_decade'])
    by_decade = [
        {'decade': decade,
         **gender_statistics(decade_groups.get((decade,), []))}
        for decade in decades
    ]
    print('\nКаждый человек учтён один раз в каждом десятилетии награждения:')
    print_table(by_decade, {'decade': 'Десятилетие', 'count': 'Людей',
                            'women': 'Женщин', 'women_pct': 'Женщин, %'})

    women_prizes = filter_records(
        person_prizes, lambda row: row['gender'] == 'female',
    )
    unique_category_decades = [members[0] for members in group_by_attributes(
        women_prizes, ['laureate_id', 'category_en', 'award_decade'],
    ).values()]
    groups = group_by_attributes(
        unique_category_decades, ['award_decade', 'category_en'],
    )
    categories = sorted(key[0] for key in category_groups)
    category_decades = []
    for decade in decades:
        row = {'decade': decade}
        for category in categories:
            row[category] = len(groups.get((decade, category), []))
        category_decades.append(row)
    print('\nУникальные женщины внутри каждой категории и десятилетия:')
    print_table(category_decades, {'decade': 'Декада', **{
        category: CATEGORY_LABELS[category] for category in categories
    }})

    first_year = min(row['award_year'] for row in prize_rows)
    last_year = max(row['award_year'] for row in prize_rows)
    periods = [(first_year, first_year + 19), (last_year - 19, last_year)]
    period_counts = []
    for start, end in periods:
        selected = filter_records(
            prize_rows, lambda row: row['gender'] == 'female'
            and start <= row['award_year'] <= end,
        )
        unique_people = [rows[0] for rows in group_by_attributes(
            selected, ['laureate_id', 'category_en'],
        ).values()]
        counts = group_by_attributes(unique_people, ['category_en'])
        for category in categories:
            period_counts.append({'period': f'{start}–{end}',
                                  'category_en': category,
                                  'women': len(counts.get((category,), []))})
    print('\nПервые и последние 20 лет в данных; повторные премии убраны:')
    print_table(period_counts, {'period': 'Период', 'category_en': 'Категория',
                                'women': 'Уникальных женщин'})
    plot_bars(top_n(by_category, 'women', number=len(by_category)),
              'category_en', 'women', 'Женщины-лауреаты по категориям',
              'Уникальных женщин внутри категории',
              Path(figures_dir) / 'gender_categories.png', show)
    plot_lines(by_decade, 'decade', {'women': 'Женщины'},
               'Число женщин по десятилетиям награждения', 'Женщин',
               Path(figures_dir) / 'gender_decades.png', show)
    return {'total': total, 'by_category': by_category, 'by_decade': by_decade,
            'category_decades': category_decades,
            'period_counts': period_counts}


def tokenize(text: str) -> list:
    """
Разбиваем текст мотивации на отдельные слова. Сначала весь текст 
приводится к нижнему регистру. Затем каждый символ, который не является 
буквой, заменяется пробелом. После этого строка разбивается на отдельные
слова.

Args:
    text: Исходный текст мотивации.

Returns:
    Список слов в нижнем регистре без знаков препинания.
"""
    letters = [character if character.isalpha() else ' '
               for character in text.lower()]
    return ''.join(letters).split()


def word_frequencies(documents: list, stopwords=None) -> dict:
    """
Посчитаем частоту каждого слова в наборе текстов мотиваций.

Функция проходит по всем документам и разбивает содержимое поля 
motivation на отдельные слова с помощью tokenize.

Для каждого слова подсчитывается общее количество его появлений во всех
текстах.

Если передан список или множество стоп-слов, они исключаются из расчёта.

Тут считаются именно вхождения слов, а не количество документов 
с этими словами, поэтому если слово встречается в одной мотивации
несколько раз, все его появления будут учтены.

Args:
    documents: Список словарей с полем motivation.
    stopwords: Необязательный набор слов для исключения.
        Если не указан, учитываются все слова.

Returns:
    Словарь вида {слово: количество_вхождений}.
"""
    if stopwords is None:
        stopwords = set()
    frequencies = {}
    for document in documents:
        for word in tokenize(document['motivation']):
            if word not in stopwords:
                frequencies[word] = frequencies.get(word, 0) + 1
    return frequencies


def most_frequent_words(frequencies: dict, number: int = 50) -> list:
    """
Получим рейтинг самых часто встречающихся слов.

Функция принимает словарь с частотами и сортирует его по убыванию
количества вхождений.

Если у нескольких слов одинаковая частота, они дополнительно сортируются 
по алфавиту. После сортировки выбирается заданное количество первых 
слов.

Args:
    frequencies: Словарь с количеством вхождений слов.
    number: Сколько слов нужно включить в рейтинг.

Returns:
    Список словарей с полями word и count,
    отсортированный по убыванию частоты.
"""
    ordered = sorted(frequencies.items(), key=lambda item: (-item[1], item[0]))
    return [{'word': word, 'count': count} for word, count in ordered[:number]]


def analyze_motivations(prize_rows: list, results_dir,
                        show: bool = False) -> dict:
    """
Проведу лингвистический анализ мотиваций Нобелевских премий.

Сначала из записей о награждениях отбираю только тех, у которых есть 
английский текст мотивации.

При этом одинаковая формулировка одной премии может повторяться у 
нескольких со-лауреатов. Чтобы не завышать частоты слов, такие повторы 
убираются по сочетанию года, категории и текста мотивации.

На основе уникальных текстов формирую корпус, который сохраняется в 
отдельный JSON-файл.

Затем рассчитывается топ-50 самых частых слов без предварительной 
очистки. Слова дополнительно помечаются как общеупотребительные или
содержательные.

После удаления стоп-слов строится новый топ-50,чтобы выделить слова, 
которые лучше отражают содержание мотиваций.

Далее для каждой категории премии определяется собственный топ-10 слов. 
Эти рейтинги сравниваются между собой через пересечение множеств, чтобы
найти слова, встречающиеся среди лидеров сразу нескольких категорий.

В конце строится график 15 самых частых слов после удаления стоп-слов.

Args:
    prize_rows: Список отдельных записей о награждениях.
    results_dir: Папка для сохранения корпуса и графика.
    show: Нужно ли отображать график на экране.

Returns:
    Словарь с количеством уникальных текстов,
    рейтингами слов до и после очистки, топ-10
    по категориям и их попарными пересечениями.
"""
    print('\nБонус:')
    with_text = filter_records(prize_rows, lambda row: bool(row['motivation']))
    groups = group_by_attributes(
        with_text, ['award_year', 'category_en', 'motivation'],
    )
    corpus = [
        {'award_year': year, 'category_en': category, 'motivation': motivation}
        for year, category, motivation in groups
    ]
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / 'motivations_corpus.json', 'w',
              encoding='utf-8') as corpus_file:
        json.dump(corpus, corpus_file, ensure_ascii=False, indent=2)
        corpus_file.write('\n')
    print('Награждений с текстом:', len(with_text), 'из', len(prize_rows))
    print('Текстов в корпусе после удаления общих формулировок:', len(corpus))
    original_top = most_frequent_words(word_frequencies(corpus))
    marked_top = add_attribute(
        original_top, 'word_kind',
        lambda row: 'общеупотребительное' if row['word'] in STOPWORDS
        else 'содержательное',
    )
    print('\nТоп-50 до очистки:')
    print_table(marked_top, {'word': 'Слово', 'count': 'Частота',
                             'word_kind': 'Тип слова'})
    cleaned_top = most_frequent_words(word_frequencies(corpus, STOPWORDS))
    print('\nТоп-50 после удаления стоп-слов:')
    print_table(cleaned_top, {'word': 'Слово', 'count': 'Частота'})

    category_top10 = {}
    category_top10_sets = {}
    for (category,), documents in sorted(group_by_attributes(
            corpus, ['category_en']).items()):
        leaders = most_frequent_words(
            word_frequencies(documents, STOPWORDS), 10,
        )
        category_top10[category] = leaders
        category_top10_sets[category] = {row['word'] for row in leaders}
    print('\nТоп-10 очищенных слов по категориям:')
    print_table([
        {'category': category,
         'words': ', '.join(row['word'] for row in words)}
        for category, words in category_top10.items()
    ], {'category': 'Категория', 'words': 'Слова по убыванию частоты'})

    intersections = []
    categories = sorted(category_top10_sets)
    for index, first in enumerate(categories):
        for second in categories[index + 1:]:
            common = category_top10_sets[first] & category_top10_sets[second]
            intersections.append({'first': first, 'second': second,
                                  'words': ', '.join(sorted(common)) or 'нет'})
    print('\nПересечения множеств топ-10:')
    print_table(intersections, {'first': 'Категория 1',
                                'second': 'Категория 2',
                                'words': 'Общие слова'})
    plot_bars(cleaned_top[:15], 'word', 'count',
              'Топ-15 слов мотиваций после удаления стоп-слов',
              'Вхождений в корпус',
              results_dir / 'figures' / 'motivation_words.png', show)
    return {'corpus_count': len(corpus), 'original_top50': marked_top,
            'cleaned_top50': cleaned_top, 'category_top10': category_top10,
            'intersections': intersections}


def main() -> None:
    """
Это основная функция проекта, которая последовательно объединяет все 
этапы исследования.

Сначала запускаются тесты универсальных функций через run_checks. 
Затем данные загружаются из JSON или API и преобразуются в единый формат 
для людей и организаций.

После подготовки выполняется дополнительная проверка качества датасета 
(уникальность ID, корректность обязательных полей и дат).

Далее создаются отдельные записи о награждениях, определяется временной 
диапазон данных и формируется список десятилетий для анализа.

На следующем этапе выполняется технический анализ, рассчитываются 
дополнительные признаки и создаются записи по уникальным категориям
лауреатов.

После этого последовательно запускаются исследования стран, возраста, 
гендерного распределения и мотиваций.

Все числовые результаты собираются в общий словарь и сохраняются в 
results/summary.json. Графики и корпус текстов также записываются в 
папку results/.

Returns:
    None. Результаты выводятся в консоль и сохраняются в файлы.
"""
    run_checks()
    payload = load_laureates()
    laureates = [get_laureate_data(row) for row in payload['laureates']]
    validate_dataset(laureates, payload)
    prize_rows = make_prize_rows(laureates)
    first_year = min(row['award_year'] for row in prize_rows)
    last_year = max(row['award_year'] for row in prize_rows)
    decades = list(range(first_year // 10 * 10, last_year // 10 * 10 + 1, 10))
    print('Источник:', payload['source'])
    print('Снимок загружен (UTC):', payload['downloaded_at'])
    print('Годы награждения:', first_year, '—', last_year)
    print('country_now - современная страна места рождения/основания.')
    print('Возраст = год первой премии − год рождения; без дней и месяцев.')
    print('Последнее десятилетие неполное; организации исключены из возраста')
    print('и гендера. Учитываются все статусы наград, включая отказы.')
    technical = technical_analysis(laureates, prize_rows)
    prepared = prepare_analysis_data(laureates)
    category_rows = make_category_rows(prepared)
    results_dir = Path(__file__).resolve().parent / 'results'
    figures_dir = results_dir / 'figures'
    countries = analyze_countries(
        prepared, category_rows, decades, figures_dir,
    )
    age = analyze_age(prepared, category_rows, decades, figures_dir)
    gender = analyze_gender(prepared, category_rows, prize_rows,
                            decades, figures_dir)
    motivations = analyze_motivations(prize_rows, results_dir)
    results = {'technical': technical, 'countries': countries, 'age': age,
               'gender': gender, 'motivations': motivations}
    summary_file = results_dir / 'summary.json'
    with open(summary_file, 'w', encoding='utf-8') as result_file:
        json.dump(results, result_file, ensure_ascii=False, indent=2)
        result_file.write('\n')
    print('\nТаблицы выше, графики и корпус сохранены в results/.')


if __name__ == '__main__':
    main()

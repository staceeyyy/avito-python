"""
Здесь напишем функции для удобного представления результатов анализа.

Модуль отвечает за вывод таблиц в консоль и построение графиков 
с помощью matplotlib.

Здесь собраны общие настройки отображения, чтобы не повторять одинаковый 
код в каждом разделе исследования.

Также предусмотрено преобразование названий категорий Нобелевской 
премии с английского на русский язык.
"""

from pathlib import Path

import matplotlib.pyplot as plt

CATEGORY_LABELS = {
    'Chemistry': 'Химия',
    'Economic Sciences': 'Экономика',
    'Literature': 'Литература',
    'Peace': 'Мир',
    'Physics': 'Физика',
    'Physiology or Medicine': 'Физиология и медицина',
}


def format_value(value) -> str:
    """
Преобразуем значение в удобный для вывода текст.

Функция используется при формировании таблиц, чтобы значения разных 
типов отображались одинаково.

Числа с плавающей точкой округляются до двух знаков после запятой, 
а отсутствующие значения None заменяются на понятную надпись 
«нет данных».

Остальные значения преобразуются в строки без дополнительной обработки.

Args:
    value: Значение, которое нужно отобразить.

Returns:
    Строка с отформатированным значением.
"""
    if value is None:
        return 'нет данных'
    if isinstance(value, float):
        return f'{value:.2f}'
    return str(value)


def print_table(records: list, columns: dict) -> None:
    """
Выводим список словарей в виде читаемой таблицы.

Функция получает записи и словарь columns, в котором указано, какие поля 
нужно показать и как назвать соответствующие столбцы.

Сначала все значения преобразуются в текст с помощью format_value. 
Затем для каждого столбца определяется ширина с учётом заголовка и 
самого длинного значения.

После этого таблица печатается в консоль с выравниванием столбцов и 
разделительной строкой.

Args:
    records: Список словарей, которые нужно вывести.
    columns: Словарь вида {название_поля: заголовок}.

Returns:
    None. Функция печатает таблицу в консоль.
"""
    headings = list(columns.values())
    rows = [
        [format_value(record.get(field)) for field in columns]
        for record in records
    ]
    widths = [
        max(len(heading), *(len(row[index]) for row in rows))
        if rows else len(heading)
        for index, heading in enumerate(headings)
    ]
    print(' | '.join(
        heading.ljust(width) for heading, width in zip(headings, widths)
    ))
    print('-+-'.join('-' * width for width in widths))
    for row in rows:
        print(' | '.join(
            value.ljust(width) for value, width in zip(row, widths)
        ))


def plot_bars(records: list, label_field: str, value_field: str,
              title: str, xlabel: str, figure_path, show: bool = False):
    """
Построим горизонтальную столбчатую диаграмму.

Функция берёт из каждой записи название категории и соответствующее 
числовое значение, после чего строит горизонтальные столбцы.

Если категория есть в CATEGORY_LABELS, для подписи используется её
русское название.

Рядом со столбцами отображаются значения показателя, а порядок категорий 
соответствует порядку входных записей.

Размер графика подстраивается под количество категорий. Готовый график 
сохраняется в PNG через finish_figure.

Args:
    records: Список словарей с данными для графика.
    label_field: Поле с названиями категорий.
    value_field: Поле с числовыми значениями.
    title: Заголовок графика.
    xlabel: Подпись горизонтальной оси.
    figure_path: Путь для сохранения изображения.
    show: Нужно ли дополнительно показать график на экране.

Returns:
    None. График сохраняется в файл.
"""
    labels = [
        CATEGORY_LABELS.get(record[label_field], str(record[label_field]))
        for record in records
    ]
    numbers = [record[value_field] for record in records]
    figure, axis = plt.subplots(figsize=(9, max(3.5, len(labels) * 0.4)))
    bars = axis.barh(labels, numbers, color='#286a8b')
    axis.invert_yaxis()
    axis.bar_label(bars, labels=[format_value(value) for value in numbers],
                   padding=4)
    axis.set_title(title, loc='left', fontsize=12)
    axis.set_xlabel(xlabel)
    axis.set_xlim(0, max(numbers, default=1) * 1.2 or 1)
    axis.grid(axis='x', alpha=0.2)
    axis.set_axisbelow(True)
    finish_figure(figure, figure_path, show)


def plot_lines(records: list, x_field: str, series: dict, title: str,
               ylabel: str, figure_path, show: bool = False):
    """
Построим линейный график для сравнения нескольких показателей.

Функция отображает динамику одного или нескольких показателей по общей 
горизонтальной оси.

Для каждой линии используются значения отдельного поля из records. 
Названия линий задаются через series и отображаются в легенде.

Если в каком-то периоде значение отсутствует и равно None, оно не 
заменяется нулём, ведь на графике такой участок может отображаться как 
разрыв.

В проекте функция используется для анализа динамики по десятилетиям.

Args:
    records: Список словарей с данными.
    x_field: Поле со значениями горизонтальной оси.
    series: Словарь вида {поле: название_линии}.
    title: Заголовок графика.
    ylabel: Подпись вертикальной оси.
    figure_path: Путь для сохранения графика.
    show: Нужно ли вывести график на экран.

Returns:
    None. График сохраняется в PNG.
"""
    figure, axis = plt.subplots(figsize=(10, 4.5))
    x_values = [record[x_field] for record in records]
    markers = ['o', 's', '^', 'D', 'v', 'P']
    for index, (field, label) in enumerate(series.items()):
        y_values = [record.get(field) for record in records]
        axis.plot(x_values, y_values, marker=markers[index % len(markers)],
                  label=label, markersize=4)
    axis.set_title(title, loc='left', fontsize=12)
    axis.set_xlabel('Начало десятилетия; последнее десятилетие неполное')
    axis.set_ylabel(ylabel)
    axis.set_xticks(x_values)
    axis.tick_params(axis='x', rotation=45)
    axis.grid(alpha=0.2)
    axis.legend(loc='best')
    finish_figure(figure, figure_path, show)


def finish_figure(figure, figure_path, show: bool) -> None:
    """
Завершить оформление графика и сохранить его в файл.

Функция создаёт папку для изображения, если её ещё нет, после чего 
настраивает расположение элементов графика, чтобы подписи не обрезались.
График сохраняется в PNG.

Args:
    figure: Объект графика matplotlib.
    figure_path: Путь, по которому нужно сохранить PNG.
    show: Нужно ли дополнительно отображать график.

Returns:
    None.
"""
    figure_path = Path(figure_path)
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(figure_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    plt.close(figure)

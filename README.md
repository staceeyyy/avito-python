# Академия Аналитиков Авито. Курс по Python.
Здесь сохранены домашние задания по курсу Python в рамках Академии Аналитиков Авито.


### Структура проекта

- `my_avito_python` - ДЗ №1: пять задач на применение стандартных методов в папке `homework_1`.
- `homework2-corp-reports` - ДЗ №2: обработка данных сотрудников в папке `homework2`.
- `main` - основная ветка репозитория.
- `.gitignore` - исключение временных и служебных файлов из Git.
- `README.md` - описание проекта, требования и инструкции по запуску.

### Требования

Python 3. Дополнительные библиотеки не требуются.

### Установка

```bash
git clone https://github.com/staceeyyy/avito-python.git
cd avito-python
```

### Запуск

*ДЗ №1:*

```bash
git switch my_avito_python
python "homework_1/дз1№1.py"
```

Остальные задачи запускаются аналогично (`дз1№2.py` - `дз1№5.py`).

*ДЗ №2:*

```bash
git switch homework2-corp-reports
python homework2/corp_reports.py
```

Читаем `homework2/Corp_Summary.csv` и формируем три отчёта:

1. Иерархия департаментов и отделов.
2. Статистика зарплат по департаментам.
3. CSV-файл `homework2/department_stats.csv` со сводной статистикой.

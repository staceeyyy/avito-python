# Анализ Нобелевских лауреатов

Проект посвящён анализу данных Нобелевских лауреатов по трём направлениям: страны происхождения, возраст при получении первой премии и гендерное распределение. Дополнительно проведён анализ текстов мотиваций награждения.

## Установка и запуск

Требуется Python 3.10+.

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```

Запуск анализа:

```bash
python main.py
```

Для запуска Jupyter Notebook:

```bash
python -m pip install jupyter
jupyter lab laureates_countries_solution.ipynb
```

Ноутбук необходимо запускать из папки проекта, поскольку он использует функции из отдельных `.py`-модулей.

## Структура проекта

- `laureates_countries_solution.ipynb` - основной анализ, графики и выводы.
- `main.py` - самостоятельная версия анализа.
- `data_loader.py`, `data/laureates.json` - загрузка и хранение данных API.
- `json_dict_processing.py`, `core.py`, `laureates_configs.py`, `prizes_configs.py` - обработка JSON.
- `dataset_helpers.py`, `aggregations.py`, `attribute_manager.py` - фильтрация, группировки и расчёты.
- `presentation.py`, `stopwords.py` - визуализация и обработка текстов.
- `checks.py` - проверка корректности функций и данных.
- 
Результаты сохраняются в `results/`: семь графиков, итоговые расчёты и корпус мотиваций.

## Проверка кода

```bash
python checks.py
python -m pip install flake8
python -m flake8 .
```

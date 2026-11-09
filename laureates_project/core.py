"""
Здесь сохранен общий интерфейс для работы с обработчиками JSON.

В этом файле собраны импорты основных функций из 
json_dict_processing.py, чтобы остальные модули могли получать нужные 
инструменты через core, не обращаясь напрямую к их реализации.

Список __all__ явно задаёт функции, которые считаются публичной частью 
модуля.
"""

from json_dict_processing import (
    create_processor,
    extract_nested_value,
    process_dictionary_with_config,
    process_list_of_dicts_with_config,
)

__all__ = [
    'create_processor',
    'extract_nested_value',
    'process_dictionary_with_config',
    'process_list_of_dicts_with_config',
]

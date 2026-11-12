import csv
from collections import defaultdict
from pathlib import Path


def read_file():
    path = Path(__file__).parent / "Corp_Summary.csv"
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))


def report1(data):  # создаем функцию иерархию департаментов
    # cоздаём словарь, в котором ключ - название департамента,
    # а значение - множество команд этого департамента
    departments = defaultdict(set)
    for i in data:  # проходим по всем сотрудникам
        # добавляем команду сотрудника в его департамент
        departments[i["Департамент"]].add(i["Отдел"])
    # перебираем департаменты в алфавитном порядке
    for dep, teams in sorted(departments.items()):
        # выводим департамент и отсортированные команды через запятую
        print(dep, ":", ", ".join(sorted(teams)))


def stats(data):  # создаем функцию расчета статистики
    # создаём словарь со списками зарплат по департаментам
    departments = defaultdict(list)
    for i in data:
        # преобразуем оклад в число и добавляем его
        # в список зарплат департамента
        departments[i["Департамент"]].append(int(i["Оклад"]))
    # считаем название, количество сотрудников, минимальный,
    # максимальный и средний оклад
    # (все расчеты в алфавитном порядке)
    return [
        [dep, len(s), min(s), max(s), round(sum(s) / len(s), 2)]
        for dep, s in sorted(departments.items())
    ]


def report2(data):  # итоговая функция сводки по департаментам
    for i in stats(data):
        print(*i, sep=" | ")


def report3(data):  # создаем функцию сохранения csv
    path = Path(__file__).parent / "department_stats.csv"
    # открываем csv для записи
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        # создаём объект для записи csv с разделителем ;
        writer = csv.writer(f, delimiter=";")
        # записываем строку с названиями столбцов
        writer.writerow([
            "Департамент", "Количество", "Минимум", "Максимум", "Среднее"
        ])
        # записываем все строки рассчитанной статистики
        writer.writerows(stats(data))
    print("Отчёт сохранён в department_stats.csv")


def main(report_number: int):
    # создаём главную функцию, принимающую номер отчёта
    data = read_file()
    if report_number == 1:
        report1(data)
    elif report_number == 2:
        report2(data)
    elif report_number == 3:
        report3(data)
    else:
        print("Такого номера отчета не существует")


if __name__ == "__main__":
    print("Отчет 1:")
    main(1)
    print("Отчет 2:")
    main(2)
    print("Отчет 3:")
    main(3)

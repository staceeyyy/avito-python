import csv
from collections import defaultdict
from pathlib import Path

def read_file():
    path = Path(__file__).parent / "Corp_Summary.csv"
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f, delimiter=";"))

def report1(data): #создаем функцию иерархию департаментов
    departments = defaultdict(set) #cоздаём словарь, в котором ключ - название департамента, а значение - множество команд этого департамента
    for i in data: #проходим по всем сотрудникам
        departments[i["Департамент"]].add(i["Отдел"]) #добавляем команду сотрудника в его департамент
    for dep, teams in sorted(departments.items()): #перебираем департаменты в алфавитном порядке
        print(dep, ":", ", ".join(sorted(teams))) #выводим департамент и отсортированные команды через запятую

def stats(data): #создаем функцию расчета статистики
    departments = defaultdict(list) #создаём словарь со списками зарплат по департаментам
    for i in data:
        departments[i["Департамент"]].append(int(i["Оклад"])) #преобразуем оклад в число и добавляем его в список зарплат департамента
    return [[dep, len(s), min(s), max(s), round(sum(s) / len(s), 2)] for dep, s in sorted(departments.items())] #считаем название, количество сотрудников, минимальный, максимальный и средний оклад (все расчеты в алфавитном порядке)

def report2(data): #итоговая функция сводки по департаментам
    for i in stats(data):
        print(*i, sep=" | ")

def report3(data): #создаем функцию сохранения csv
    path = Path(__file__).parent / "department_stats.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as f: #открываем csv для записи
        writer = csv.writer(f, delimiter=";") #создаём объект для записи csv с разделителем ;
        writer.writerow(["Департамент", "Количество", "Минимум", "Максимум", "Среднее"]) #записываем строку с названиями столбцов
        writer.writerows(stats(data)) #записываем все строки рассчитанной статистики
    print("Отчёт сохранён в department_stats.csv")

def main(report_number: int): #создаём главную функцию, принимающую номер отчёта
    data = read_file()
    if report_number == 1:
        report1(data)
    elif report_number == 2:
        report2(data)
    elif report_number == 3:
        report3(data)
    else:
        print("Такого номера отчета не существует")
print("Отчет 1:")        
main(1)
print("Отчет 2:")
main(2)
print("Отчет 3:")
main(3)

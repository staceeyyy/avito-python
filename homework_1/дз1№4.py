if __name__ == '__main__':
    days = [
        {"day": "пн", "orders": 20, "revenue": 40_000, "returns": 2},
        {"day": "вт", "orders": 16, "revenue": 19_200, "returns": 4},
        {"day": "ср", "orders": 25, "revenue": 55_000, "returns": 1},
        {"day": "чт", "orders": 10, "revenue": 12_000, "returns": 3},
        {"day": "пт", "orders": 30, "revenue": 48_000, "returns": 3},
    ]
    week_revenue = 0
    for day in days: 
        week_revenue += day['revenue']
    print(f"1. Выручка за всю неделю: {week_revenue}")

    max_revenue= max(days, key = lambda day: day['revenue'])
    print(f"2. День с самой большой выручкой: {max_revenue['day']}")

    print(f"3. Средняя выручка на один заказ каждый день:")
    for day in days: 
        print(f"{day['day']} - {day['revenue']/day['orders']}")

    lst = []
    for day in days: 
        if day['returns']/day['orders'] > 0.2: 
            lst.append(day['day'])
    print(f"4. Дни, где возвратов больше 20% заказов: {lst}")

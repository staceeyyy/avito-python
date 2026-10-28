from collections import Counter


if __name__ == "__main__":
    queries = [
        "чехол",
        "iphone",
        "чехол",
        "наушники",
        "iphone",
        "iphone",
        "кабель",
        "чехол",
        "iphone",
    ]

    print(f"1. Количество поисковых запросов в ленте: {len(queries)}")

    counter = Counter(queries)
    print("2. Сколько раз ввели каждый запрос?")
    for key, item in counter.items():
        print(f"{key} - {item}")

    print(
        "3. Запрос с наибольшим количеством вводов: "
        f"{max(counter, key=counter.get)}"
    )
    print(
        "4. Доля, которую занимает запрос с наибольшим количеством "
        "вводов среди всех поисков: "
        f"{max(counter.values()) / len(queries)}"
    )

    single_queries = []
    for key, item in counter.items():
        if item == 1:
            single_queries.append(key)

    print(f"5. Запросы, которые встретились один раз: {single_queries}")

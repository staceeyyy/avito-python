from collections import Counter
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
print(f"3. Запрос с наибольшим количеством вводов: {max(counter, key = counter.get)}")
print(f"4. Доля, которую занимает запрос с наибольшим количеством вводов среди всех поисков: {(max(counter.values())) / len(queries)}")
lst = [] 
for key, item in counter.items(): 
    if item == 1:
        lst.append(key)
print(f"5. Запросы, которые встретились один раз: {lst}")

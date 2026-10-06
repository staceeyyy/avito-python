reviews = [
    {"id": 1, "product": "Чехол", "stars": 5},
    {"id": 1, "product": "Чехол", "stars": 3},
    {"id": 1, "product": "Чехол", "stars": 4},
    {"id": 2, "product": "Наушники", "stars": 2},
    {"id": 2, "product": "наушники", "stars": 2},
    {"id": 2, "product": "НАУШНИКИ", "stars": 5},
    {"id": 3, "product": "Планшет", "stars": 5},
    {"id": 4, "product": "Колонка", "stars": 4},
    {"id": 4, "product": "Колонка", "stars": 4},
    {"id": 5, "product": "Кабель", "stars": 1},
]
for review in reviews:
    review['product'] = review['product'].lower()

stars_sum = {}
reviews_cnt = {}
for review in reviews: 
    product = review['product']

    if product not in stars_sum: 
        stars_sum[product] = 0
        reviews_cnt[product] = 0

    stars_sum[product] += review['stars']
    reviews_cnt[product] += 1

average_stars = {}
for product in stars_sum:
    average_stars[product] = stars_sum[product] / reviews_cnt[product]

print("1. Средняя оценка каждого товара:")
for product, average in average_stars.items():
    print(f"{product} - {average}")

products_two_reviews = {}
for product, average in average_stars.items():
    if reviews_cnt[product] >= 2:
        products_two_reviews[product] = average

worst_product = min(products_two_reviews, key=products_two_reviews.get)
print(f"2. Худший товар по средней оценке среди тех, у кого хотя бы два отзыва: {worst_product}")

bad_reviews_count = 0
for review in reviews:
    if review["stars"] == 1 or review["stars"] == 2:
        bad_reviews_count += 1

print(f"3. Количество отзывов на 1 или 2 звезды: {bad_reviews_count}")
print(f"4. Доля отзывов на 1 или 2 звезды: {bad_reviews_count / len(reviews)}")

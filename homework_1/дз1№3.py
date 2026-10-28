if __name__ == '__main__':
    orders = [
        {"id": 1, "buyer": "anya", "status": "delivered", "amount": 900},
        {"id": 2, "buyer": "boris", "status": "returned", "amount": 4_500},
        {"id": 3, "buyer": "anya", "status": "delivered", "amount": 1_500},
        {"id": 4, "buyer": "vera", "status": "delivered", "amount": 3_200},
        {"id": 5, "buyer": "boris", "status": "delivered", "amount": 700},
        {"id": 6, "buyer": "gleb", "status": "returned", "amount": 2_100},
    ]

    total_returned_price = 0 
    for order in orders: 
        if order["status"] == "returned":
            total_returned_price += order["amount"]
    print(f"1. Возвраты были оформлены на {total_returned_price} рублей")
    who_returned = []
    for order in orders: 
        if order["status"] == "returned":
            who_returned.append(order["buyer"])
    print(f"2. Покупатели, которые хотя бы раз вернули заказ: {who_returned}")
    delivered_count = 0
    for order in orders: 
        if order["status"] == "delivered":
            delivered_count += 1
    print(f"3. Количество доставленных заказов: {delivered_count}")
    total_delivered_price = 0
    for order in orders: 
        if order["status"] == "delivered":
            total_delivered_price += order["amount"]
    print(f"4. Средний чек доставленных заказов: {total_delivered_price / delivered_count}")
        

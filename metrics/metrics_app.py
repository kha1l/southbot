from database.postgres import Database
import requests
from datetime import datetime, time, date


def revenue(units):
    db = Database()
    created_after = date.today()
    created_before = datetime.now()
    crb = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    cra = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    token = db.get_tokens()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token[0][2]}',

    }
    url_hand = 'https://api.dodois.io/dodopizza/ru/production/orders-handover-time'
    for unit in units:
        data = {
            'from': cra,
            'to': crb,
            'units': unit[0]
        }
        url = f'https://publicapi.dodois.io/ru/api/v1/OperationalStatisticsForTodayAndWeekBefore/{unit[1]}'
        link = f'https://publicapi.dodois.io/ru/api/v1/unitinfo/' \
               f'{unit[1]}/dailyrevenue/{created_after.year}/{created_after.month}/{created_after.day}'
        response = requests.get(url, headers=headers)
        response_link = requests.get(link, headers=headers)
        mobile_orders = 0
        delivery_orders = 0
        try:
            orders = response_link.json()
            try:
                order = orders['UnitRevenue'][0]
                mobile_orders = int(order['StationaryMobileCount'])
                delivery_orders = int(order['DeliveryCount'])
            except IndexError:
                mobile_orders = 0
                delivery_orders = 0
        except requests.exceptions.JSONDecodeError:
            pass
        today = response.json()['today']
        week = response.json()['weekBeforeToThisTime']
        rev_t = today['revenue']
        rev_w = week['revenue']

        resp = requests.get(url_hand, params=data, headers=headers)
        handover_time = resp.json()['ordersHandoverTime']
        sum_time = 0
        cnt = 0
        for hand in handover_time:
            if hand['salesChannel'] == 'Dine-in':
                cooking = hand['cookingTime']
                cnt += 1
                sum_time += cooking
        try:
            mean_time = round(sum_time / cnt)
        except ZeroDivisionError:
            mean_time = 0
        avg = change_time(mean_time)
        db.add_revenue(unit[2], rev_t,  rev_w, avg, mobile_orders, delivery_orders)


def delivery_stats(units):
    db = Database()
    unt = []
    created_after = date.today()
    created_before = datetime.now()
    crb = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    cra = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    token = db.get_tokens()
    for unit in units:
        unt.append(unit[0])
    units_str = ','.join(unt)
    for i in token:
        url = 'https://api.dodois.io/dodopizza/ru/delivery/statistics/'
        data = {
            'from': cra,
            'to': crb,
            'units': units_str
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {i[2]}'
        }
        response = requests.get(url, params=data, headers=headers)
        for j in response.json()['unitsStatistics']:
            rest = j['unitName']
            avg_delivery = change_time(j['avgDeliveryOrderFulfillmentTime'])
            cooking = change_time(j['avgCookingTime'])
            shelf = change_time(j['avgHeatedShelfTime'])
            avg_trip = change_time(j['avgOrderTripTime'])
            db.add_stats(rest, avg_delivery, cooking, shelf, avg_trip)


def change_time(metric):
    hour = int(metric // 3600)
    minute = int((metric - hour * 3600) // 60)
    second = round((metric - hour * 3600) % 60)
    res = str(time(hour=hour, minute=minute, second=second))
    return res


def check_rest(units):
    db = Database()
    created_after = date.today()
    created_before = datetime.now()
    crb = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    cra = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    token = db.get_tokens()
    for unit in units:
        total = 0
        count = 0
        url = 'https://api.dodois.io/dodopizza/ru/accounting/sales'
        data = {
            'from': cra,
            'to': crb,
            'units': unit[0]
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token[0][2]}',

        }
        response = requests.get(url, params=data, headers=headers)
        print(response.text)
        for i in response.json()['sales']:
            channel = i['salesChannel']
            products = i['products']
            if channel == 'Dine-in':
                count += 1
                for product in products:
                    total += product['priceWithDiscount']
        try:
            avg_check = round(total / count, 2)
        except ZeroDivisionError:
            avg_check = 0
        db.update_metrics(unit[2], avg_check)


def metrics():
    db = Database()
    db.drop_metrics_rev()
    db.drop_metrics_stats()
    units = db.get_units()
    revenue(units)
    delivery_stats(units)
    check_rest(units)

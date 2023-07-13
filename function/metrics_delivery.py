from database.psql import Database
from datetime import datetime, date, timedelta
from function.api import post_api
from function.metrics_rest import change_time
from config.conf import Config


async def delivery_stats():
    db = Database()
    cfg = Config()
    unt = []
    created_after = date.today()
    created_before = datetime.now()
    crb = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    cra = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    orders = db.select_orders('delivery')
    uuids = db.select_uuid()
    token = db.get_token()
    for unit in uuids:
        unt.append(unit[0])
    units_str = ','.join(unt)
    delivery = await post_api(f'https://api.dodois.io/dodopizza/ru/delivery/statistics/',
                              token[2], units=units_str, _from=cra, to=crb)
    for order in orders:
        message = '<b>Скорость доставки:</b>\n'
        for j in delivery['unitsStatistics']:
            if j['unitId'] in order[2]:
                rest = j['unitName']
                avg_delivery = await change_time(timedelta(seconds=j['avgDeliveryOrderFulfillmentTime']))
                message += f'    <b>{rest}:</b> {avg_delivery}\n'
        message += '<b>Время приготовления на доставку:</b>\n'
        for j in delivery['unitsStatistics']:
            if j['unitId'] in order[2]:
                rest = j['unitName']
                cooking = await change_time(timedelta(seconds=j['avgCookingTime']))
                message += f'    <b>{rest}:</b> {cooking}\n'
        message += '<b>Время на полке:</b>\n'
        for j in delivery['unitsStatistics']:
            if j['unitId'] in order[2]:
                rest = j['unitName']
                shelf = await change_time(timedelta(seconds=j['avgHeatedShelfTime']))
                message += f'    <b>{rest}:</b> {shelf}\n'
        message += '<b>Время поездок курьеров:</b>\n'
        for j in delivery['unitsStatistics']:
            if j['unitId'] in order[2]:
                rest = j['unitName']
                avg_trip = await change_time(timedelta(seconds=j['avgOrderTripTime']))
                message += f'    <b>{rest}:</b> {avg_trip}\n'
        await cfg.bot.send_message(order[1], message)

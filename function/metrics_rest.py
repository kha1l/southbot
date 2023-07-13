from database.psql import Database
from datetime import datetime, date, timedelta
from function.api import post_api, get_public_api
from config.conf import Config


async def change_time(tm):
    hour = tm.seconds // 3600
    minute = tm.seconds % 3600 // 60
    second = tm.seconds % 3600 % 60
    if minute < 10:
        minute = f'0{minute}'
    if second < 10:
        second = f'0{second}'
    return f'{hour}:{minute}:{second}'


async def metrics():
    db = Database()
    cfg = Config()
    created_after = date.today()
    created_before = datetime.now()
    dt_pyrus = created_after - timedelta(hours=3)
    dt = datetime.strftime(dt_pyrus, '%Y-%m-%dT%H:%M:%SZ')
    crb = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    cra = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    token = db.get_token()
    orders = db.select_orders('metrics')
    uuids = db.select_uuid()
    rest_uuid = {}
    rest_id_list = []
    for uuid in uuids:
        rest_uuid[uuid[0]] = [uuid[1], uuid[2]]
        rest_id_list.append(uuid[0])
    uuid = ','.join(rest_id_list)
    handovers = await post_api(f'https://api.dodois.io/dodopizza/ru/production/orders-handover-statistics',
                               token[2], units=uuid, _from=cra, to=crb, salesChannels='DineIn')
    handover = handovers['ordersHandoverStatistics']
    for order in orders:
        message = '<b>Выручка:</b>\n'
        for unit in order[2]:
            rest_id = rest_uuid[unit][0]
            rest_name = rest_uuid[unit][1]
            url = f'https://publicapi.dodois.io/ru/api/v1/OperationalStatisticsForTodayAndWeekBefore/{rest_id}'
            revenue = await get_public_api(url)
            today = revenue['today']
            week = revenue['weekBeforeToThisTime']
            revenue_today = int(today['revenue'])
            revenue_week = int(week['revenue'])
            nw = '{:,d}'.format(revenue_today).replace(',', ' ')
            lw = '{:,d}'.format(revenue_week).replace(',', ' ')
            try:
                perc = round((revenue_today * 100 / revenue_week) - 100)
            except ZeroDivisionError:
                perc = 0
            if perc >= 0:
                perc = f'+{perc}'
                message += f'<b>    {rest_name}:</b>  ' \
                           f'{nw} ({lw}) <b>{perc}%</b> \U0001F7E2\n'
            else:
                message += f'<b>    {rest_name}:</b>  ' \
                           f'{nw} ({lw}) <b>{perc}%</b> \U0001F534\n'
        message += f'<b>Рейтинг и Проблемность:</b>\n'
        for unit in order[2]:
            rest_id = rest_uuid[unit][0]
            rest_name = rest_uuid[unit][1]
            link = f'https://publicapi.dodois.io/ru/api/v1/unitinfo/' \
                   f'{rest_id}/dailyrevenue/{created_after.year}/{created_after.month}/{created_after.day}'
            count_orders = await get_public_api(link)
            order_unit = count_orders['UnitRevenue'][0]
            mobile_orders = int(order_unit['StationaryMobileCount'])
            delivery_orders = int(order_unit['DeliveryCount'])
            grades = db.get_grade(dt_pyrus, unit)
            prb_rest = db.get_problems(dt_pyrus, unit, 'Ресторан')
            prb_del = db.get_problems(dt_pyrus, unit, 'Доставка')
            avg_grade = grades[0]
            if avg_grade is None:
                avg_grade = 0
            else:
                avg_grade = round(avg_grade, 2)
            try:
                prob_rest = round(prb_rest[0] / mobile_orders * 100, 2)
            except ZeroDivisionError:
                prob_rest = 0
            except TypeError:
                prob_rest = 0
            try:
                prob_del = round(prb_del[0] / delivery_orders * 100, 2)
            except ZeroDivisionError:
                prob_del = 0
            except TypeError:
                prob_del = 0
            message += f'    <b>{rest_name}</b>\n' \
                       f'        <b>Рейтинг клиентов:</b> {avg_grade}\n' \
                       f'        <b>Проблемность ресторан:</b> {prob_rest}\n' \
                       f'        <b>Проблемность доставка:</b> {prob_del}\n'
        message += f'<b>Средний чек ресторана:</b>\n'
        for unit in order[2]:
            count, total = 0, 0
            rest_name = ''
            check = await post_api(f'https://api.dodois.io/dodopizza/ru/accounting/sales',
                                   token[2], units=unit, _from=cra, to=crb, take=980)
            for ch in check['sales']:
                rest_name = ch['unitName']
                channel = ch['salesChannel']
                products = ch['products']
                if channel == 'Dine-in':
                    count += 1
                    for product in products:
                        total += product['priceWithDiscount']
            try:
                avg_check = round(total / count, 2)
            except ZeroDivisionError:
                avg_check = 0
            message += f'    <b>{rest_name}:</b> {avg_check}\n'
        message += f'<b>Время приготовления в ресторан:</b>\n'
        for unit in order[2]:
            rest_name, tm = '', '0:00:00'
            for hand in handover:
                if hand['unitId'] == unit:
                    rest_name = hand['unitName']
                    time_rest = timedelta(seconds=(hand['avgTrackingPendingTime'] + hand['avgCookingTime']))
                    tm = await change_time(time_rest)
            message += f'    <b>{rest_name}:</b> {tm}\n'
        await cfg.bot.send_message(order[1], message)

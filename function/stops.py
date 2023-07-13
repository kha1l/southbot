from database.psql import Database
from function.api import post_api
from config.conf import Config
from datetime import datetime, timedelta


async def stops():
    created_before = datetime.now().replace(second=0, microsecond=0)
    created_after = created_before - timedelta(minutes=5)
    dt_end = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%S')
    dt_start = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%S')
    db = Database()
    cfg = Config()
    token = db.get_token()
    orders = db.select_orders('stop')
    uuids = db.select_uuid()
    rest_uuid_list = []
    for uuid in uuids:
        rest_uuid_list.append(uuid[0])
    uuid = ','.join(rest_uuid_list)
    ingredients = await post_api(f'https://api.dodois.io/dodopizza/ru/production/stop-sales-ingredients',
                                 token[2], units=uuid, _from=dt_start, to=dt_end)
    ingredient = ingredients['stopSalesByIngredients']
    for order in orders:
        for ings in ingredient:
            if ings['unitId'] in order[2]:
                start_date = ings['startedAt']
                start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S')
                if start_date > created_after:
                    rest = ings['unitName']
                    tm = ings['startedAt'].replace('T', ' ')
                    ing = ings['ingredientName']
                    reason = ings['reason']
                    message = f'<b>Пиццерия:</b> {rest}\n' \
                              f'<b>Время остановки:</b> {tm}\n' \
                              f'<b>Ингредиент:</b> {ing}\n' \
                              f'<b>Причина:</b> {reason}\n'
                    await cfg.bot.send_message(order[1], message)

from config.conf import Config
from database.psql import Database
from datetime import datetime, timedelta
from function.api import pyrus_api


async def send_tickets():
    db = Database()
    cfg = Config()
    orders = db.select_orders('grade')
    created_before = (datetime.now() - timedelta(hours=3)).replace(second=0, microsecond=0)
    created_after = created_before - timedelta(minutes=5)
    dt_end = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    dt_start = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    for order in orders:
        catalogs = ','.join(order[2])
        data = {
            "field_ids": [1, 60, 57, 198, 13, 222, 37, 202, 196, 204, 203, 2, 261, 262, 134],
            "include_archived": "y",
            "created_after": dt_start,
            "created_before": dt_end,
            "fld198": catalogs
        }
        pyrus = await pyrus_api('https://api.pyrus.com/v4/forms/522023/register', data)
        try:
            tasks = pyrus['tasks']
        except KeyError:
            tasks = []
        for task in tasks:
            prob = 0
            comment, name, uuid = '', '', ''
            type_order, number_order, grade = '', 0, 0
            dt, tm = '', ''
            id_task = task['id']
            url_t = f'https://pyrus.com/?id={id_task}'
            tickets = await pyrus_api(f'https://api.pyrus.com/v4/tasks/{id_task}')
            try:
                ticket = tickets['task']
                fields = ticket['fields']
            except KeyError:
                fields = []
            for field in fields:
                if field['id'] == 198:
                    value = field['value']
                    try:
                        name = value['values'][1]
                        uuid = value['values'][0].lower()
                    except IndexError:
                        name = ''
                        uuid = ''
                elif field['id'] == 284:
                    try:
                        number_order = field['value']
                    except KeyError:
                        number_order = ''
                elif field['id'] == 285:
                    try:
                        dt = field['value']
                    except KeyError:
                        dt = ''
                elif field['id'] == 286:
                    try:
                        tm = field['value']
                    except KeyError:
                        tm = ''
                elif field['id'] == 280:
                    try:
                        value = field['value']
                        type_order = value['choice_names'][0]
                    except IndexError:
                        type_order = ''
                    except KeyError:
                        type_order = ''
                elif field['id'] == 13:
                    try:
                        value = field['value']['fields']
                    except KeyError:
                        value = []
                    for fld_value in value:
                        if fld_value['id'] == 142:
                            try:
                                grade = fld_value['value']
                            except KeyError:
                                grade = 0
                        elif fld_value['id'] == 143:
                            try:
                                comment = fld_value['value']
                            except KeyError:
                                comment = ''
                elif field['id'] == 202:
                    try:
                        value = field['value']
                    except KeyError:
                        value = []
                    for c in value:
                        j = c['cells']
                        for k in j:
                            if k['id'] == 204:
                                problem = k['value']['values']
                                if problem[6] == 'Service':
                                    pass
                                else:
                                    prob += 1
            db.add_grade(dt, grade, type_order, prob, uuid)
            if 0 < grade < 5:
                message = f'<b>{name}</b>\n' \
                          f'<b>{url_t}</b>\n' \
                          f'<b>Дата и время:</b> {dt + " " + tm}\n' \
                          f'<b>Тип заказа:</b> {type_order}\n' \
                          f'<b>Номер заказа:</b> {number_order}\n' \
                          f'<b>Оценка:</b> {grade}\n' \
                          f'<b>Комментарии:</b> {comment}\n'
                await cfg.bot.send_message(order[1], message)

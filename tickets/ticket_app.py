from config.settings import Config, Token
import requests
from database.postgres import Database
from datetime import date, timedelta, datetime
from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2 import errors


def get_tickets_day(access):
    db = Database()
    dt_tick = date.today() - timedelta(days=1)
    dt_tick2 = date.today() - timedelta(days=2)
    created_after = datetime(dt_tick2.year, dt_tick2.month, dt_tick2.day, 21, 0, 0)
    created_before = datetime(dt_tick.year, dt_tick.month, dt_tick.day, 20, 59, 59)
    crb = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    cra = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    uuids = db.get_stationary_for_pyrus()
    stationary = []
    db.drop_tickets_on_day(dt_tick)
    for i in uuids:
        stationary.append(str(i[1]))
    stat_st = ','.join(stationary)
    url = f'https://api.pyrus.com/v4/forms/522023/register'
    data = {
        "field_ids": [1, 60, 57, 198, 13, 222, 37, 202, 196, 204, 203, 2, 261, 262, 134],
        "include_archived": "y",
        "created_after": cra,
        "created_before": crb,
        "fld198": stat_st
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access}'
    }
    response = requests.post(url, json=data, headers=headers)
    try:
        res = response.json()['tasks']
    except KeyError:
        res = []
    for i in res:
        id_task = i['id']
        num, prob, grade = 0, 0, 0
        dt, client, uuid, name, prbl = dt_tick, '', '', '', ''
        t_ord, com, tm = '', '', ''
        url_t = f'https://pyrus.com/?id={id_task}'
        cnt = 0 
        resp = requests.get(f'https://api.pyrus.com/v4/tasks/{id_task}', headers=headers)
        list_id = [5, 284, 285, 286, 280, 13, 202, 198]
        js = resp.json()['task']
        ticket = datetime.strptime(js['create_date'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=3)
        for o in js['fields']:
            if o['id'] in list_id:
                try:
                    v = o['value']
                    if o['id'] == 280:
                        try:
                            t_ord = v['choice_names'][0]
                        except IndexError:
                            t_ord = ''
                    elif o['id'] == 198:
                        try:
                            uuid = v['values'][0]
                            name = v['values'][1]
                        except IndexError:
                            uuid = ''
                            name = ''
                    elif o['id'] == 13:
                        for z in v['fields']:
                            if z['id'] == 142:
                                try:
                                    grade = z['value']
                                except KeyError:
                                    grade = 0
                            elif z['id'] == 143:
                                try:
                                    com = z['value']
                                except KeyError:
                                    com = ''
                            elif z['id'] == 144:
                                try:
                                    check = z['value']
                                    val = check['fields']
                                    for k in val:
                                        if k['value'] == 'checked':
                                            cnt += 1
                                except KeyError:
                                    pass
                    elif o['id'] == 202:
                        for c in v:
                            j = c['cells']
                            for k in j:
                                if k['id'] == 203:
                                    prob_name = k['value']['values']
                                    prbl += prob_name[0] + '\n'
                                if k['id'] == 204:
                                    problem = k['value']['values']
                                    if problem[6] == 'Service':
                                        pass
                                    else:
                                        cnt += 1
                        prob = cnt
                    elif o['id'] == 5:
                        client = v
                    elif o['id'] == 284:
                        num = v
                    elif o['id'] == 285:
                        dt = v
                    elif o['id'] == 286:
                        tm = v
                        try:
                            h = int(tm.split(":")[0]) + 3
                            m = tm.split(':')[-1]
                            if h < 10:
                                tm = f'0{h}:{m}'
                            else:
                                tm = f'{h}:{m}'
                        except IndexError:
                            tm = v
                        except ValueError:
                            tm = v
                except KeyError:
                    pass

        try:
            db.add_tickets(id_task, url_t, name, uuid, num, dt,
                           tm, t_ord, grade, com, prob, client, dt_tick, ticket, 'tickets', prbl)
        except errors.lookup(UNIQUE_VIOLATION):
            pass


def get_tickets(access):
    db = Database()
    dt_tick = date.today()
    created_after = datetime.now() - timedelta(hours=3) - timedelta(minutes=5)
    created_before = datetime.now() - timedelta(hours=3)
    # created_after = datetime(2022, 11, 10, 7, 30, 0)
    # created_before = datetime(2022, 11, 11, 11, 0, 0)
    crb = datetime.strftime(created_before, '%Y-%m-%dT%H:%M:%SZ')
    cra = datetime.strftime(created_after, '%Y-%m-%dT%H:%M:%SZ')
    uuids = db.get_stationary_for_pyrus()
    stationary = []
    db.drop_tickets()
    for i in uuids:
        stationary.append(str(i[1]))
    stat_st = ','.join(stationary)
    url = f'https://api.pyrus.com/v4/forms/522023/register'
    data = {
        "field_ids": [1, 60, 57, 198, 13, 222, 37, 202, 196, 204, 203, 2, 261, 262, 134],
        "include_archived": "y",
        "created_after": cra,
        "created_before": crb,
        "fld198": stat_st
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access}'
    }
    response = requests.post(url, json=data, headers=headers)
    try:
        res = response.json()['tasks']
    except KeyError:
        res = []
    for i in res:
        id_task = i['id']
        num, prob, grade = 0, 0, 0
        dt, client, uuid, name, prbl = dt_tick, '', '', '', ''
        t_ord, com, tm = '', '', ''
        url_t = f'https://pyrus.com/?id={id_task}'
        resp = requests.get(f'https://api.pyrus.com/v4/tasks/{id_task}', headers=headers)
        list_id = [5, 284, 285, 286, 280, 13, 202, 198]
        js = resp.json()['task']
        ticket = datetime.strptime(js['create_date'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=3)
        for o in js['fields']:
            if o['id'] in list_id:
                try:
                    v = o['value']
                    if o['id'] == 280:
                        try:
                            t_ord = v['choice_names'][0]
                        except IndexError:
                            t_ord = ''
                    elif o['id'] == 198:
                        try:
                            uuid = v['values'][0]
                            name = v['values'][1]
                        except IndexError:
                            uuid = ''
                            name = ''
                    elif o['id'] == 13:
                        for z in v['fields']:
                            if z['id'] == 142:
                                try:
                                    grade = z['value']
                                except KeyError:
                                    grade = 0
                            elif z['id'] == 143:
                                try:
                                    com = z['value']
                                except KeyError:
                                    com = ''
                    elif o['id'] == 202:
                        cnt = 0
                        for c in v:
                            j = c['cells']
                            for k in j:
                                if k['id'] == 203:
                                    prob_name = k['value']['values']
                                    prbl += prob_name[0] + '\n'
                                if k['id'] == 204:
                                    problem = k['value']['values']
                                    if problem[6] == 'Service':
                                        pass
                                    else:
                                        cnt += 1
                        prob = cnt
                    elif o['id'] == 5:
                        client = v
                    elif o['id'] == 284:
                        num = v
                    elif o['id'] == 285:
                        dt = v
                    elif o['id'] == 286:
                        tm = v
                        try:
                            h = int(tm.split(":")[0]) + 3
                            m = tm.split(':')[-1]
                            if h < 10:
                                tm = f'0{h}:{m}'
                            else:
                                tm = f'{h}:{m}'
                        except IndexError:
                            tm = v
                        except ValueError:
                            tm = v
                except KeyError:
                    pass

        try:
            db.add_tickets(id_task, url_t, name, uuid, num, dt,
                           tm, t_ord, grade, com, prob, client, dt_tick, ticket, 'tickets', prbl)
        except errors.lookup(UNIQUE_VIOLATION):
            pass
        if (grade == 4 or grade == 5) or (prob == 0 and grade == 0 and prbl == ''):
            pass
        else:
            try:
                db.add_tickets(id_task, url_t, name, uuid, num, dt,
                               tm, t_ord, grade, com, prob, client, dt_tick, ticket, 'grademp', prbl)
            except errors.lookup(UNIQUE_VIOLATION):
                pass


def tickets():
    cfg = Config()
    access = Token(cfg.bot_pyrus, cfg.key).access
    get_tickets(access)


def tickets_day():
    cfg = Config()
    access = Token(cfg.bot_pyrus, cfg.key).access
    get_tickets_day(access)

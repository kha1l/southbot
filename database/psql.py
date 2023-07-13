import psycopg2
from config.conf import Config


class Database:
    @property
    def connection(self):
        cfg = Config()
        return psycopg2.connect(
            database=cfg.dbase,
            user=cfg.user,
            password=cfg.password,
            host=cfg.host,
            port='5432'
        )

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = tuple()
        connection = self.connection
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)
        if commit:
            connection.commit()
        if fetchone:
            data = cursor.fetchone()
        if fetchall:
            data = cursor.fetchall()
        connection.close()
        return data

    def get_rest(self):
        sql = '''
            SELECT rest_name, rest_uuid, catalog from stationary;
        '''
        return self.execute(sql, fetchall=True)

    def get_token(self):
        sql = '''
            SELECT id, refresh_token, access_token
            FROM token
        '''
        return self.execute(sql, fetchone=True)

    def update_token(self, token_id: int, access: str, refresh: str):
        sql = '''
            UPDATE token SET access_token = %s, refresh_token = %s
            WHERE id = %s
        '''
        params = (access, refresh, token_id)
        self.execute(sql, parameters=params, commit=True)

    def add_unit(self, unit):
        sql = '''
            INSERT INTO stationary (rest_name, rest_uuid, 
            rest_id, catalog) VALUES (%s, %s, %s, %s)
        '''
        params = (unit.name, unit.id, unit.rest_id, unit.catalog)
        self.execute(sql, parameters=params, commit=True)

    def add_orders(self, chat, uuid, post):
        sql = '''
            INSERT INTO orders (chat_id, uuid, post, token_id) VALUES (%s, %s, %s, 1)
        '''
        params = (chat, uuid, post)
        self.execute(sql, parameters=params, commit=True)

    def drop_orders(self, chat):
        sql = '''
            DELETE FROM orders WHERE chat_id=%s
        '''
        params = (chat, )
        self.execute(sql, parameters=params, commit=True)

    def check_order(self, chat, post):
        sql = '''
            SELECT * from orders WHERE chat_id = %s and post = %s
        '''
        params = (chat, post)
        return self.execute(sql, parameters=params, fetchone=True)

    def select_uuid(self):
        sql = '''
            SELECT rest_uuid, rest_id, rest_name FROM stationary
        '''
        return self.execute(sql, fetchall=True)

    def select_orders(self, post):
        sql = '''
            SELECT * from orders Where post = %s
        '''
        params = (post, )
        return self.execute(sql, parameters=params, fetchall=True)

    def update_order(self, chat, uuid, post):
        sql = '''
            UPDATE orders SET uuid = %s WHERE chat_id = %s and post = %s
        '''
        params = (uuid, chat, post)
        self.execute(sql, parameters=params, commit=True)

    def add_grade(self, dt, grade, tps, prob, uuid):
        sql = '''
            INSERT INTO pyrus (ordersday, grade, type_order, problems, rest_uuid) 
            VALUES (%s, %s, %s, %s, %s)
        '''
        params = (dt, grade, tps, prob, uuid)
        self.execute(sql, parameters=params, commit=True)

    def get_grade(self, dt, uuid):
        sql = '''
            SELECT avg(grade) From pyrus WHERE
            rest_uuid = %s and grade <> 0 and 
            ordersday = %s
        '''
        params = (uuid, str(dt))
        return self.execute(sql, parameters=params, fetchone=True)

    def get_problems(self, dt, uuid, tps):
        sql = '''
            SELECT sum(problems) from pyrus WHERE type_order = %s and
            rest_uuid = %s and ordersday = %s
        '''
        params = (tps, uuid, str(dt))
        return self.execute(sql, parameters=params, fetchone=True)

import pymysql
import pymysql.cursors

import app.configurate as configurate


def create_connection():
    """Подключение к бд"""
    try:
        connection=pymysql.connect(
            host=configurate.HOST_NAME,
            user=configurate.USER_NAME,
            password=configurate.PASSWORD,
            database=configurate.DATA_BASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f'[ERROR] Mysql error {e}')

def close_connection(connection):
    if connection:
        connection.close()

def execute_read_query(connection, query, params=None):
    """Выполнение SELECT-запроса"""
    if connection is None:
        return []
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
    except Exception as e:
        return []

def execute_query(connection, query, params=None):
    """Универсальная функция для INSERT"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())
            connection.commit()
            return True
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        connection.rollback()
        return False

def param_kot():
    """Адреса нод в бд (adrees node in mysql)"""

    try:
        connect=create_connection()
        sel="Select idkot,adr,Pgw,Twp,Two,Pwp,Pwo,flag FROM param_kot where flag=-1"
        parametr=execute_read_query(connect,sel)
        return parametr
    finally:
        close_connection(connect)



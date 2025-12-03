import datetime
import logging
from typing import Any
from asyncua import Client
from app.sql_main import *
from asyncua.ua.uaerrors import BadNodeIdUnknown

async def save_read(node, default=0):
    """
    Безопасное чтение ноды возвращает ноль если node не найдена
    (Save read nods , return 0 if node is not found )
    """
    try:
        value = await node.read_value()
        return value if value is not None else default

    except BadNodeIdUnknown:  # Обработка ошибки если в бд адрес ноды Null, то без лога возврат на дефолт
        return default

    except Exception as e:
        logging.error(f'Ошибка ноды {e} {node}')
        return default


async def opc_parse(server_url: str) -> dict:
    """
    Парсим ноды по адресу из бд по функции param_kot
    (Parsing nods on address in Mysql by func param_kot)
    """
    param = param_kot()
    values = {}
    async with Client(server_url) as client:
        for i in param:
            node_pwg = client.get_node(f"ns=1;s={i['Pgw']}")
            node_twp = client.get_node(f"ns=1;s={i['Twp']}")
            node_two = client.get_node(f"ns=1;s={i['Two']}")
            node_pwp = client.get_node(f"ns=1;s={i['Pwp']}")
            node_pwo = client.get_node(f"ns=1;s={i['Pwo']}")

            values[i['idkot']] = {'Pgw': await save_read(node_pwg) / 100,
                                  'Twp': await save_read(node_twp),
                                  'Two': await save_read(node_two),
                                  'Pwp': await save_read(node_pwp) / 100,
                                  'Pwo': await save_read(node_pwo) / 100,
                                  'adr': i['adr']}
    return values


def sql_parse_by_idkot(value: dict) -> list:
    """
    Парсим базу данных для сравнения с значениями opc
    (Parse mysql for comparison is value OPC)

    """
    if not value:
        return [{}]
    connect = create_connection()
    try:
        result_keys = list(value.keys())
        placeholders = ','.join(['%s'] * len(result_keys))
        query = f"""
            SELECT idkot, MAX(Dateizm), Pgw, Twp, Two, Pwp, Pwo
            FROM enrkoteln
            WHERE idkot IN ({placeholders})
            GROUP BY idkot
        """
        result = execute_read_query(connect, query, params=result_keys)
        return result
    finally:
        close_connection(connect)


def merge_opc_and_db(opc_data: dict, db_data_list: list) -> dict[Any, Any]:
    """
                            [Основная логика]
    Сравнением opc и бд и получение среднего числа  (comparison opc and mysql)
    """
    today = datetime.datetime.today().date()
    db_dict = {row['idkot']: row for row in db_data_list}
    result = {}
    params = ['Pgw', 'Twp', 'Two', 'Pwp', 'Pwo']
    for idkot, opc_vals in opc_data.items():
        if idkot not in db_dict:
            continue
        db_vals = db_dict[idkot]
        data_today = (db_vals['MAX(Dateizm)'] != today)
        summed = {'adr': opc_vals['adr']}
        status_opc = False
        for param in params:
            opc_val = opc_vals[param]
            db_val = db_vals.get(param)
            if data_today:
                if opc_val > 1.0:
                    summed[param] = round(opc_val, 2)
                    status_opc = True
                else:
                    summed[param] = db_val if db_val is not None else 0.0
            else:
                if opc_val > 1.0:
                    status_opc = True
                    if db_val is not None and db_val!=0:
                        summed[param] = round((opc_val + db_val) / 2, 2)
                    else:
                        summed[param] = round(opc_val, 2)
                else:
                    summed[param] = db_val if db_val is not None else 0.0
        if status_opc:
            result[idkot] = summed
        if not status_opc:
            message = f"⛔️ Нет связи с OPC для {opc_vals['adr']} (idkot={idkot}) — Будет пропущена"
            logging.error(message)
    return result


def insert_record(cursor, idkot: int, adr: str, dateizm, pgw, twp, two, pwp, pwo):
    query = """
        INSERT INTO enrkoteln (idkot, adr, Dateizm, PGaz, TGaz, Pgw, Twp, Two, Pwp, Pwo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (idkot, adr, dateizm, 0.0, 0, pgw, twp, two, pwp, pwo))


def update_record(cursor, idkot: int, dateizm, pgw, twp, two, pwp, pwo):
    query = """
        UPDATE enrkoteln
        SET PGaz = %s, TGaz = %s, Pgw = %s, Twp = %s, Two = %s, Pwp = %s, Pwo = %s
        WHERE idkot = %s AND Dateizm = %s
    """
    cursor.execute(query, (0.0, 0, pgw, twp, two, pwp, pwo, idkot, dateizm))


def upsert_new(new_data: dict):
    """
    Добавляем новые значения (append new value in mysql)
    """
    if not new_data:
        return
    connect = create_connection()
    try:
        today = datetime.datetime.today().date()
        with connect.cursor() as cursor:
            for idkot, values in new_data.items():
                adr = values['adr']
                pgw = values['Pgw']
                twp = values['Twp']
                two = values['Two']
                pwp = values['Pwp']
                pwo = values['Pwo']
                cursor.execute("SELECT Id FROM enrkoteln WHERE idkot = %s AND Dateizm = %s", (idkot, today))
                exists = cursor.fetchone()
                if exists:
                    update_record(cursor, idkot, today, pgw, twp, two, pwp, pwo)
                else:
                    insert_record(cursor, idkot, adr, today, pgw, twp, two, pwp, pwo)

        connect.commit()
        logging.info(f"✅ Все данные за {today} успешно обработаны")
    except Exception as e:
        logging.error(f'Ошибка при upsert new {e}')
        connect.rollback()
    finally:
        close_connection(connect)

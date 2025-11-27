import asyncio

from opc_to_mysql import *

#--------------------------------------------------Настройка логирования----------------------------------------------------------#
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a',
                    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s', datefmt='%H:%M:%S')

logging.getLogger("asyncua.client.client").setLevel(logging.WARNING)
#---------------------------------------------------------------------------------------------------------------------------------#

server_url = configurate.SERVER_URL


async def main():
    """ Основной цикл (Base cycle) """
    while True:
        try:
            print('[INFO] Начало опроса...')
            result_opc = await opc_parse(server_url)
            result_sql = await asyncio.to_thread(sql_parse_by_idkot, result_opc)
            result_operation = merge_opc_and_db(result_opc, result_sql)
            await asyncio.to_thread(upsert_new, result_operation)
            print('[INFO] Опрос завершен ✅\n\n')
            logging.info("\nОпрос завершен\n")
            await asyncio.sleep(configurate.TIME_CHEAK)

        except Exception as e:
            print(f'[ERROR] Ошибка {e}')
            logging.error(f'Ошибка при выполнении {e}🔥\n\n')
            await asyncio.sleep(600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Скрипт остановлен')

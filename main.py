import asyncio
from app.opc_to_mysql import *
import sys
from logging.handlers import TimedRotatingFileHandler

#--------------------------------------------------Настройка логирования----------------------------------------------------------#
sys.stdout.reconfigure(line_buffering=True)
file_log = TimedRotatingFileHandler('Log.log',when='D',interval=7,backupCount=1,encoding='utf-8')
console_out = logging.StreamHandler(sys.stdout)

logging.basicConfig (handlers=(file_log, console_out),
                     format='|%(asctime)s| [%(levelname)s]: %(message)s',
                     datefmt='%m.%d.%Y %H:%M:%S',
                     level=logging.INFO)

logging.getLogger("asyncua").setLevel(logging.WARNING)
#---------------------------------------------------------------------------------------------------------------------------------#

server_url = configurate.SERVER_URL

async def main():
    """ Основной цикл (Base cycle) """
    while True:
        try:
            logging.info('Начала опроса')
            result_opc = await opc_parse(server_url)
            result_sql = await asyncio.to_thread(sql_parse_by_idkot, result_opc)
            result_operation = merge_opc_and_db(result_opc, result_sql)
            await asyncio.to_thread(upsert_new, result_operation)
            logging.info("Опрос завершен")
            await asyncio.sleep(configurate.TIME_CHEAK)

        except Exception as e:
            logging.error(f'Ошибка при выполнении {e}🔥\n\n')
            await asyncio.sleep(600)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Скрипт остановлен')
    
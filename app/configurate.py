import dotenv
import os

dotenv.load_dotenv()

#Configuration

SERVER_URL=os.getenv('SERVER_URL')
TIME_CHEAK= int(os.getenv('TIME_CHEAK'))
#Mysql
HOST_NAME=os.getenv('HOST_NAME')
USER_NAME=os.getenv('USER_NAME')
PASSWORD=os.getenv('PASSWORD')
DATA_BASE=os.getenv('DATA_BASE')

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [1241085255]  # Твой ID

# ID канала для публикации анонимок (замени на свой)
CHANNEL_ID = "-1003132478039"  # Пока заглушка

# Настройки базы данных
DATABASE_NAME = "podslushano.db"
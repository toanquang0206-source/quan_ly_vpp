import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD","Toan0707"),
    "database": os.getenv("DB_NAME", "quan_ly_kho_vpp"),
    "charset": "utf8mb4",
}
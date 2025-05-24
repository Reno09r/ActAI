import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = quote_plus(os.getenv("PASS", "postgres"))  # URL-кодируем пароль
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "actai_db")

# Формируем URL для подключения к базе данных
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Security configuration
SALT = os.getenv("SALT", "default_salt_for_development")
HASH = os.getenv("HASH", "default_hash_for_development")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_jwt_secret_for_development")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1200
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
import urllib.parse

# Параметры подключения — замените на реальные
DB_USER = "root"
DB_PASS = "n1byRhw28-"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "booking_db"
DB_CHARSET = "utf8mb4"

# Кодирование пароля для URL
password_quoted = urllib.parse.quote_plus(DB_PASS)

# URL без имени БД (для создания БД при необходимости)
ROOT_DB_URL = f"mysql+pymysql://{DB_USER}:{password_quoted}@{DB_HOST}:{DB_PORT}/?charset={DB_CHARSET}"

# URL с именем БД (для работы с таблицами)
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{password_quoted}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"

# Создаём engine для подключения к серверу без базы
root_engine = create_engine(ROOT_DB_URL, echo=False, pool_pre_ping=True)

# Проверяем и создаём базу, если нужно
def ensure_database():
    create_stmt = f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET {DB_CHARSET} COLLATE {DB_CHARSET}_unicode_ci;"
    with root_engine.connect() as conn:
        conn.execute(text(create_stmt))

# Основной engine для работы с ORM
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False)
    date_arrival = Column(Date, nullable=False)
    date_departure = Column(Date, nullable=False)
    room_number = Column(Integer, nullable=False)
    ip = Column(String(45), nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)

class IpRateLimit(Base):
    __tablename__ = "ip_rate_limit"
    ip = Column(String(45), primary_key=True)
    last_booking_at = Column(DateTime)
    first_attempt_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)

def init_db():
    ensure_database()           # создаём БД, если нет
    Base.metadata.create_all(bind=engine)  # создаём таблицы

if __name__ == "__main__":
    init_db()
    print(f"MySQL DB ensured and tables created in database: {DB_NAME}")

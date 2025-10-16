from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = "sqlite:///./sql_app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class Person(Base):
    __tablename__ = "persons"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    date_arrival = Column(Date, nullable=False)
    date_departure = Column(Date, nullable=False)
    room_number = Column(Integer, nullable=False)
    ip = Column(String, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)

# в database.py, модель IpRateLimit должна иметь:
class IpRateLimit(Base):
    __tablename__ = "ip_rate_limit"
    ip = Column(String, primary_key=True)
    last_booking_at = Column(DateTime)
    first_attempt_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)

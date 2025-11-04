from datetime import date
from typing import Optional
from database import Base, engine, SessionLocal, Person, User,IpRateLimit
from sqlalchemy.orm import Session

import uvicorn
from passlib.context import CryptContext
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import delete
from contextlib import asynccontextmanager
from datetime import datetime as dt, timedelta


SECRET_KEY = "replace-with-env-secret"
SESSION_COOKIE = "session"
SESSION_MAX_AGE = 60 * 60
CSRF_SALT = "csrf-salt"




pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")
serializer = URLSafeTimedSerializer(SECRET_KEY)

scheduler = BackgroundScheduler()

app = FastAPI(lifespan=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


Base.metadata.create_all(bind=engine)
RATE_LIMIT_SECONDS = 30 * 60
MAX_ATTEMPTS = 3

def can_create_booking(db: Session, ip: str) -> bool:
    rec = db.query(IpRateLimit).filter_by(ip=ip).first()
    now = dt.now()
    window_start = now - timedelta(seconds=RATE_LIMIT_SECONDS)

    if not rec:
        db.add(IpRateLimit(ip=ip, attempts=1, first_attempt_at=now, last_booking_at=now))
        db.commit()
        return True

    if rec.first_attempt_at is None or rec.first_attempt_at < window_start:
        rec.attempts = 1
        rec.first_attempt_at = now
        rec.last_booking_at = now
        db.commit()
        return True

    rec.attempts = (rec.attempts or 0) + 1
    rec.last_booking_at = now
    db.commit()
    if rec.attempts <= MAX_ATTEMPTS:
        return True
    return False

def get_client_ip(request: Request, trust_x_forwarded_for: bool = False) -> str:

    if trust_x_forwarded_for:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
    client = request.client
    return client.host if client is not None else "0.0.0.0"
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return pwd_ctx.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def create_session_token(username: str) -> str:
    return serializer.dumps({"user": username})

def load_session_token(token: str, max_age: int = SESSION_MAX_AGE) -> Optional[dict]:
    try:
        return serializer.loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

def create_csrf_token() -> str:
    return serializer.dumps({"ts": dt.now().isoformat()}, salt=CSRF_SALT)

def validate_csrf_token(token: str) -> bool:
    try:
        serializer.loads(token, max_age=3600, salt=CSRF_SALT)
        return True
    except Exception:
        return False

def init_admin():
    with SessionLocal() as db:
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            db.add(User(username="admin", password_hash=hash_password("1234"), role="admin"))
            db.commit()

init_admin()

class BookingIn(BaseModel):
    name: str = Field(..., min_length=3, max_length=20)
    phone_number: str = Field(..., min_length=5, max_length=20)
    date_arrival: date
    date_departure: date
    room_number: int = Field(..., ge=1)

    @field_validator("date_departure")
    def departure_after_arrival(cls, v, info):
        arrival = info.data.get("date_arrival")
        if arrival and v < arrival:
            raise ValueError("date_departure must be >= date_arrival")
        return v

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None

    data = load_session_token(token)
    if not data:
        return None

    username = data.get("user")
    if not username:
        return None

    user = db.query(User).filter_by(username=username).first()
    return user

def require_admin(user: User = Depends(get_current_user)):

    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def delete_past_registrations(db: Session) -> int:
    today = date.today()
    stmt = delete(Person).where(Person.date_departure < today)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount if result is not None else 0

def cleanup_job():
    db = SessionLocal()
    try:
        removed = delete_past_registrations(db)
        print(f"[cleanup] removed {removed} rows")
    except Exception as e:
        print(f"[cleanup] error: {e}")
    finally:
        db.close()

def start_scheduler():
    try:
        cleanup_job()
        if scheduler.get_job("cleanup_job"):
            scheduler.remove_job("cleanup_job")
        scheduler.add_job(cleanup_job, 'interval', hours=24, id="cleanup_job", next_run_time=dt.now())
        scheduler.start()
        print("[scheduler] started")
    except Exception as e:
        print(f"[scheduler] start error: {e}")

def stop_scheduler():
    try:
        scheduler.shutdown(wait=False)
        print("[scheduler] stopped")
    except Exception as e:
        print(f"[scheduler] stop error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    rows = []
    if user and user.role == "admin":
        rows = db.query(Person).all()
    csrf_token = create_csrf_token()
    return templates.TemplateResponse("index.html", {
        "request": request, "user": user, "rows": rows, "login_error": None, "csrf_token": csrf_token
    })

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), csrf_token: str = Form(...),
          db: Session = Depends(get_db)):
    if not validate_csrf_token(csrf_token):
        raise HTTPException(status_code=400, detail="Bad CSRF token")
    user = db.query(User).filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        csrf_token = create_csrf_token()
        return templates.TemplateResponse("index.html", {"request": request, "user": None, "rows": [], "login_error": "Неверные учетные данные", "csrf_token": csrf_token})
    resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(SESSION_COOKIE, create_session_token(user.username), httponly=True, samesite="lax", max_age=SESSION_MAX_AGE)
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    resp.delete_cookie(SESSION_COOKIE)
    return resp

@app.post("/admin/delete-all")
async def delete_all_people(confirm: bool = Form(...), db: Session = Depends(get_db), user: User = Depends(require_admin)):
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
    ips = [row[0] for row in db.query(Person.ip).distinct().all() if row[0]]
    stmt = delete(Person)
    db.execute(stmt)
    db.commit()
    for ip in ips:
        rec = db.query(IpRateLimit).filter_by(ip=ip).first()
        if rec:
            rec.attempts = 0
            rec.first_attempt_at = None
            rec.last_booking_at = None
    db.commit()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/admin/delete-by-id-single")
async def delete_by_id_single(
    id: int = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    if not validate_csrf_token(csrf_token):
        raise HTTPException(status_code=400, detail="Bad CSRF token")
    stmt = delete(Person).where(Person.id == id)
    result = db.execute(stmt)
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Person not found")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/add-booking", response_model=dict)
async def create_booking(request: Request, payload: BookingIn, db: Session = Depends(get_db)):
    ip = get_client_ip(request, trust_x_forwarded_for=False)
    if not can_create_booking(db, ip):
        raise HTTPException(status_code=429, detail="Too many bookings from this IP, try later")
    person = Person(
        name=payload.name.strip(),
        phone_number=payload.phone_number.strip(),
        date_arrival=payload.date_arrival,
        date_departure=payload.date_departure,
        room_number=payload.room_number,
        ip=ip  
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    return {
        "id": person.id,
        "name": person.name,
        "phone_number": person.phone_number,
        "date_arrival": person.date_arrival.isoformat(),
        "date_departure": person.date_departure.isoformat(),
        "room_number": person.room_number
    }



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

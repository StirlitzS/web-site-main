from datetime import datetime, date
from typing import Optional
from database import Base, engine, SessionLocal, Person, User
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
from datetime import datetime as dt

# --- Settings (в prod храните в env) ---
SECRET_KEY = "replace-with-env-secret"
SESSION_COOKIE = "session"
SESSION_MAX_AGE = 60 * 60  # seconds
CSRF_SALT = "csrf-salt"

# --- Init ---
pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")
serializer = URLSafeTimedSerializer(SECRET_KEY)

scheduler = BackgroundScheduler()

app = FastAPI(lifespan=None)  # временно создадим, затем присвоим lifespan ниже
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Utilities ---
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
    return serializer.dumps({"ts": datetime.utcnow().isoformat()}, salt=CSRF_SALT)

def validate_csrf_token(token: str) -> bool:
    try:
        serializer.loads(token, max_age=3600, salt=CSRF_SALT)
        return True
    except Exception:
        return False

# --- Ensure admin exists (only for demo) ---
def init_admin():
    with SessionLocal() as db:
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            db.add(User(username="admin", password_hash=hash_password("1234"), role="admin"))
            db.commit()

init_admin()

# --- Pydantic model for booking ---
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

# --- Auth helpers / dependencies ---
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

# --- Cleanup implementation ---
def delete_past_registrations(db: Session) -> int:
    """Удаляет Person с date_departure < today. Возвращает число удалённых строк."""
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
    # Выполнить чистку сразу при старте, затем каждые 24 часа
    try:
        cleanup_job()
        # если задача с таким id уже существует, перезапишем её
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

# --- Lifespan (заменяет deprecated on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()

# присвоим lifespan при создании приложения
app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# --- Routes ---
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

@app.post("/admin/delete-all", status_code=204)
async def delete_all_people(confirm: bool = Form(...), db: Session = Depends(get_db), user: User = Depends(require_admin)):
    """
    Удаляет все записи Person. Требует отправки form-поля confirm=true (чтобы избежать случайных вызовов).
    Возвращает 204 No Content.
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
    stmt = delete(Person)
    result = db.execute(stmt)
    db.commit()
    resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return resp


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
        # можно вернуть 404 или редирект с flash-параметром
        raise HTTPException(status_code=404, detail="Person not found")
    resp = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return resp


@app.post("/add-booking", response_model=dict)
async def create_booking(payload: BookingIn, db: Session = Depends(get_db)):
    person = Person(
        name=payload.name.strip(),
        phone_number=payload.phone_number.strip(),
        date_arrival=payload.date_arrival,
        date_departure=payload.date_departure,
        room_number=payload.room_number
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

@app.get("/api/users")
def get_people(db: Session = Depends(get_db), user: User = Depends(require_admin)):
    rows = db.query(Person).all()
    return [{"id": r.id, "name": r.name, "phone_number": r.phone_number,
             "date_arrival": r.date_arrival.isoformat(), "date_departure": r.date_departure.isoformat(),
             "room_number": r.room_number} for r in rows]

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

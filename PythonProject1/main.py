from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class Booking(BaseModel):
    name: str
    phone_number: str
    date_arrival: datetime
    date_departure: datetime


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "Главная"})

@app.post("/add-booking")
async def read_index(booking: Booking):
    return {booking.name: booking.phone_number}

if __name__ == "__main__":
    uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True, workers=3)
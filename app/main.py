from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from app.database import init_db
from app.routes import chat, dashboard, leads, logs

BASE = Path(__file__).parent
load_dotenv()
app = FastAPI(title="Lead Capture CRM Automation", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
app.include_router(leads.router); app.include_router(dashboard.router); app.include_router(logs.router); app.include_router(chat.router)

@app.on_event("startup")
def startup(): init_db()

@app.get("/", response_class=HTMLResponse)
def home(request: Request): return templates.TemplateResponse(request, "index.html")

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request): return templates.TemplateResponse(request, "dashboard.html")

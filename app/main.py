from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.weather import router

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title="WeatherCN Weather", version="1.0.0")
app.include_router(router)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/api/health")
def health(): return {"status": "ok", "service": "weathercn-weather"}

@app.get("/")
def index(): return FileResponse(BASE_DIR / "templates" / "index.html")

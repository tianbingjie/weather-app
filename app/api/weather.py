from fastapi import APIRouter, HTTPException, Query
from app.services.weather_client import WeatherAPIError
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/api")
service = WeatherService()

@router.get("/search")
def search(q: str = Query(min_length=1, max_length=80)):
    try: return service.search(q)
    except WeatherAPIError as exc: raise HTTPException(502, str(exc)) from exc

@router.get("/locate")
def locate(lat: float, lon: float):
    try: return service.locate(lat, lon)
    except WeatherAPIError as exc: raise HTTPException(502, str(exc)) from exc

@router.get("/weather/{location_key}")
def weather(location_key: str, lat: float | None = None, lon: float | None = None):
    return service.dashboard(location_key, lat, lon)

# ...existing code...
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx

API_KEY = "a3261f82d5f44627bcd193728251711"
BASE_URL = "http://api.weatherapi.com/v1/current.json"

app = FastAPI(title="Weather API Proxy")


class WeatherOut(BaseModel):
    location: str
    temp_c: float
    temp_f: float
    condition: str
    raw: dict | None = None


@app.get("/weather", response_model=WeatherOut)
async def get_weather(location: str = Query(..., description="City name, postcode or lat,long")):
    """
    Fetch current weather for `location` from WeatherAPI and return temperature.
    Example: GET /weather?location=London
    """
    params = {"key": API_KEY, "q": location, "aqi": "yes"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(BASE_URL, params=params)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {e}") from e

    if resp.status_code != 200:
        # attempt to include API error message
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=502, detail={"status": resp.status_code, "error": detail})

    data = resp.json()
    # basic validation
    if "location" not in data or "current" not in data:
        raise HTTPException(status_code=502, detail="Invalid response from weather provider")

    out = WeatherOut(
        location=f"{data['location'].get('name','')}, {data['location'].get('country','')}".strip(", "),
        temp_c=float(data["current"].get("temp_c", 0.0)),
        temp_f=float(data["current"].get("temp_f", 0.0)),
        condition=data["current"].get("condition", {}).get("text", ""),
        raw=data,  # optional: include full provider response
    )
    return out
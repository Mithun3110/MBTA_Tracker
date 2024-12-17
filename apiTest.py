from fastapi import FastAPI, HTTPException
import requests
import os
MBTA_API_KEY = os.getenv("MBTA_API_KEY", "c671369fcd2846b88f782851472f2c7b")

MBTA_API_URL = "https://api-v3.mbta.com"

app = FastAPI()

def get_mbta_data(endpoint: str, params: dict):
    headers = {
        "x-api-key": MBTA_API_KEY
    }
    response = requests.get(f"{MBTA_API_URL}/{endpoint}", headers=headers, params=params)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from MBTA API")
    
    return response.json()

@app.get("/")
def read_root():
    return {"message": "Boston MBTA API with FastAPI is running!"}

@app.get("/mbta/stops")
def get_nearby_stops(lat: float, lon: float):
    params = {
        "filter[latitude]": lat,
        "filter[longitude]": lon
    }
    data = get_mbta_data("stops", params)
    return data



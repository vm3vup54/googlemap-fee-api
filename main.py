from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import googlemaps
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

app = FastAPI()
gmaps = googlemaps.Client(key=API_KEY)

class RouteRequest(BaseModel):
    origin: str
    destination: str

@app.post("/route")
def get_route(data: RouteRequest):
    try:
        directions = gmaps.directions(data.origin, data.destination, mode="driving", departure_time=datetime.now())
        if not directions:
            raise HTTPException(status_code=404, detail="無法取得路線")

        leg = directions[0]['legs'][0]
        distance_km = leg['distance']['value'] / 1000
        duration_min = leg['duration']['value'] // 60
        fee = int(round(distance_km * 2 * 3))
        today = datetime.today().strftime("%Y-%m-%d")
        report = f"{today} {data.origin}-{data.destination}【自行開車 {distance_km:.1f}(公里數)*3(元/公里)*2(來回)={fee}(費用)】"

        return {
            "distance_km": round(distance_km, 1),
            "duration_min": duration_min,
            "fee": fee,
            "report": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

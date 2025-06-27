from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import googlemaps
import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlencode

load_dotenv()
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

app = FastAPI()
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

class RouteRequest(BaseModel):
    origin: str
    destination: str

def upload_to_imgbb(image_path: str) -> str:
    with open(image_path, "rb") as file:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY},
            files={"image": file}
        )
    data = res.json()
    return data["data"]["url"] if res.ok else None

@app.post("/route")
def get_route(data: RouteRequest):
    try:
        directions = gmaps.directions(
            data.origin,
            data.destination,
            mode="driving",
            departure_time=datetime.now(),
            alternatives=True
        )
        if not directions:
            raise HTTPException(status_code=404, detail="無法取得路線")

        routes = []
        best_duration = float("inf")
        best_leg = None
        for route in directions:
            leg = route["legs"][0]
            duration_min = leg["duration"]["value"] // 60
            distance_km = leg["distance"]["value"] / 1000
            routes.append({
                "distance_km": round(distance_km, 1),
                "duration_min": duration_min
            })
            if duration_min < best_duration:
                best_duration = duration_min
                best_leg = leg

        best_distance = best_leg["distance"]["value"] / 1000
        fee = round(best_distance * 2 * 3)
        today = datetime.today().strftime("%Y-%m-%d")
        report = f"{today} {data.origin}-{data.destination}【自行開車 {best_distance:.1f}(公里數)*3(元/公里)*2(來回)={fee}(費用)】"

        static_map_url = (
            "https://maps.googleapis.com/maps/api/staticmap?" +
            urlencode({
                "size": "600x400",
                "path": f"enc:{directions[0]['overview_polyline']['points']}",
                "markers": f"color:red|label:A|{data.origin}",
                "markers": f"color:green|label:B|{data.destination}",
                "key": GOOGLE_MAPS_API_KEY
            })
        )
        image_path = "map.png"
        with open(image_path, "wb") as f:
            img_data = requests.get(static_map_url).content
            f.write(img_data)

        map_url = upload_to_imgbb(image_path)
        map_link = f"https://www.google.com/maps/dir/{data.origin}/{data.destination}"

        return {
            "routes": routes,
            "distance_km": round(best_distance, 1),
            "duration_min": best_duration,
            "fee": fee,
            "report": report,
            "map_url": map_url,
            "map_link": map_link  # ✅ 已加入 Google Maps 連結
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/")
def gpt_route(data: RouteRequest):
    return get_route(data)

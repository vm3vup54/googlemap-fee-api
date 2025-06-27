from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import googlemaps
from datetime import datetime
import os
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles

# 載入 .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

app = FastAPI()

# 設定靜態檔案路徑
os.makedirs("static/maps", exist_ok=True)
app.mount("/maps", StaticFiles(directory="static/maps"), name="maps")

# Google Maps 客戶端
gmaps = googlemaps.Client(key=API_KEY)

class RouteRequest(BaseModel):
    origin: str
    destination: str

def download_map(origin, destination):
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    params = {
        "size": "600x400",
        "maptype": "roadmap",
        "markers": f"color:blue|label:S|{origin}&markers=color:red|label:E|{destination}",
        "path": f"color:0x0000ff|weight:5|{origin}|{destination}",
        "key": API_KEY
    }
    full_url = f"{base_url}?{urlencode(params)}"
    response = requests.get(full_url)
    if response.status_code == 200:
        filename = f"map_{datetime.now().timestamp()}.png"
        save_path = f"static/maps/{filename}"
        with open(save_path, "wb") as f:
            f.write(response.content)
        return f"/maps/{filename}"  # 回傳靜態檔網址
    else:
        return None

@app.post("/")
def gpt_route(data: RouteRequest):
    try:
        directions = gmaps.directions(
            data.origin, data.destination,
            mode="driving",
            alternatives=True,
            departure_time=datetime.now()
        )

        if not directions:
            raise HTTPException(status_code=404, detail="無法取得路線")

        # 所有路線摘要
        results = []
        for i, route in enumerate(directions):
            leg = route['legs'][0]
            results.append({
                "route_index": i + 1,
                "distance_km": round(leg['distance']['value'] / 1000, 1),
                "duration_min": leg['duration']['value'] // 60
            })

        # 只用第一條（最佳）路線計費
        best_leg = directions[0]['legs'][0]
        best_distance_km = round(best_leg['distance']['value'] / 1000, 1)
        fee = round(best_distance_km * 2 * 3)

        today = datetime.today().strftime("%Y-%m-%d")
        report = f"{today} {data.origin}-{data.destination}【自行開車 {best_distance_km:.1f}(公里數)*3(元/公里)*2(來回)={fee}(費用)】"
        
        # 下載地圖
        map_url = download_map(data.origin, data.destination)

        return {
            "routes": results,
            "fee": fee,
            "report": report,
            "map_url": map_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Google Maps Travel Fee API

## 使用說明

1. 將 `.env` 中的 `your_api_key_here` 換成你的 Google Maps API 金鑰。
2. 安裝依賴：
   ```
   pip install -r requirements.txt
   ```
3. 啟動伺服器：
   ```
   uvicorn main:app --reload
   ```

## API 範例

**POST /route**

```json
{
  "origin": "台北市政府",
  "destination": "桃園國際機場"
}
```

**回傳結果**

```json
{
  "distance_km": 42.7,
  "duration_min": 35,
  "fee": 256,
  "report": "2025-06-26 台北市政府-桃園國際機場【自行開車 42.7(公里數)*3(元/公里)*2(來回)=256(費用)】"
}
```

import asyncio
import cv2
import numpy as np
import torch
from fastapi import FastAPI, WebSocket
from concurrent.futures import ThreadPoolExecutor
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
model = torch.hub.load('ultralytics/yolov5', 'custom',
                       path='app/yolov5_weights/best.pt', force_reload=False)
executor = ThreadPoolExecutor(max_workers=4)

async def run_inference(frame_bytes):
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return []
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(executor, model, frame)
    detections = []
    for *xyxy, conf, cls in results.xyxy[0]:
        if conf >= 0.65:
            x1, y1, x2, y2 = map(int, xyxy)
            detections.append({
                "class_id": int(cls),
                "confidence": float(conf),
                "bbox": [x1, y1, x2, y2]
            })
    return detections

@app.websocket("/ws/detect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            frame_bytes = await websocket.receive_bytes()
            detections = await run_inference(frame_bytes)
            await websocket.send_json({"detections": detections})
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

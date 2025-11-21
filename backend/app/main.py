import base64
import json
import os
from fastapi import FastAPI, Request, BackgroundTasks
from app.scheduler import check_and_dispatch
from app.worker import process_event
from app.api import dashboard
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/dashboard")

@app.get("/")
async def root():
    return {"message": "Boat Race Trading System API"}

@app.post("/dispatch")
async def dispatch_job(background_tasks: BackgroundTasks):
    """Cloud Schedulerから呼ばれるエンドポイント"""
    background_tasks.add_task(check_and_dispatch)
    return {"status": "dispatched"}

@app.post("/pubsub/handler")
async def pubsub_handler(request: Request, background_tasks: BackgroundTasks):
    """Pub/Sub Pushサブスクリプションから呼ばれるエンドポイント"""
    try:
        envelope = await request.json()
        if not envelope:
            msg = "no Pub/Sub message received"
            print(f"error: {msg}")
            return f"Bad Request: {msg}", 400

        if not isinstance(envelope, dict) or "message" not in envelope:
            msg = "invalid Pub/Sub message format"
            print(f"error: {msg}")
            return f"Bad Request: {msg}", 400

        pubsub_message = envelope["message"]

        if isinstance(pubsub_message, dict) and "data" in pubsub_message:
            data_str = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
            try:
                data = json.loads(data_str)
                # バックグラウンドで処理を実行
                background_tasks.add_task(process_event, data)
            except json.JSONDecodeError:
                print(f"Invalid JSON: {data_str}")
                return "Invalid JSON", 400

        return ("", 204)

    except Exception as e:
        print(f"Exception in pubsub_handler: {e}")
        return (f"Internal Server Error: {e}", 500)

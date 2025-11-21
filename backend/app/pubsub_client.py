import os
import json
from google.cloud import pubsub_v1

PROJECT_ID = os.getenv("PROJECT_ID", "dummy-project")
TOPIC_ID = "race-events"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

def publish_message(data: dict):
    """Pub/Subにメッセージを送信する"""
    if PROJECT_ID == "dummy-project":
        print(f"[Mock Pub/Sub] Publishing: {data}")
        return

    data_str = json.dumps(data)
    data_bytes = data_str.encode("utf-8")
    
    try:
        future = publisher.publish(topic_path, data_bytes)
        print(f"Published message ID: {future.result()}")
    except Exception as e:
        print(f"Error publishing message: {e}")

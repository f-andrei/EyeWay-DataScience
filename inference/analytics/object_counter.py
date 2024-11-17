# type: ignore
from utils.constants import BACKEND_API_URL, CLASS_NAMES
from datetime import datetime
import requests
import os


class ObjectCounter:
    def __init__(self):
        self.url = os.path.join(BACKEND_API_URL, "objects")
        self.saved_objects = {}
        self.buffer = []
        self.last_send_time = datetime.now()
        
    def send_buffer(self):
        if not self.buffer:
            return
            
        try:
            payload = {
                "objects": self.buffer
            }
            print(f"Pushing {len(self.buffer)} objects to the database")
            response = requests.post(self.url, json=payload, timeout=2)
            if response.status_code == 200:
                self.buffer = []
        except Exception as e:
            print(f"Error sending buffer: {e}")

    def count_objects(self, obj_meta, camera_id):
        try:
            if obj_meta.object_id not in self.saved_objects:
                self.saved_objects[obj_meta.object_id] = 1
                obj_data = {
                    "camera_id": camera_id,
                    "class_label": CLASS_NAMES[obj_meta.class_id],
                    "timestamp": datetime.now().isoformat()
                }
                self.buffer.append(obj_data)
                
                current_time = datetime.now()
                if (current_time - self.last_send_time).total_seconds() >= 120:
                    self.send_buffer()
                    self.last_send_time = current_time
                    
        except Exception as err:
            print(f"An error occurred: {err}")
        return None
import requests # type: ignore
from .utils import draw_bounding_boxes
import pyds # type: ignore
import cv2 # type: ignore
import numpy as np # type: ignore
from datetime import datetime
import os
import base64
from dotenv import load_dotenv # type: ignore

load_dotenv()

class_names = ["Pessoa","Bicicleta","Carro","Motocicleta","Aviao","Onibus","Trem","Caminhao"]
API_URL = os.getenv("API_URL", "http://host.docker.internal:3000")
class InfractionsHandler:
    def __init__(self):
        self.url = os.path.join(API_URL, "infractions")
        self.saved_objects = {}

    def handle_infraction(self, gst_buffer, frame_meta, obj_meta, infraction_type):
        if obj_meta.object_id not in self.saved_objects:
            self.saved_objects[obj_meta.object_id] = 1

            frame = self.get_frame(gst_buffer, obj_meta, frame_meta, infraction_type)
            image_base64 = cv2.imencode('.jpg', frame)[1].tobytes()
            image_base64 = base64.b64encode(image_base64).decode('utf-8')

            payload = {
                "camera_id": frame_meta.pad_index,
                "vehicle_type": class_names[obj_meta.class_id],
                "infraction_type": infraction_type, 
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "image_base64": image_base64
            }

            response = requests.post(self.url, json=payload)
            print(response.status_code)
            return response
    
    def get_frame(self, gst_buffer, obj_meta, frame_meta, text):
        n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
        frame_copy = np.array(n_frame, copy=True, order='C')
        frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_RGBA2BGRA)
        frame_copy = draw_bounding_boxes(frame_copy, obj_meta, text)
        return frame_copy
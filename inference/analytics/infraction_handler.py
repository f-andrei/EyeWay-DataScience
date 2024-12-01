# type: ignore
import requests
import base64
import os
import io
from utils.constants import BACKEND_API_URL, CLASS_NAMES
from common.image_utils import draw_bounding_boxes, get_frame

class InfractionsHandler:
    def __init__(self):
        self.url = os.path.join(BACKEND_API_URL, "infractions")
        self.saved_objects = {}

    def handle_infraction(self, gst_buffer, frame_meta, obj_meta, infraction_type, camera_id):
        try:
            if obj_meta.object_id not in self.saved_objects:
                self.saved_objects[obj_meta.object_id] = 1

                frame = get_frame(gst_buffer, frame_meta)
                if frame is None:
                    print("Error: Failed to get frame")
                    return None

                frame_with_boxes = draw_bounding_boxes(frame, obj_meta)
                
                img_buffer = io.BytesIO()
                
                frame_with_boxes.save(img_buffer, format='PNG')

                img_buffer.seek(0)
                image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

                payload = {
                    "camera_id": camera_id,
                    "vehicle_type": CLASS_NAMES[obj_meta.class_id],
                    "infraction_type": infraction_type, 
                    "image_base64": image_base64
                }
                
                response = requests.post(self.url, json=payload, timeout=2)
                return response
                
        except requests.exceptions.Timeout:
            print("Request timed out")
        except requests.exceptions.ConnectionError:
            print("Failed to connect to the server")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error occurred: {err}")
            import traceback
            print(traceback.format_exc())
        return None
    

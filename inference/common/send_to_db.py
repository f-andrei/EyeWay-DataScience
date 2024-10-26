import requests # type: ignore
from .utils import draw_bounding_boxes
import pyds # type: ignore
import cv2 # type: ignore
import numpy as np # type: ignore
from datetime import datetime
import os
import base64
import ctypes
from dotenv import load_dotenv # type: ignore
import cupy as cp # type: ignore

load_dotenv()

class_names = ["Pessoa","Bicicleta","Carro","Motocicleta","Aviao","Onibus","Trem","Caminhao"]
# API_URL = os.getenv("API_URL", "http://host.docker.internal:3000")
API_URL = "http://172.26.144.1:3000"
class InfractionsHandler:
    def __init__(self):
        self.url = os.path.join(API_URL, "infractions")
        self.saved_objects = {}

    def handle_infraction(self, gst_buffer, frame_meta, obj_meta, infraction_type):
        try:
            if obj_meta.object_id not in self.saved_objects:
                self.saved_objects[obj_meta.object_id] = 1

                frame = self.get_frame(gst_buffer, obj_meta, frame_meta, infraction_type)
                frame = draw_bounding_boxes(frame, obj_meta, "Conversao proibida")
                image_base64 = cv2.imencode('.jpg', frame)[1].tobytes()
                image_base64 = base64.b64encode(image_base64).decode('utf-8')

                payload = {
                    "camera_id": frame_meta.pad_index,
                    "vehicle_type": class_names[obj_meta.class_id],
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
        except requests.exceptions.RequestException as err:
            print(f"An error occurred: {err}")
        return None
    
    def get_frame(self, gst_buffer, obj_meta, frame_meta, text):
        try:
            # Create dummy owner object to keep memory for the image array alive
            owner = None
            
            # Getting Image data using nvbufsurface
            data_type, shape, strides, dataptr, size = pyds.get_nvds_buf_surface_gpu(hash(gst_buffer), frame_meta.batch_id)
            
            # Setup pointer handling
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
            
            # Get pointer to buffer and create UnownedMemory object
            c_data_ptr = ctypes.pythonapi.PyCapsule_GetPointer(dataptr, None)
            unownedmem = cp.cuda.UnownedMemory(c_data_ptr, size, owner)
            
            # Create MemoryPointer object from unownedmem
            memptr = cp.cuda.MemoryPointer(unownedmem, 0)
            
            # Create cupy array to access the image data
            n_frame_gpu = cp.ndarray(shape=shape, dtype=data_type, memptr=memptr, strides=strides, order='C')
            
            # Initialize cuda stream
            stream = cp.cuda.stream.Stream(null=True)
            
            with stream:
                # Convert RGBA to RGB by reordering channels (on GPU)
                # Keep only RGB channels (remove alpha)
                rgb_frame_gpu = n_frame_gpu[:, :, :3]
                
                # If you need to flip from RGBA to RGB, uncomment this:
                rgb_frame_gpu = rgb_frame_gpu[:, :, ::-1]  # Reverse the channel order
                
            stream.synchronize()
            
            # Copy to CPU and ensure it's contiguous
            frame_cpu = cp.asnumpy(rgb_frame_gpu)
            
            return frame_cpu
            
        except Exception as e:
            print(f"Error getting frame: {e}")
            return None
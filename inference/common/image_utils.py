# type: ignore
from PIL import Image, ImageDraw, ImageFont
from utils.constants import CLASS_NAMES
import numpy as np
import cupy as cp
import ctypes
import pyds
import cv2
import traceback

def get_frame(gst_buffer, frame_meta):
    try:
        owner = None
        data_type, shape, strides, dataptr, size = pyds.get_nvds_buf_surface_gpu(hash(gst_buffer), frame_meta.batch_id)
        
        ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
        ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
        
        c_data_ptr = ctypes.pythonapi.PyCapsule_GetPointer(dataptr, None)
        unownedmem = cp.cuda.UnownedMemory(c_data_ptr, size, owner)
        memptr = cp.cuda.MemoryPointer(unownedmem, 0)
        
        n_frame_gpu = cp.ndarray(shape=shape, dtype=data_type, memptr=memptr, strides=strides, order='C')
        
        stream = cp.cuda.stream.Stream(null=True)
        
        with stream:
            # Just copy the first three channels without reordering
            frame_gpu = n_frame_gpu[:, :, :3].copy()
            
        stream.synchronize()
        
        # Get the data to CPU
        frame_cpu = cp.asnumpy(frame_gpu)
        frame_cpu = np.ascontiguousarray(frame_cpu, dtype=np.uint8)
        
        return frame_cpu
        
    except Exception as e:
        print(f"Error getting frame: {str(e)}")
        traceback.print_exc()
        raise e
        
    finally:
        # Clean up GPU memory
        if 'frame_gpu' in locals():
            del frame_gpu
        if 'n_frame_gpu' in locals():
            del n_frame_gpu
        if 'memptr' in locals():
            del memptr
        if 'unownedmem' in locals():
            del unownedmem

def draw_bounding_boxes(image, obj_meta):
    """
    Draw bounding boxes on an image
    """
    # Convert to PIL Image preserving original color space
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    
    # Convert to RGBA for overlay while preserving colors
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    class_id = obj_meta.class_id
    rect_params = obj_meta.rect_params
    top = int(rect_params.top)
    left = int(rect_params.left)
    width = int(rect_params.width)
    height = int(rect_params.height)
    
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # Draw semi-transparent rectangle in BGR order since we're preserving original colors
    draw_overlay.rectangle([left, top, left + width, top + height], 
                         fill=(255, 255, 255, 80))
    
    image = Image.alpha_composite(image, overlay)
    
    draw = ImageDraw.Draw(image)
    color = (255, 0, 0, 255)
    
    w_percents = int(width * 0.05) if width > 100 else int(width * 0.1)
    h_percents = int(height * 0.05) if height > 100 else int(height * 0.1)
    
    # Draw corners
    # Top left
    draw.line([left, top, left + w_percents, top], fill=color, width=6)
    draw.line([left, top, left, top + h_percents], fill=color, width=6)
    
    # Top right
    draw.line([left + width - w_percents, top, left + width, top], fill=color, width=6)
    draw.line([left + width, top, left + width, top + h_percents], fill=color, width=6)
    
    # Bottom left
    draw.line([left, top + height - h_percents, left, top + height], fill=color, width=6)
    draw.line([left, top + height, left + w_percents, top + height], fill=color, width=6)
    
    # Bottom right
    draw.line([left + width - w_percents, top + height, left + width, top + height], fill=color, width=6)
    draw.line([left + width, top + height - h_percents, left + width, top + height], fill=color, width=6)
    
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            font = ImageFont.load_default()
    
    draw.text((left, top - 35), CLASS_NAMES[class_id], fill=(255, 255, 255, 255), font=font)
    
    final_image = image.convert(image.mode)
    return final_image
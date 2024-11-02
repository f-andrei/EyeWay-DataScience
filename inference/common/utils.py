# type: ignore
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class_names = ["Pessoa", "Bicicleta", "Carro", "Motocicleta", "Avião", "Ônibus", "Trem", "Caminhão"]
saved_objects = {}

def draw_bounding_boxes(image, obj_meta):
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    
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
    
 
    draw_overlay.rectangle([left, top, left + width, top + height], 
                         fill=(0, 0, 255, 40)) 
    
    image = Image.alpha_composite(image, overlay)
    
    draw = ImageDraw.Draw(image)
    color = (255, 255, 255, 255)  
    
    w_percents = int(width * 0.05) if width > 100 else int(width * 0.1)
    h_percents = int(height * 0.05) if height > 100 else int(height * 0.1)
    
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
        # For Windows
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        try:
            # For Linux
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            font = ImageFont.load_default()
    
    draw.text((left - 10, top - 50), class_names[class_id], fill=(255, 255, 255, 255), font=font)
    
    return np.array(image)
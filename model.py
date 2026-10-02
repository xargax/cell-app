import os
import io
import streamlit as st
import numpy as np
import cv2
from PIL import Image
from ultralytics import YOLO
import gdown
import config

@st.cache_resource(show_spinner=False)
def load_yolo_model():
    local_weights_path = "/tmp/best.pt"
    if not os.path.exists(local_weights_path):
        url = f"https://drive.google.com/uc?id={config.MODEL_DRIVE_FILE_ID}"
        gdown.download(url, local_weights_path, quiet=False)
    return YOLO(local_weights_path)

def process_single_image(image_bytes, model):
    img_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_np = np.array(img_pil)
    
    # Инференс YOLO
    results = model.predict(source=img_pil, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
    
    annotated = img_np.copy()
    
    # Цвета в формате RGB:
    # Синий - жизнеспособная, Циан - нежизнеспособная (мертвая), Белый - почкующаяся
    CLASS_COLORS = {
        0: (0, 70, 255),     # Синий (жизнеспособная)
        1: (0, 230, 230),    # Циан (нежизнеспособная)
        2: (255, 255, 255),  # Белый (почкующаяся)
    }
    
    class_counts = {
        "viable": 0,    # жизнеспособные
        "dead": 0,      # нежизнеспособные
        "budding": 0    # почкующиеся
    }
    
    total_cells = 0

    if results.boxes is not None and len(results.boxes) > 0:
        boxes = results.boxes.xyxy.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy().astype(int)
        
        for box, cls_id in zip(boxes, classes):
            x1, y1, x2, y2 = map(int, box)
            
            # Подсчёт по классам в зависимости от порядка классов в модели
            # (0: viable, 1: dead/non-viable, 2: budding)
            if cls_id == 0:
                class_counts["viable"] += 1
            elif cls_id == 1:
                class_counts["dead"] += 1
            elif cls_id == 2:
                class_counts["budding"] += 1
            
            color = CLASS_COLORS.get(cls_id, (0, 70, 255))
            
            # Рисуем только чистую тонкую рамку (толщина 2px), без перекрывающих надписей
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            total_cells += 1

    return annotated, total_cells, class_counts

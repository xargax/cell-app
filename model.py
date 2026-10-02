import os
import io
import streamlit as st
from PIL import Image
from ultralytics import YOLO
import gdown
import config

@st.cache_resource(show_spinner=False)
def load_yolo_model():
    local_weights_path = "/tmp/best.pt"
    
    # Скачиваем веса с Google Диска, если их еще нет во временной папке
    if not os.path.exists(local_weights_path):
        url = f"https://drive.google.com/uc?id={config.MODEL_DRIVE_FILE_ID}"
        gdown.download(url, local_weights_path, quiet=False)
        
    # Загружаем модель YOLOv8
    model = YOLO(local_weights_path)
    return model

def process_single_image(image_bytes, model):
    # Корректно открываем байты через io.BytesIO
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Запускаем детекцию на CPU (conf порог можно настроить, например 0.25)
    results = model.predict(source=img, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
    
    # Количество найденных клеток
    cell_count = len(results.boxes) if results.boxes is not None else 0
    
    # Отрисовываем разметку и переводим BGR в RGB
    annotated_bgr = results.plot()
    annotated_rgb = annotated_bgr[..., ::-1]
    
    return annotated_rgb, cell_count

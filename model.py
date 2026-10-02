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
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # Инференс
    results = model.predict(source=img, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
    
    cell_count = len(results.boxes) if results.boxes is not None else 0
    
    # Вариант 1 (рекомендуемый для микроскопии): аккуратные рамки БЕЗ перекрывающего текста
    annotated_bgr = results.plot(
        line_width=1,   # Тонкая рамка (1 px)
        labels=False,   # Скрывает гигантские плашки с текстом
        boxes=True
    )
    
    # Если подписи всё же нужны, но микроскопические, используйте вместо этого:
    # annotated_bgr = results.plot(line_width=1, font_size=6, labels=True, conf=False)

    annotated_rgb = annotated_bgr[..., ::-1]
    
    return annotated_rgb, cell_count

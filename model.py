import streamlit as st
from PIL import Image
from ultralytics import YOLO
import gsheets

@st.cache_resource(show_spinner=False)
def load_yolo_model():
    weights_path = gsheets.download_model_weights()
    model = YOLO(weights_path, task="detect")
    return model

def process_single_image(image_bytes, model):
    img = Image.open(image_bytes).convert("RGB")
    
    # Инференс на CPU
    results = model.predict(source=img, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
    
    # Подсчет найденных клеток
    cell_count = len(results.boxes)
    
    # Отрисовка рамок (BGR в RGB для Streamlit)
    annotated_bgr = results.plot()
    annotated_rgb = annotated_bgr[..., ::-1]
    
    return annotated_rgb, cell_count

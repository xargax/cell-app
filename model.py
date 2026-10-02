import os
import streamlit as st
from PIL import Image
from ultralytics import YOLO
import gdown
import config

@st.cache_resource(show_spinner=False)
def load_yolo_model():
    local_weights_path = "/tmp/best.torchscript"
    
    # Скачиваем файл только если его еще нет на сервере
    if not os.path.exists(local_weights_path):
        url = f"https://drive.google.com/uc?id={config.MODEL_DRIVE_FILE_ID}"
        gdown.download(url, local_weights_path, quiet=False)
        
    model = YOLO(local_weights_path, task="detect")
    return model

def process_single_image(image_bytes, model):
    img = Image.open(image_bytes).convert("RGB")
    results = model.predict(source=img, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
    
    cell_count = len(results.boxes)
    annotated_bgr = results.plot()
    annotated_rgb = annotated_bgr[..., ::-1]
    
    return annotated_rgb, cell_countimport streamlit as st
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

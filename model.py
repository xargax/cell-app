import streamlit as st
from PIL import Image
from ultralytics import YOLO
import gsheets

@st.cache_resource(show_spinner=False)
def load_yolo_model():
    # Загружаем файл весов из Google Drive во временную папку
    weights_path = gsheets.download_model_weights()
    # Ultralytics умеет работать с .torchscript напрямую
    model = YOLO(weights_path, task="detect")
    return model

def process_single_image(image_bytes, model):
    img = Image.open(image_bytes).convert("RGB")
    
    # Инференс на CPU
    # Порог conf можно настроить в зависимости от качества детекции
    results = model.predict(source=img, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
    
    # Количество найденных объектов (клеток)
    cell_count = len(results.boxes)
    
    # Отрисовка рамок детекции (plot возвращает BGR NumPy массив)
    annotated_bgr = results.plot()
    annotated_rgb = annotated_bgr[..., ::-1]  # конвертация в RGB для st.image
    
    return annotated_rgb, cell_countimport streamlit as st
import numpy as np
from PIL import Image
from ultralytics import YOLO
import gsheets

@st.cache_resource(show_spinner=False)
def load_yolo_model():
    weights_path = gsheets.download_model_weights()
    return YOLO(weights_path)

def process_single_image(image_bytes, model):
    img = Image.open(image_bytes).convert("RGB")
    results = model.predict(source=img, conf=0.25, imgsz=640, device="cpu", verbose=False)[0]
    
    boxes = results.boxes
    cell_count = len(boxes)
    annotated_bgr = results.plot()  # Возвращает массив NumPy BGR
    annotated_rgb = annotated_bgr[..., ::-1]
    
    return annotated_rgb, cell_count

import streamlit as st
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

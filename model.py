import os
import io
import streamlit as st
import torch
import torchvision
import numpy as np
import cv2
from PIL import Image
import gdown
import config

@st.cache_resource(show_spinner=False)
def load_yolo_model():
    local_weights_path = "/tmp/best.torchscript"
    if not os.path.exists(local_weights_path):
        url = f"https://drive.google.com/uc?id={config.MODEL_DRIVE_FILE_ID}"
        gdown.download(url, local_weights_path, quiet=False)
    
    # Загружаем граф TorchScript напрямую через PyTorch
    model = torch.jit.load(local_weights_path, map_location="cpu")
    model.eval()
    return model

def xywh2xyxy(x):
    """Конвертация [x_center, y_center, width, height] -> [x1, y1, x2, y2]"""
    y = torch.zeros_like(x) if isinstance(x, torch.Tensor) else np.zeros_like(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2
    y[:, 1] = x[:, 1] - x[:, 3] / 2
    y[:, 2] = x[:, 0] + x[:, 2] / 2
    y[:, 3] = x[:, 1] + x[:, 3] / 2
    return y

def non_max_suppression(prediction, conf_thres=0.25, iou_thres=0.45):
    """NMS для выходов YOLOv5"""
    # prediction shape: [1, num_boxes, 5 + num_classes] (x, y, w, h, obj_conf, cls_conf...)
    pred = prediction[0]
    
    # Фильтрация по confidence (объекта)
    if pred.shape[-1] > 5:
        scores = pred[:, 4:5] * pred[:, 5:]
        conf, class_idx = scores.max(1, keepdim=True)
        pred = torch.cat((pred[:, :4], conf, class_idx.float()), 1)
        pred = pred[conf.view(-1) > conf_thres]
    else:
        conf = pred[:, 4:5]
        pred = torch.cat((pred[:, :4], conf, torch.zeros_like(conf)), 1)
        pred = pred[conf.view(-1) > conf_thres]

    if not pred.shape[0]:
        return []

    # Преобразуем координаты в [x1, y1, x2, y2]
    boxes = xywh2xyxy(pred[:, :4])
    scores = pred[:, 4]
    
    # NMS из torchvision
    keep = torchvision.ops.nms(boxes, scores, iou_thres)
    return pred[keep]

def process_single_image(image_bytes, model, target_size=640, conf_thres=0.25):
    # 1. Чтение изображения
    pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    orig_w, orig_h = pil_img.size
    img_np = np.array(pil_img)

    # 2. Жёсткий ресайз в квадрат 640x640 (именно под него запечены размерности в TorchScript)
    resized_img = cv2.resize(img_np, (target_size, target_size))
    
    # Подготовка тензора: [H, W, C] -> [1, C, H, W], нормализация 0..1
    tensor = torch.from_numpy(resized_img).permute(2, 0, 1).float() / 255.0
    tensor = tensor.unsqueeze(0)

    # 3. Инференс
    with torch.no_grad():
        preds = model(tensor)
        # Если модель возвращает кортеж, берем первый тензор
        if isinstance(preds, (list, tuple)):
            preds = preds[0]

    # 4. Постобработка (NMS)
    detections = non_max_suppression(preds, conf_thres=conf_thres)
    
    cell_count = len(detections)

    # 5. Отрисовка рамок на исходном изображении
    annotated = img_np.copy()
    if cell_count > 0:
        gain_x = orig_w / target_size
        gain_y = orig_h / target_size
        
        for det in detections:
            x1 = int(det[0].item() * gain_x)
            y1 = int(det[1].item() * gain_y)
            x2 = int(det[2].item() * gain_x)
            y2 = int(det[3].item() * gain_y)
            conf = float(det[4].item())

            # Рисуем рамку вокруг клетки
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 75, 75), 2)
            label = f"{conf:.2f}"
            cv2.putText(annotated, label, (x1, max(y1 - 6, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 75, 75), 1)

    return annotated, cell_count

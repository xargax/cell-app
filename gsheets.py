import io
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]

@st.cache_resource
def get_gcredentials():
    creds_dict = dict(st.secrets["gcp_service_account"])
    # Коррекция экранирования переносов строк приватного ключа
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    return Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

@st.cache_resource(show_spinner=False)
def download_model_weights() -> str:
    creds = get_gcredentials()
    drive_service = build("drive", "v3", credentials=creds)
    request = drive_service.files().get_media(fileId=config.MODEL_DRIVE_FILE_ID)
    
    local_weights_path = "/tmp/best.torchscript"
    fh = io.FileIO(local_weights_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return local_weights_path

def get_sheets_client():
    return gspread.authorize(get_gcredentials())

def get_or_create_user(email: str, password_hash: str = None, mode: str = "login"):
    client = get_sheets_client()
    sheet = client.open_by_key(config.SPREADSHEET_ID).worksheet("users")
    records = sheet.get_all_records()
    
    user = next((r for r in records if r["email"] == email), None)
    
    if mode == "login":
        return user
    elif mode == "register":
        if user:
            return None  # Почта занята
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([email, password_hash, now])
        return {"email": email, "password_hash": password_hash, "created_at": now}

def save_session_history(email: str, img_count: int, counts_per_img: list, concentration: float):
    client = get_sheets_client()
    sheet = client.open_by_key(config.SPREADSHEET_ID).worksheet("sessions")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([
        email, 
        now, 
        img_count, 
        ", ".join(map(str, counts_per_img)), 
        f"{concentration:.2e}"
    ])

def fetch_user_history(email: str):
    client = get_sheets_client()
    sheet = client.open_by_key(config.SPREADSHEET_ID).worksheet("sessions")
    records = sheet.get_all_records()
    user_records = [r for r in records if r.get("email") == email]
    return user_records[::-1]

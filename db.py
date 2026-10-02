import sqlite3
from datetime import datetime, timezone

DB_NAME = "cell_app.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password_hash TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            timestamp TEXT,
            image_count INTEGER,
            counts_per_image TEXT,
            concentration TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_or_create_user(email: str, password_hash: str = None, mode: str = "login"):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    cur.execute("SELECT email, password_hash FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    
    if mode == "login":
        conn.close()
        return {"email": row[0], "password_hash": row[1]} if row else None
        
    elif mode == "register":
        if row:
            conn.close()
            return None
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO users VALUES (?, ?, ?)", (email, password_hash, now))
        conn.commit()
        conn.close()
        return {"email": email, "password_hash": password_hash, "created_at": now}

def save_session_history(email: str, img_count: int, counts_per_img: list, concentration: float):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    counts_str = ", ".join(map(str, counts_per_img))
    conc_str = f"{concentration:.2e}"
    
    cur.execute(
        "INSERT INTO sessions (email, timestamp, image_count, counts_per_image, concentration) VALUES (?, ?, ?, ?, ?)",
        (email, now, img_count, counts_str, conc_str)
    )
    conn.commit()
    conn.close()

def fetch_user_history(email: str):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT timestamp, image_count, concentration FROM sessions WHERE email = ? ORDER BY id DESC LIMIT 10",
        (email,)
    )
    rows = cur.fetchall()
    conn.close()
    
    return [
        {"timestamp": r[0], "image_count": r[1], "concentration": r[2]}
        for r in rows
    ]

def clear_user_history(email: str):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE email = ?", (email,))
    conn.commit()
    conn.close()

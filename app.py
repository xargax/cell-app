import streamlit as st
from datetime import datetime
import config
import auth
import db as gsheets  # Используем новую локальную БД SQLite
import model

st.set_page_config(page_title="Cell Counter", layout="wide", initial_sidebar_state="collapsed")

# Инициализация состояния
if "screen" not in st.session_state:
    st.session_state.screen = "auth"
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "selected_images" not in st.session_state:
    st.session_state.selected_images = []
if "results" not in st.session_state:
    st.session_state.results = None

# Стили для правостороннего drawer-меню
RIGHT_DRAWER_CSS = """
<style>
[data-testid="stSidebar"] { display: none; }
.drawer-toggle {
    position: fixed;
    top: 1rem;
    right: 1.5rem;
    z-index: 99999;
}
#drawer-check { display: none; }
.right-drawer {
    position: fixed;
    top: 0;
    right: -360px;
    width: 340px;
    height: 100vh;
    background-color: #1e1e24;
    color: #f1f1f1;
    box-shadow: -4px 0 15px rgba(0,0,0,0.3);
    transition: right 0.3s ease;
    z-index: 99998;
    padding: 80px 20px 20px 20px;
    overflow-y: auto;
}
#drawer-check:checked ~ .right-drawer { right: 0; }
.drawer-btn {
    display: inline-block;
    padding: 8px 14px;
    background-color: #ff4b4b;
    color: white;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
}
</style>
"""

def render_right_drawer():
    st.markdown(RIGHT_DRAWER_CSS, unsafe_allow_html=True)
    history = gsheets.fetch_user_history(st.session_state.user_email)
    
    history_html = "".join([
        f"<div style='border-bottom: 1px solid #444; padding: 8px 0;'>"
        f"<b>{h.get('timestamp', '')}</b><br>"
        f"Изображений: {h.get('image_count', 0)}<br>"
        f"Концентрация: <code>{h.get('concentration', '')} кл/мл</code>"
        f"</div>"
        for h in history[:10]
    ]) or "<p>История пока пуста</p>"
    
    drawer_html = f"""
    <div class="drawer-toggle">
        <label for="drawer-check" class="drawer-btn">☰ Профиль</label>
    </div>
    <input type="checkbox" id="drawer-check">
    <div class="right-drawer">
        <h3>{st.session_state.user_email}</h3>
        <hr style="border-color:#444">
        <h4>История сессий</h4>
        {history_html}
    </div>
    """
    st.markdown(drawer_html, unsafe_allow_html=True)
    
    # Кнопка выхода в интерфейсе Streamlit (в правом верхнем углу)
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("Выйти из аккаунта", key="logout_btn"):
            st.session_state.clear()
            st.session_state.screen = "auth"
            st.rerun()

# Инициализация режима формы (если еще не выбран)
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None

# --- ЭКРАН 1: АВТОРИЗАЦИЯ ---
if st.session_state.screen == "auth":
    # Стили для центрирования по вертикали и горизонтали
    st.markdown(
        """
        <style>
        /* Убираем стандартные отступы сверху для центрирования по высоте */
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            max-width: 100% !important;
        }
        .main-wrapper {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        .auth-card {
            width: 100%;
            max-width: 440px;
        }
        .auth-title {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .auth-title h1 {
            font-size: 2.1rem;
            margin-bottom: 0.3rem;
        }
        .auth-title p {
            color: #888;
            font-size: 0.95rem;
            margin: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Центрирующая сетка
    _, center_box, _ = st.columns([1, 1.2, 1])

    with center_box:
        # Небольшой отступ сверху для визуального баланса по высоте
        st.markdown("<div style='height: 10vh;'></div>", unsafe_allow_html=True)
        
        st.markdown(
            """
            <div class="auth-title">
                <h1>🔬 Подсчёт концентрации клеток</h1>
                <p>Автоматический анализ микропрепаратов</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Выбор: Вход / Регистрация
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("Вход", use_container_width=True, type="primary" if st.session_state.auth_mode == "login" else "secondary"):
                st.session_state.auth_mode = "login"
                st.rerun()
        with b_col2:
            if st.button("Регистрация", use_container_width=True, type="primary" if st.session_state.auth_mode == "register" else "secondary"):
                st.session_state.auth_mode = "register"
                st.rerun()

        # Форма ввода
        if st.session_state.auth_mode is not None:
            is_login = st.session_state.auth_mode == "login"
            mode_title = "Вход в систему" if is_login else "Регистрация нового пользователя"
            btn_title = "Войти" if is_login else "Зарегистрироваться"

            with st.container(border=True):
                st.markdown(f"<h4 style='text-align: center; margin-top: 0.2rem;'>{mode_title}</h4>", unsafe_allow_html=True)
                email = st.text_input("Электронная почта", placeholder="user@example.com").strip().lower()
                password = st.text_input("Пароль", type="password", placeholder="••••••••")
                
                st.write("")
                if st.button(btn_title, type="primary", use_container_width=True):
                    if not email or not password:
                        st.warning("Пожалуйста, заполните оба поля")
                    elif "@" not in email or "." not in email:
                        st.warning("Введите корректный адрес электронной почты")
                    elif "gcp_service_account" not in st.secrets:
                        st.error("Ошибка конфигурации: отсутствуют секреты [gcp_service_account].")
                    else:
                        try:
                            if is_login:
                                user = gsheets.get_or_create_user(email, mode="login")
                                if not user:
                                    st.error("Нет такого зарегистрированного пользователя. Пожалуйста, пройдите регистрацию.")
                                elif auth.verify_password(password, user.get("password_hash", "")):
                                    st.session_state.user_email = email
                                    st.session_state.screen = "upload"
                                    st.rerun()
                                else:
                                    st.error("Неверный пароль. Попробуйте снова.")
                            else:
                                hashed = auth.hash_password(password)
                                new_user = gsheets.get_or_create_user(email, hashed, mode="register")
                                if new_user:
                                    st.success("Регистрация успешна! Выполняется вход...")
                                    st.session_state.user_email = email
                                    st.session_state.screen = "upload"
                                    st.rerun()
                                else:
                                    st.error("Пользователь с такой почтой уже существует. Пожалуйста, нажмите «Вход».")
                        except Exception as e:
                            st.error(f"Не удалось подключиться к базе данных: {e}")
                            
# --- ЭКРАН 2: ЗАГРУЗКА ИЗОБРАЖЕНИЙ ---
elif st.session_state.screen == "upload":
    render_right_drawer()
    st.title("Загрузка микропрепаратов")
    st.caption("Добавьте от 1 до 4 изображений счетного поля (JPG, PNG)")
    
    uploaded_files = st.file_uploader(
        "Выберите файлы", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        for f in uploaded_files:
            if len(st.session_state.selected_images) < 4:
                # Проверка дубликатов по имени
                if not any(item["name"] == f.name for item in st.session_state.selected_images):
                    st.session_state.selected_images.append({"name": f.name, "bytes": f.read()})
            else:
                st.warning("Максимум 4 изображения. Лишние пропущены.")
                break

    if st.session_state.selected_images:
        st.subheader(f"Выбрано: {len(st.session_state.selected_images)} / 4")
        cols = st.columns(4)
        for idx, item in enumerate(st.session_state.selected_images):
            with cols[idx]:
                st.image(item["bytes"], use_container_width=True)
                st.caption(item["name"][:18])
                if st.button("Удалить", key=f"del_{idx}"):
                    st.session_state.selected_images.pop(idx)
                    st.rerun()
        
        st.divider()
        if st.button("🚀 Начать подсчёт", type="primary", use_container_width=True):
            st.session_state.screen = "processing"
            st.rerun()
    else:
        st.info("Загрузите хотя бы одно изображение для запуска обработки.")

# --- ЭКРАН 3: ОБРАБОТКА ---
elif st.session_state.screen == "processing":
    st.title("Обработка данных")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.text("Инициализация весов YOLO...")
    model_instance = model.load_yolo_model()
    progress_bar.progress(20)
    
    images = st.session_state.selected_images
    total_imgs = len(images)
    step_val = 60 / total_imgs
    
    processed_results = []
    counts = []
    
    for i, item in enumerate(images):
        status_text.text(f"Детекция клеток на изображении {i + 1} из {total_imgs}...")
        ann_img, count = model.process_single_image(item["bytes"], model_instance)
        processed_results.append({"annotated": ann_img, "count": count, "name": item["name"]})
        counts.append(count)
        progress_bar.progress(int(20 + (i + 1) * step_val))
        
    status_text.text("Расчёт концентрации и сохранение сессии...")
    avg_cells = sum(counts) / total_imgs
    concentration = (avg_cells / config.VOLUME_PER_IMAGE_ML) * config.DILUTION_FACTOR
    
    gsheets.save_session_history(
        st.session_state.user_email,
        total_imgs,
        counts,
        concentration
    )
    progress_bar.progress(100)
    status_text.text("Готово!")
    
    st.session_state.results = {
        "items": processed_results,
        "concentration": concentration,
        "avg_cells": avg_cells
    }
    st.session_state.selected_images = []  # Очищаем ОЗУ от исходных байтов
    st.session_state.screen = "results"
    st.rerun()

# --- ЭКРАН 4: РЕЗУЛЬТАТЫ ---
elif st.session_state.screen == "results":
    render_right_drawer()
    st.title("Результаты анализа")
    res = st.session_state.results
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Обработано полей", len(res["items"]))
    m2.metric("В среднем клеток на поле", f"{res['avg_cells']:.1f}")
    m3.metric("Концентрация", f"{res['concentration']:.2e} кл/мл")
    
    st.divider()
    cols = st.columns(len(res["items"]))
    for idx, item in enumerate(res["items"]):
        with cols[idx]:
            st.image(item["annotated"], use_container_width=True)
            st.markdown(f"**{item['name']}**")
            st.markdown(f"Найдено: **{item['count']}** клеток")
            
    st.divider()
    if st.button("Новый расчёт", type="primary"):
        st.session_state.results = None
        st.session_state.screen = "upload"
        st.rerun()

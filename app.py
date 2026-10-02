import streamlit as st
import config
import auth
import db as gsheets
import model

# Устанавливаем стандартную центрированную раскладку
st.set_page_config(page_title="Cell Counter", layout="centered", initial_sidebar_state="collapsed")

# Инициализация сессионных переменных
if "screen" not in st.session_state:
    st.session_state.screen = "auth"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "selected_images" not in st.session_state:
    st.session_state.selected_images = []
if "results" not in st.session_state:
    st.session_state.results = None

# Глобальные стили: центрирование контента и стилизация левого меню
GLOBAL_CSS = """
<style>
/* Ограничиваем ширину основной рабочей области и центрируем */
.block-container {
    max-width: 860px !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}

/* Скрываем стандартный сайдбар Streamlit */
[data-testid="stSidebar"] { display: none !important; }

/* Кнопка-аватар в левом верхнем углу */
.avatar-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.5rem;
}
.avatar-circle {
    width: 46px;
    height: 46px;
    border-radius: 50%;
    background: linear-gradient(135deg, #ff4b4b, #ff7676);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    transition: transform 0.2s;
}
.avatar-circle:hover {
    transform: scale(1.05);
}
.user-greeting {
    font-size: 1.05rem;
    font-weight: 600;
}

/* Выдвижное меню слева */
#drawer-toggle { display: none; }
.left-drawer-backdrop {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.45);
    z-index: 99998;
}
.left-drawer {
    position: fixed;
    top: 0;
    left: -380px;
    width: 360px;
    height: 100vh;
    background: #ffffff;
    box-shadow: 5px 0 25px rgba(0,0,0,0.25);
    z-index: 99999;
    transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    flex-direction: column;
    padding: 24px;
    box-sizing: border-box;
}

/* Открытие меню по чекбоксу */
#drawer-toggle:checked ~ .left-drawer {
    left: 0;
}
#drawer-toggle:checked ~ .left-drawer-backdrop {
    display: block;
}

/* Секции внутри меню */
.drawer-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding-bottom: 18px;
    border-bottom: 1px solid #eee;
}
.drawer-close {
    margin-left: auto;
    cursor: pointer;
    font-size: 1.4rem;
    color: #888;
}
.drawer-history {
    flex: 1;
    overflow-y: auto;
    padding: 16px 0;
}
.history-card {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
    font-size: 0.9rem;
}
.history-card b {
    color: #333;
}
.drawer-footer {
    padding-top: 14px;
    border-top: 1px solid #eee;
}
</style>
"""

def render_left_menu():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    
    email = st.session_state.user_email or "Пользователь"
    first_letter = email[0].upper()
    history = gsheets.fetch_user_history(email)
    
    # Формируем карточки истории исследований
    if history:
        history_cards = "".join([
            f"""
            <div class="history-card">
                <div style="color: #666; font-size: 0.8rem;">{h.get('timestamp', '')}</div>
                <div>Обработано полей: <b>{h.get('image_count', 0)}</b></div>
                <div>Концентрация: <b style="color: #ff4b4b;">{h.get('concentration', '')} кл/мл</b></div>
            </div>
            """
            for h in history
        ])
    else:
        history_cards = "<p style='color: #888; text-align: center; margin-top: 2rem;'>История исследований пуста</p>"

    # Разметка меню и аватара
    menu_html = f"""
    <input type="checkbox" id="drawer-toggle">
    <label for="drawer-toggle" class="left-drawer-backdrop"></label>

    <div class="avatar-header">
        <label for="drawer-toggle" class="avatar-circle">{first_letter}</label>
        <div class="user-greeting">
            <div>{email}</div>
            <div style="font-size: 0.8rem; color: #888; font-weight: normal;">Нажмите на аватар для меню</div>
        </div>
    </div>

    <div class="left-drawer">
        <!-- Секция 1: Информация о пользователе -->
        <div class="drawer-header">
            <div class="avatar-circle" style="width: 42px; height: 42px; font-size: 1.1rem;">{first_letter}</div>
            <div style="overflow: hidden; text-overflow: ellipsis; max-width: 200px;">
                <b style="font-size: 1rem; color: #111;">{email}</b>
                <div style="font-size: 0.8rem; color: #28a745;">● В сети</div>
            </div>
            <label for="drawer-toggle" class="drawer-close">✕</label>
        </div>

        <!-- Секция 2: История исследований -->
        <div style="font-weight: 600; font-size: 0.95rem; margin-top: 14px; color: #444;">
            История исследований
        </div>
        <div class="drawer-history">
            {history_cards}
        </div>

        <!-- Секция 3: Нижняя секция с кнопкой выхода -->
        <div class="drawer-footer">
            <div style="font-size: 0.8rem; color: #888; margin-bottom: 8px;">Сессия активна</div>
        </div>
    </div>
    """
    st.markdown(menu_html, unsafe_allow_html=True)

    # Стандартная кнопка Streamlit для надежного выхода из системы
    col_out, _ = st.columns([1, 2])
    with col_out:
        if st.button("🚪 Выйти из аккаунта", key="logout_btn", use_container_width=True):
            st.session_state.clear()
            st.session_state.screen = "auth"
            st.session_state.auth_mode = "login"
            st.rerun()

# ==========================================
# 1. ЭКРАН: АВТОРИЗАЦИЯ
# ==========================================
if st.session_state.screen == "auth":
    st.markdown(
        """
        <style>
        .auth-box {
            max-width: 440px;
            margin: 8vh auto 0 auto;
            text-align: center;
        }
        </style>
        <div class="auth-box">
            <h1>🔬 Cell Counter</h1>
            <p style="color: gray; margin-bottom: 2rem;">Автоматический подсчёт концентрации клеток</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    _, center_col, _ = st.columns([1, 2.2, 1])
    with center_col:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Вход", use_container_width=True, type="primary" if st.session_state.auth_mode == "login" else "secondary"):
                st.session_state.auth_mode = "login"
                st.rerun()
        with c2:
            if st.button("Регистрация", use_container_width=True, type="primary" if st.session_state.auth_mode == "register" else "secondary"):
                st.session_state.auth_mode = "register"
                st.rerun()

        is_login = st.session_state.auth_mode == "login"
        
        with st.container(border=True):
            st.subheader("Вход" if is_login else "Регистрация")
            email = st.text_input("Электронная почта", placeholder="name@example.com").strip().lower()
            password = st.text_input("Пароль", type="password", placeholder="••••••••")
            st.write("")
            
            if st.button("Продолжить", type="primary", use_container_width=True):
                if not email or not password:
                    st.warning("Заполните оба поля")
                elif "@" not in email or "." not in email:
                    st.warning("Введите корректную почту")
                else:
                    if is_login:
                        user = gsheets.get_or_create_user(email, mode="login")
                        if not user:
                            st.error("Нет такого зарегистрированного пользователя. Пожалуйста, перейдите в «Регистрация».")
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
                            st.success("Успешная регистрация!")
                            st.session_state.user_email = email
                            st.session_state.screen = "upload"
                            st.rerun()
                        else:
                            st.error("Пользователь с такой почтой уже существует. Выберите «Вход».")

# ==========================================
# 2. ЭКРАН: ЗАГРУЗКА ИЗОБРАЖЕНИЙ
# ==========================================
elif st.session_state.screen == "upload":
    render_left_menu()
    
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
                if not any(item["name"] == f.name for item in st.session_state.selected_images):
                    st.session_state.selected_images.append({"name": f.name, "bytes": f.read()})
            else:
                st.warning("Достигнут лимит: максимум 4 изображения.")
                break

    if st.session_state.selected_images:
        st.write(f"Выбрано изображений: **{len(st.session_state.selected_images)} / 4**")
        
        # Сетка миниатюр
        cols = st.columns(len(st.session_state.selected_images))
        for idx, item in enumerate(st.session_state.selected_images):
            with cols[idx]:
                with st.container(border=True):
                    st.image(item["bytes"], use_container_width=True)
                    st.caption(item["name"][:14])
                    if st.button("Удалить", key=f"del_{idx}", use_container_width=True):
                        st.session_state.selected_images.pop(idx)
                        st.rerun()
        
        st.divider()
        if st.button("🚀 Начать подсчёт", type="primary", use_container_width=True):
            st.session_state.screen = "processing"
            st.rerun()
    else:
        st.info("Загрузите хотя бы одно изображение для запуска обработки.")

# ==========================================
# 3. ЭКРАН: ОБРАБОТКА (Без меню)
# ==========================================
elif st.session_state.screen == "processing":
    st.markdown("<h2 style='text-align: center; margin-top: 15vh;'>Выполняется детекция клеток</h2>", unsafe_allow_html=True)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    status_text.caption("Загрузка модели детекции...")
    model_instance = model.load_yolo_model()
    progress_bar.progress(20)
    
    images = st.session_state.selected_images
    total = len(images)
    step = 60 / total
    
    processed = []
    counts = []
    
    for i, item in enumerate(images):
        status_text.caption(f"Анализ изображения {i+1} из {total}...")
        ann_img, count = model.process_single_image(item["bytes"], model_instance)
        processed.append({"annotated": ann_img, "count": count, "name": item["name"]})
        counts.append(count)
        progress_bar.progress(int(20 + (i + 1) * step))
        
    status_text.caption("Вычисление концентрации...")
    avg_cells = sum(counts) / total
    concentration = (avg_cells / config.VOLUME_PER_IMAGE_ML) * config.DILUTION_FACTOR
    
    # Запись в локальную базу данных
    gsheets.save_session_history(
        st.session_state.user_email,
        total,
        counts,
        concentration
    )
    progress_bar.progress(100)
    
    st.session_state.results = {
        "items": processed,
        "concentration": concentration,
        "avg_cells": avg_cells
    }
    st.session_state.selected_images = []
    st.session_state.screen = "results"
    st.rerun()

# ==========================================
# 4. ЭКРАН: РЕЗУЛЬТАТЫ
# ==========================================
elif st.session_state.screen == "results":
    render_left_menu()
    
    st.title("Результаты анализа")
    res = st.session_state.results
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Обработано полей", len(res["items"]))
    m2.metric("Среднее число клеток", f"{res['avg_cells']:.1f}")
    m3.metric("Концентрация", f"{res['concentration']:.2e} кл/мл")
    
    st.divider()
    cols = st.columns(len(res["items"]))
    for idx, item in enumerate(res["items"]):
        with cols[idx]:
            with st.container(border=True):
                st.image(item["annotated"], use_container_width=True)
                st.markdown(f"**{item['name']}**")
                st.markdown(f"Найдено: **{item['count']}**")
            
    st.divider()
    if st.button("Новый расчёт", type="primary", use_container_width=True):
        st.session_state.results = None
        st.session_state.screen = "upload"
        st.rerun()

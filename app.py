import streamlit as st
import config
import auth
import db as gsheets
import model

st.set_page_config(
    page_title="Cell Counter", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Инициализация состояния
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

# Стили оформления страницы и Drawer-меню
STYLE_CSS = """
<style>
/* Отступ сверху для контента */
.block-container {
    max-width: 840px !important;
    padding-top: 5rem !important;
    padding-bottom: 4rem !important;
    margin: 0 auto !important;
}

/* Оформление Drawer-панели */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-right: 1px solid #e9ecef !important;
    box-shadow: 4px 0 20px rgba(0,0,0,0.08) !important;
    z-index: 999999 !important;
}

/* Кнопка открытия меню (слева вверху) */
button[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    position: fixed !important;
    top: 16px !important;
    left: 20px !important;
    z-index: 1000000 !important;
    background: #ff4b4b !important;
    color: white !important;
    border-radius: 50% !important;
    width: 44px !important;
    height: 44px !important;
    box-shadow: 0 2px 10px rgba(255, 75, 75, 0.35) !important;
    justify-content: center !important;
    align-items: center !important;
    border: none !important;
}
button[data-testid="stSidebarCollapsedControl"] svg {
    fill: white !important;
    stroke: white !important;
    width: 22px !important;
    height: 22px !important;
}

/* Карточки истории */
.history-item {
    background-color: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 0.88rem;
}

/* Профиль вверху */
.profile-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 1rem;
    border-bottom: 1px solid #eee;
    margin-bottom: 1rem;
}
.profile-avatar {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #ff4b4b, #ff7676);
    color: white;
    font-weight: bold;
    font-size: 1.2rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* Отключаем полосу прокрутки у самого сайдбара */
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    overflow: hidden !important;
    height: 100vh !important;
    padding-bottom: 0 !important;
}

/* Область истории: компактная адаптивная высота, скролл только при переполнении записями */
.history-scroll-box {
    max-height: calc(100vh - 280px) !important;
    overflow-y: auto !important;
    padding-right: 4px;
    scrollbar-width: thin;
}

/* Кнопка выхода: аккуратный отступ 32px от нижнего края */
div[data-testid="stSidebar"] div.stButton:has(button[key="logout_btn"]),
div[data-testid="stSidebar"] div.stButton {
    position: fixed !important;
    bottom: 32px !important;
    left: 20px !important;
    width: calc(100% - 40px) !important;
    max-width: 295px !important;
    z-index: 100000 !important;
}

</style>
"""

def render_drawer_menu():
    st.markdown(STYLE_CSS, unsafe_allow_html=True)
    email = st.session_state.user_email or "Пользователь"
    first_letter = email[0].upper()

    with st.sidebar:
        # Секция 1: Профиль пользователя
        st.markdown(
            f"""
            <div class="profile-box">
                <div class="profile-avatar">{first_letter}</div>
                <div style="overflow: hidden; text-overflow: ellipsis;">
                    <div style="font-weight: 700; color: #222; font-size: 0.95rem;">{email}</div>
                    <div style="color: #28a745; font-size: 0.8rem;">● Авторизован</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Секция 2: История исследований (на всю доступную высоту)
        st.markdown("##### 📋 История исследований")
        history = gsheets.fetch_user_history(email)
        
        if history:
            history_html = "".join([
                f"""
                <div class="history-item">
                    <div style="color: #888; font-size: 0.78rem;">{h.get('timestamp', '')}</div>
                    <div style="margin-top: 2px;">Полей: <b>{h.get('image_count', 0)}</b></div>
                    <div>Концентрация: <b style="color: #ff4b4b;">{h.get('concentration', '')} кл/мл</b></div>
                </div>
                """
                for h in history
            ])
        else:
            history_html = "<div style='color: #888; font-size: 0.88rem; padding: 12px 0;'>История исследований пока пуста.</div>"

        st.markdown(f'<div class="history-scroll-box">{history_html}</div>', unsafe_allow_html=True)

        # Секция 3: Кнопка выхода (прижата к низу через position: fixed)
        if st.button("🚪 Выйти из аккаунта", key="logout_btn", use_container_width=True, type="secondary"):
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
        .block-container {
            max-width: 480px !important;
            padding-top: 8vh !important;
            margin: 0 auto !important;
        }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        </style>
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2>🔬 Cell Counter</h2>
            <p style="color: gray; margin: 0;">Автоматический подсчёт концентрации клеток</p>
        </div>
        """,
        unsafe_allow_html=True
    )

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
        st.subheader("Вход в систему" if is_login else "Создание аккаунта")
        email = st.text_input("Электронная почта", placeholder="user@example.com").strip().lower()
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
                        st.error("Нет такого зарегистрированного пользователя. Пожалуйста, перейдите во вкладку «Регистрация».")
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
                        st.error("Пользователь с такой почтой уже существует. Выберите «Вход».")

# ==========================================
# 2. ЭКРАН: ЗАГРУЗКА ИЗОБРАЖЕНИЙ
# ==========================================
elif st.session_state.screen == "upload":
    render_drawer_menu()

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
    st.markdown("<style>[data-testid='stSidebarCollapsedControl'] { display: none !important; }</style>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; margin-top: 10vh;'>Выполняется детекция клеток</h2>", unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    status_text.caption("Загрузка весов модели...")
    model_instance = model.load_yolo_model()
    progress_bar.progress(20)

    images = st.session_state.selected_images
    total = len(images)
    step = 60 / total

    processed = []
    counts = []

    for i, item in enumerate(images):
        status_text.caption(f"Обработка изображения {i+1} из {total}...")
        ann_img, count = model.process_single_image(item["bytes"], model_instance)
        processed.append({"annotated": ann_img, "count": count, "name": item["name"]})
        counts.append(count)
        progress_bar.progress(int(20 + (i + 1) * step))

    status_text.caption("Расчёт концентрации...")
    avg_cells = sum(counts) / total
    concentration = (avg_cells / config.VOLUME_PER_IMAGE_ML) * config.DILUTION_FACTOR

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
    render_drawer_menu()

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

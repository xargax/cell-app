import streamlit as st
import config
import auth
import db as gsheets
import model

st.set_page_config(
    page_title="Cell Counter", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

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

# Диалоговые окна подтверждения
@st.dialog("Очистка истории")
def confirm_clear_history_dialog():
    st.write("Вы действительно хотите удалить всю историю исследований? Это действие нельзя отменить.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Да, очистить", type="primary", width="stretch"):
            gsheets.clear_user_history(st.session_state.user_email)
            st.rerun()
    with c2:
        if st.button("Отмена", width="stretch"):
            st.rerun()

@st.dialog("Выход из системы")
def confirm_logout_dialog():
    st.write("Вы действительно хотите выйти из текущего аккаунта?")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Да, выйти", type="primary", width="stretch"):
            st.session_state.clear()
            st.session_state.screen = "auth"
            st.session_state.auth_mode = "login"
            st.rerun()
    with c2:
        if st.button("Отмена", width="stretch"):
            st.rerun()

STYLE_CSS = """
<style>
/* 1. Отключаем полноэкранный зум на фотографиях */
button[title="View fullscreen"] {
    display: none !important;
}

/* 2. Центрирование модального окна строго посередине экрана */
[data-testid="stModal"],
div[data-baseweb="modal"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding-top: 0 !important;
}

div[role="dialog"] {
    margin: auto !important;
    max-height: 85vh !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.25) !important;
}

/* 3. Отступ основного контента */
.block-container {
    max-width: 860px !important;
    padding-top: 4.5rem !important;
    padding-bottom: 3rem !important;
    margin: 0 auto !important;
}

/* 4. Сайдбар: контрастный фон */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    background-color: #eef1f5 !important;
    border-right: 1px solid #dce1e7 !important;
    overflow: hidden !important;
    height: 100vh !important;
    box-sizing: border-box !important;
}

/* Скрываем скроллбар сайдбара */
[data-testid="stSidebarContent"]::-webkit-scrollbar,
[data-testid="stSidebarUserContent"]::-webkit-scrollbar {
    display: none !important;
    width: 0 !important;
}

/* Шапка профиля */
.profile-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid #dce1e7;
    margin-bottom: 0.8rem;
}
.profile-avatar {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, #ff4b4b, #ff7676);
    color: white;
    font-weight: 700;
    font-size: 1.05rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

/* Область истории: зафиксирована по высоте, чтобы не схлопывалась при пустой истории */
.history-scroll-box {
    height: calc(100vh - 245px) !important;
    max-height: calc(100vh - 245px) !important;
    overflow-y: auto !important;
    padding-right: 4px;
    scrollbar-width: thin;
}

/* Карточки истории */
.history-item {
    background-color: #ffffff;
    border-radius: 6px;
    border: 1px solid #dce1e7;
    padding: 8px 12px;
    margin-bottom: 8px;
    font-size: 0.84rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}

/* Кнопки в сайдбаре: фиксируем внизу панели */
[data-testid="stSidebar"] div.stButton:has(button[key="clear_hist_btn"]) {
    position: fixed !important;
    bottom: 68px !important;
    left: 18px !important;
    width: calc(100% - 36px) !important;
    max-width: 295px !important;
    z-index: 1000000 !important;
}

[data-testid="stSidebar"] div.stButton:has(button[key="logout_btn"]) {
    position: fixed !important;
    bottom: 22px !important;
    left: 18px !important;
    width: calc(100% - 36px) !important;
    max-width: 295px !important;
    z-index: 1000000 !important;
}

[data-testid="stSidebar"] div.stButton button {
    height: 38px !important;
    font-size: 0.85rem !important;
    border-radius: 6px !important;
}

/* Круглые индикаторы для легенды */
.dot-indicator {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
}
.dot-viable { background-color: #0046ff; }
.dot-dead { background-color: #00e6e6; }
.dot-budding { 
    background-color: #ffffff; 
    border: 1.5px solid #555555; 
}
</style>
"""

def render_drawer_menu():
    st.markdown(STYLE_CSS, unsafe_allow_html=True)
    email = st.session_state.user_email or "Пользователь"
    first_letter = email[0].upper()

    with st.sidebar:
        # Профиль
        st.markdown(
            f"""<div class="profile-box">
<div class="profile-avatar">{first_letter}</div>
<div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
<div style="font-weight: 600; color: #222; font-size: 0.92rem;">{email}</div>
<div style="color: #28a745; font-size: 0.78rem;">● Авторизован</div>
</div>
</div>""",
            unsafe_allow_html=True
        )

        # Заголовок
        st.markdown("<div style='font-weight: 600; font-size: 0.88rem; margin-bottom: 8px; color: #444;'>История исследований</div>", unsafe_allow_html=True)
        
        # Получение истории
        history = gsheets.fetch_user_history(email)
        if history:
            cards = [
                f'<div class="history-item">'
                f'<div style="color: #888; font-size: 0.76rem;">{h.get("timestamp", "")}</div>'
                f'<div style="margin-top: 3px;">Полей: <b>{h.get("image_count", 0)}</b></div>'
                f'<div>Концентрация: <b style="color: #ff4b4b;">{h.get("concentration", "")} кл/мл</b></div>'
                f'</div>'
                for h in history
            ]
            history_html = "".join(cards)
        else:
            history_html = "<div style='color: #888; font-size: 0.85rem; padding: 10px 0;'>История исследований пуста.</div>"

        # Скроллируемая область истории
        st.markdown(f'<div class="history-scroll-box">{history_html}</div>', unsafe_allow_html=True)

        # Нижние кнопки
        if st.button("Очистить историю", key="clear_hist_btn", width="stretch", type="secondary"):
            confirm_clear_history_dialog()
            
        if st.button("Выйти из аккаунта", key="logout_btn", width="stretch", type="secondary"):
            confirm_logout_dialog()

# ==========================================
# 1. ЭКРАН: АВТОРИЗАЦИЯ
# ==========================================
if st.session_state.screen == "auth":
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 460px !important;
            padding-top: 8vh !important;
            margin: 0 auto !important;
        }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        </style>
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2>Cell Counter</h2>
            <p style="color: gray; margin: 0; font-size: 0.95rem;">Автоматический подсчёт концентрации клеток</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Вход", width="stretch", type="primary" if st.session_state.auth_mode == "login" else "secondary"):
            st.session_state.auth_mode = "login"
            st.rerun()
    with c2:
        if st.button("Регистрация", width="stretch", type="primary" if st.session_state.auth_mode == "register" else "secondary"):
            st.session_state.auth_mode = "register"
            st.rerun()

    is_login = st.session_state.auth_mode == "login"

    with st.container(border=True):
        st.subheader("Вход в систему" if is_login else "Создание аккаунта")
        email = st.text_input("Электронная почта", placeholder="user@example.com").strip().lower()
        password = st.text_input("Пароль", type="password", placeholder="••••••••")
        st.write("")

        if st.button("Продолжить", type="primary", width="stretch"):
            if not email or not password:
                st.warning("Заполните оба поля")
            elif "@" not in email or "." not in email:
                st.warning("Введите корректную почту")
            else:
                if is_login:
                    user = gsheets.get_or_create_user(email, mode="login")
                    if not user:
                        st.error("Нет такого зарегистрированного пользователя. Перейдите во вкладку «Регистрация».")
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
    st.caption("Добавьте изображения счетного поля (JPG, PNG)")

    uploaded_files = st.file_uploader(
        "Выберите файлы", 
        type=["png", "jpg", "jpeg"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        for f in uploaded_files:
            if not any(item["name"] == f.name for item in st.session_state.selected_images):
                st.session_state.selected_images.append({"name": f.name, "bytes": f.read()})

    if st.session_state.selected_images:
        st.write(f"Выбрано изображений: **{len(st.session_state.selected_images)}**")

        # Аккуратная сетка: 3 миниатюры в ряд, не раздувает фото на весь экран
        GRID_COLS = 3
        for row_start in range(0, len(st.session_state.selected_images), GRID_COLS):
            row_items = st.session_state.selected_images[row_start:row_start + GRID_COLS]
            cols = st.columns(GRID_COLS)
            for idx in range(GRID_COLS):
                with cols[idx]:
                    if idx < len(row_items):
                        real_idx = row_start + idx
                        item = row_items[idx]
                        with st.container(border=True):
                            st.image(item["bytes"], width="stretch")
                            st.caption(item["name"])
                            if st.button("Удалить", key=f"del_{real_idx}", width="stretch"):
                                st.session_state.selected_images.pop(real_idx)
                                st.rerun()

        st.divider()
        if st.button("Начать подсчёт", type="primary", width="stretch"):
            st.session_state.screen = "processing"
            st.rerun()
    else:
        st.info("Загрузите хотя бы одно изображение для запуска обработки.")

# ==========================================
# 3. ЭКРАН: ОБРАБОТКА
# ==========================================
elif st.session_state.screen == "processing":
    st.markdown("<style>[data-testid='stSidebarCollapsedControl'] { display: none !important; }</style>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; margin-top: 12vh;'>Выполняется детекция клеток</h3>", unsafe_allow_html=True)
    
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
        status_text.caption(f"Обработка изображения {i+1} из {total}...")
        ann_img, count, class_breakdown = model.process_single_image(item["bytes"], model_instance)
        processed.append({
            "annotated": ann_img, 
            "count": count, 
            "name": item["name"],
            "classes": class_breakdown
        })
        counts.append(count)
        progress_bar.progress(int(20 + (i + 1) * step))

    status_text.caption("Расчёт концентрации...")
    avg_cells = sum(counts) / total if total > 0 else 0
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

    # Основные метрики
    m1, m2, m3 = st.columns(3)
    m1.metric("Обработано полей", len(res["items"]))
    m2.metric("В среднем клеток на поле", f"{res['avg_cells']:.1f}")
    m3.metric("Итоговая концентрация", f"{res['concentration']:.2e} кл/мл")

    st.write("")
    
    # Легенда
    st.markdown(
        """
        <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 10px 16px; margin-bottom: 1.2rem; display: flex; gap: 24px; font-size: 0.88rem; align-items: center;">
            <span style="font-weight: 600; color: #333;">Обозначения:</span>
            <span><span class="dot-indicator dot-viable"></span>Жизнеспособные</span>
            <span><span class="dot-indicator dot-dead"></span>Нежизнеспособные</span>
            <span><span class="dot-indicator dot-budding"></span>Почкующиеся</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Сетка результатов: 3 колонки
    GRID_COLS = 3
    for row_start in range(0, len(res["items"]), GRID_COLS):
        row_items = res["items"][row_start:row_start + GRID_COLS]
        cols = st.columns(GRID_COLS)
        for idx in range(GRID_COLS):
            with cols[idx]:
                if idx < len(row_items):
                    item = row_items[idx]
                    with st.container(border=True):
                        st.image(item["annotated"], width="stretch")
                        st.markdown(f"**{item['name']}**")
                        st.markdown(f"Всего: **{item['count']}** кл.")
                        
                        c = item.get("classes", {})
                        st.caption(
                            f'<span class="dot-indicator dot-viable"></span>Жизнеспособных: <b>{c.get("viable", 0)}</b><br>'
                            f'<span class="dot-indicator dot-dead"></span>Нежизнеспособных: <b>{c.get("dead", 0)}</b><br>'
                            f'<span class="dot-indicator dot-budding"></span>Почкующихся: <b>{c.get("budding", 0)}</b>',
                            unsafe_allow_html=True
                        )

    st.divider()
    if st.button("Новый расчёт", type="primary", width="stretch"):
        st.session_state.results = None
        st.session_state.screen = "upload"
        st.rerun()

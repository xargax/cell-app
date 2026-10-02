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

# Диалоговые окна подтверждения
@st.dialog("Очистка истории")
def confirm_clear_history_dialog():
    st.write("Вы уверены, что хотите удалить всю историю исследований? Это действие нельзя отменить.")
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

# Стили оформления страницы и Drawer-меню
<style>
/* 1. Отключаем полноэкранный зум картинок Streamlit */
button[title="View fullscreen"] {
    display: none !important;
}

/* 2. Контейнер сайдбара с правильным Flexbox без обрезания кнопок */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {
    background-color: #f4f5f7 !important;
    border-right: 1px solid #e2e5e9 !important;
    padding: 0.8rem 0.8rem 0.5rem 0.8rem !important;
    overflow: hidden !important;
    height: 100vh !important;
    box-sizing: border-box !important;
}

/* 3. Профиль пользователя */
.profile-box {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 0.6rem;
    border-bottom: 1px solid #e2e5e9;
    margin-bottom: 0.6rem;
}
.profile-avatar {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #ff4b4b, #ff7676);
    color: white;
    font-weight: 700;
    font-size: 1rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

/* 4. Область истории: запас снизу под 2 кнопки */
.history-scroll-box {
    height: calc(100vh - 220px) !important;
    max-height: calc(100vh - 220px) !important;
    overflow-y: auto !important;
    padding-right: 4px;
    scrollbar-width: thin;
}

.history-item {
    background-color: #ffffff;
    border-radius: 6px;
    border: 1px solid #e0e4e8;
    padding: 8px 10px;
    margin-bottom: 6px;
    font-size: 0.82rem;
}

/* 5. Кнопки в Drawer: прижаты к низу, чётко видны */
[data-testid="stSidebar"] div.stButton button {
    height: 34px !important;
    font-size: 0.82rem !important;
    border-radius: 6px !important;
    padding: 0 8px !important;
}

/* Точечные маркеры */
.dot-indicator {
    display: inline-block;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
}
.dot-viable { background-color: #0046ff; }
.dot-dead { background-color: #00e6e6; }
.dot-budding { 
    background-color: #ffffff; 
    border: 1.5px solid #555555; 
}
</style>

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
<div style="font-weight: 600; color: #222; font-size: 0.9rem;">{email}</div>
<div style="color: #28a745; font-size: 0.75rem;">● Авторизован</div>
</div>
</div>""",
            unsafe_allow_html=True
        )

        # История
        st.markdown("<div style='font-weight: 600; font-size: 0.84rem; margin-bottom: 6px; color: #444;'>История исследований</div>", unsafe_allow_html=True)
        
        history = gsheets.fetch_user_history(email)
        if history:
            cards = [
                f'<div class="history-item">'
                f'<div style="color: #888; font-size: 0.74rem;">{h.get("timestamp", "")}</div>'
                f'<div style="margin-top: 2px;">Полей: <b>{h.get("image_count", 0)}</b></div>'
                f'<div>Концентрация: <b style="color: #ff4b4b;">{h.get("concentration", "")} кл/мл</b></div>'
                f'</div>'
                for h in history
            ]
            history_html = "".join(cards)
        else:
            history_html = "<div style='color: #888; font-size: 0.82rem; padding: 10px 0;'>История исследований пуста.</div>"

        st.markdown(f'<div class="history-scroll-box">{history_html}</div>', unsafe_allow_html=True)

        # Кнопки управления внизу панели
        st.write("")
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

        # Фиксированная сетка по 2 карточки в ряд (чтобы одиночный снимок не растягивался на весь экран)
        GRID_COLS = 2
        for row_start in range(0, len(st.session_state.selected_images), GRID_COLS):
            row_items = st.session_state.selected_images[row_start:row_start + GRID_COLS]
            cols = st.columns(GRID_COLS)
            for idx, item in enumerate(row_items):
                real_idx = row_start + idx
                with cols[idx]:
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

    # Сетка результатов по 2 в ряд
    GRID_COLS = 2
    for row_start in range(0, len(res["items"]), GRID_COLS):
        row_items = res["items"][row_start:row_start + GRID_COLS]
        cols = st.columns(GRID_COLS)
        for idx, item in enumerate(row_items):
            with cols[idx]:
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

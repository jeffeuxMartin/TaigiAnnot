import streamlit as st
# st.write("Streamlit version:", st.__version__)
from streamlit_cookies_manager import EncryptedCookieManager
# import streamlit_cookies_manager
# st.write("streamlit-cookies-manager version:", streamlit_cookies_manager.__version__)

from auth import USERS, init_session_state, restore_login_from_cookie, login, logout
from pages_qc import qc_page

st.set_page_config(
    page_title="!!!臺語音訊標註!!!",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

cookies = EncryptedCookieManager(
    prefix="taigi_label_",
    password=st.secrets.get("COOKIE_PASSWORD", "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"),
)

if not cookies.ready():
    st.stop()


def login_page() -> None:
    st.title("登入")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("帳號")
        password = st.text_input("密碼", type="password")
        submitted = st.form_submit_button("登入")

    if submitted:
        login(cookies, username, password)


init_session_state()
restore_login_from_cookie(cookies, USERS)

if not st.session_state.logged_in:
    login_page()
else:
    c1, c2 = st.columns([4, 1])
    with c1:
        st.caption(f"目前登入：{st.session_state.username}")
    with c2:
        if st.button("登出", use_container_width=True):
            logout(cookies)

    qc_page()

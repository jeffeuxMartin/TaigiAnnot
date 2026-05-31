import streamlit as st

USERS = {f"u{i}": f"pass{i}" for i in range(1, 6)}


def init_session_state() -> None:
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", None)
    st.session_state.setdefault("just_logged_out", False)


def restore_login_from_cookie(cookies, users=None) -> None:
    users = users or USERS

    if st.session_state.logged_in:
        return

    if st.session_state.just_logged_out:
        return

    username = cookies.get("username")
    logged_in = cookies.get("logged_in")

    if logged_in == "1" and username in users:
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.just_logged_out = False


def login(cookies, username: str, password: str, users=None) -> None:
    users = users or USERS
    username = username.strip()
    password = password.strip()

    if users.get(username) != password:
        st.error("帳號或密碼錯誤")
        return

    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.just_logged_out = False

    cookies["logged_in"] = "1"
    cookies["username"] = username
    cookies.save()

    st.rerun()


def logout(cookies) -> None:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.just_logged_out = True

    cookies["logged_in"] = "0"
    cookies["username"] = ""
    cookies.save()

    st.query_params.clear()
    st.rerun()

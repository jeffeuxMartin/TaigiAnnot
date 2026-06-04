from __future__ import annotations

from html import escape

import streamlit as st
import qc_api


INTENT_EMOJI = {
    "SOS_CALL": "🚨",
    "FALL_HELP": "🫏",
    "BREATHING_CHEST_EMERG": "😰",
    "PAIN_GENERAL": "🤬",
    "CALL_CONTACT": "📞",
    "LIGHT_ON": "💡",
    "LIGHT_OFF": "🌑",
    "CANCEL_ALERT": "❌",
}

INTENT_LABELS = {
    "SOS_CALL": "危急",
    "FALL_HELP": "跌倒",
    "BREATHING_CHEST_EMERG": "胸喘",
    "PAIN_GENERAL": "痛爆",
    "CALL_CONTACT": "電話",
    "LIGHT_ON": "開燈",
    "LIGHT_OFF": "關燈",
    "CANCEL_ALERT": "取消",
}


def inject_css() -> None:
    st.markdown("""
    <style>
    section.main > div { max-width: 760px; padding-top: .6rem; }
    .qc-card { background:#f7f7f7; border-radius:18px; padding:1rem; box-shadow:0 2px 12px rgba(0,0,0,.08); }
    .qc-top { display:flex; justify-content:space-between; align-items:center; background:#344354; color:white; padding:.75rem 1rem; border-radius:12px; margin-bottom:.8rem; }
    .qc-emoji { font-size:2rem; text-align:center; }
    .qc-label { color:#777; font-size:.75rem; letter-spacing:.08em; text-transform:uppercase; margin-top:.5rem; }
    .qc-qw { color:#a33; font-weight:700; font-size:1.2rem; }
    .qc-tt { color:#2c8a3d; font-size:1.05rem; }
    .qc-whisper { color:#1d4ed8; font-size:1.05rem; }
    .qc-meta { display:grid; grid-template-columns:repeat(3,1fr); gap:.8rem; margin:.8rem 0; }
    .qc-val { font-size:1.1rem; overflow-wrap:anywhere; }
    .qc-intent { color:#b54a42; font-weight:700; }
    .qc-source { color:#888; font-size:.75rem; overflow-wrap:anywhere; margin-top:.6rem; }
    div[data-testid="stButton"] button { min-height:3rem; font-size:1.1rem; }
    div[data-testid="stCheckbox"] label { font-size:1.05rem; line-height:1.6; }
    audio { width:100%; }
    </style>
    """, unsafe_allow_html=True)


def go_prev_item(username: str) -> bool:
    prev_item = qc_api.get_prev_item(username)

    if prev_item is None:
        st.warning("沒有上一筆。")
        return False

    prev_item["_mode"] = "edit"
    st.session_state.qc_item = prev_item
    return True



def _bool_result(item: dict, key: str) -> bool:
    return bool(item.get("_result", {}).get(key, False))


def _text_result(item: dict, key: str) -> str:
    return str(item.get("_result", {}).get(key, "") or "")


def render_item(item: dict, username: str) -> None:
    intent = item.get("intent", "—")
    emoji = INTENT_EMOJI.get(intent, "?")
    intent_label = INTENT_LABELS.get(intent, intent)
    mode = item.get("_mode", "current")

    st.markdown('<div class="qc-card">', unsafe_allow_html=True)

    c0, c1, c2, c3 = st.columns([1, 1, .8, 1])
    with c0:
        prev = st.button("←", use_container_width=True)
    with c1:
        skip = st.button("跳", use_container_width=True, disabled=(mode == "edit"))
    with c2:
        st.markdown(f'<div class="qc-emoji">{escape(emoji)}</div>', unsafe_allow_html=True)
    with c3:
        submit_label = "更" if mode == "edit" else "提"
        submit = st.button(submit_label, type="primary", use_container_width=True)

    st.markdown('<div class="qc-label">Transcript</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="qc-qw">{escape(item.get("transcription_model1") or "（空）")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="qc-tt">{escape(item.get("transcription_model2") or "")}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="qc-whisper">{escape(item.get("transcription_model3") or "")}</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="qc-meta">
      <div><div class="qc-label">Intent</div><div class="qc-val qc-intent">{escape(intent_label)}</div></div>
      <div><div class="qc-label">Speaker</div><div class="qc-val">{escape(item.get("speaker_id", ""))}</div></div>
      <div><div class="qc-label">Split</div><div class="qc-val">{escape(item.get("split", ""))}</div></div>
    </div>
    """, unsafe_allow_html=True)

    url = qc_api.audio_url(item.get("file_name", ""))
    st.caption("Audio URL")
    st.code(url or "（目前沒有音檔網址）", language="text")

    key_suffix = f"{item['utterance_id']}_{mode}"

    opt_empty = st.checkbox(
        "a. 空音檔",
        value=_bool_result(item, "opt_empty"),
        key=f"empty_{key_suffix}",
    )
    opt_incomplete = st.checkbox(
        "b. 錄音不完全",
        value=_bool_result(item, "opt_incomplete"),
        key=f"incomplete_{key_suffix}",
    )
    opt_intent_mismatch = st.checkbox(
        "c. 與 metadata 的 intent 不對應",
        value=_bool_result(item, "opt_intent_mismatch"),
        key=f"intent_{key_suffix}",
    )
    opt_weird = st.checkbox(
        "d. 其他怪怪的",
        value=_bool_result(item, "opt_weird"),
        key=f"weird_{key_suffix}",
    )

    weird_note = ""
    if opt_weird:
        weird_note = st.text_area(
            "請描述哪裡怪怪的",
            value=_text_result(item, "weird_note"),
            key=f"note_{key_suffix}",
        )

    st.markdown(f'<div class="qc-source">{escape(item.get("utterance_id", ""))}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if prev:
        if go_prev_item(username):
            st.rerun()

    if skip:
        qc_api.skip_item(username, item["utterance_id"])
        st.session_state.qc_progress = None
        st.session_state.qc_item = None
        st.rerun()

    if submit:
        qc_api.submit_result(
            username,
            item,
            {
                "opt_empty": opt_empty,
                "opt_incomplete": opt_incomplete,
                "opt_intent_mismatch": opt_intent_mismatch,
                "opt_weird": opt_weird,
                "weird_note": weird_note,
            },
        )
        st.session_state.qc_progress = None
        st.session_state.qc_item = None
        st.rerun()


def qc_page() -> None:
    inject_css()
    username = st.session_state.get("username", "")

    st.session_state.setdefault("qc_item", None)
    st.session_state.setdefault("qc_progress", None)

    if st.session_state.qc_progress is None:
        with st.spinner("載入資料中…"):
            st.session_state.qc_progress = qc_api.get_progress()

    progress = st.session_state.qc_progress

    st.markdown(f"""
    <div class="qc-top">
      <div>使用者：<b>{escape(username)}</b></div>
      <div>新題 {progress['fresh_left']}｜跳過 {progress['skipped']}｜處理中 {progress['working']}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.qc_item is None:
        with st.spinner("領取題目中…"):
            st.session_state.qc_item = qc_api.get_next_item(username)

    item = st.session_state.qc_item
    if item is None:
        st.success("🎉 目前沒有可分配題目")
        return

    render_item(item, username)

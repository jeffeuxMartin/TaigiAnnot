import streamlit as st
import pandas as pd
import time

def _bool_result(item, column):
    # This function would normally fetch the boolean value from your data source
    return item[column]

def _text_result(item, column):
    # This function would normally fetch the text value from your data source
    return item[column]

def main():
    st.title("Hello, Streamlit!")
    st.write("This is a simple Streamlit app.")


    # A fake df for demonstration
    df = pd.DataFrame({
        "item": ["Item 1", "Item 2", "Item 3"],
        "opt_empty": [True, False, True],
        "opt_incomplete": [False, True, False],
        "opt_intent_mismatch": [False, False, True],
        "opt_weird": [True, False, False],
        "weird_note": ["Note 1", "", ""],  # No data for items without weirdness
    })

    # simulate rendering items according to the time
    idx = time.localtime().tm_sec % len(df)  # Just for demonstration, cycle through items based on seconds
    item = df.iloc[idx]

    render_item(item)

def render_item(item): 
    st.subheader(f"Reviewing: {item['item']}")
    key_suffix = item['item'].replace(" ", "_")  # Create a unique key suffix based on the item name

    with st.form("my_form"):
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


# TODO: save result

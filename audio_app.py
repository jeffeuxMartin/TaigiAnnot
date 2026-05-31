import streamlit as st

url = "https://huggingface.co/datasets/TaigiSpeech/TaigiSpeech/resolve/main/data/test/audio/p002_0001_1_tw.wav"

st.title("HF Audio Test")
st.write(url)
st.audio(url)

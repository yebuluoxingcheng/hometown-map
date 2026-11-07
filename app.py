from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from qa import ask

ROOT = Path(__file__).resolve().parent
MAP_HTML = ROOT / "docs" / "index.html"

st.set_page_config(page_title="我的城市 · 枣庄新城", layout="wide")
st.title("我的城市 · 枣庄新城")
st.caption("P0 v1.2 · 地图 + AI 问答")

if not MAP_HTML.exists():
    st.error("找不到 docs/index.html，先运行：python hometown_map.py")
    st.stop()

components.html(MAP_HTML.read_text(encoding="utf-8"), height=560, scrolling=False)

st.subheader("问问你的城市")
st.caption("比如：我家附近有什么？哪个点离中心最远？")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if question := st.chat_input("输入问题"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("想一下…"):
            answer = ask(question)
        st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

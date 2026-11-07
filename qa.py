"""把地点数据拼成上下文，调用 DeepSeek 回答。"""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

SYSTEM_PROMPT = """你是枣庄新城的生活助手。
只根据下面列出的地点回答；数据里没有的，直接说“我不知道”，不要编。
用户提到的地点如果不在列表里，先说明没有这个地点，再回答能回答的部分。
距离是到几何中心的直线距离，不是步行距离。回答用中文，两三句话。

地点：
{context}
"""


def _api_key() -> str:
    """本地读 .env，Streamlit Cloud 读 st.secrets。"""
    try:
        import streamlit as st

        key = st.secrets.get("DEEPSEEK_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.getenv("DEEPSEEK_API_KEY", "")


def build_context() -> str:
    places = pd.read_csv(ROOT / "places.csv").dropna(subset=["lon", "lat"])
    metrics = pd.read_csv(ROOT / "metrics.csv")
    dist = dict(zip(metrics["name"], metrics["dist_km"]))

    rows = []
    for row in places.itertuples(index=False):
        d = dist.get(row.name)
        suffix = f"，距中心 {d:.1f} km" if d is not None else ""
        rows.append(f"- {row.name}（{row.category}）{suffix}")
    return "\n".join(rows)


def ask(question: str) -> str:
    client = OpenAI(api_key=_api_key(), base_url="https://api.deepseek.com")
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(context=build_context())},
            {"role": "user", "content": question},
        ],
    )
    return resp.choices[0].message.content

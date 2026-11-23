"""P0 的问答限额：防止公开应用被打爆 API 额度。

用法（app.py）：
    from rate_limit import check, consume, remaining
    ok, why = check()      # 只检查，不扣
    ...
    answer = ask(question)
    consume()              # 成功后再扣

规则：
- 每个浏览器会话最多 10 问（刷新页面重置）
- 全站每天最多 200 问（北京时间零点重置）
"""

import datetime
from zoneinfo import ZoneInfo

import streamlit as st

SESSION_LIMIT = 10
DAILY_LIMIT = 200
TZ = ZoneInfo("Asia/Shanghai")


@st.cache_resource
def _daily() -> dict:
    """进程级计数器，跨会话共享，按日期重置。"""
    return {"date": "", "count": 0}


def _today() -> str:
    return datetime.datetime.now(TZ).date().isoformat()


def _reset_if_new_day(daily: dict) -> None:
    today = _today()
    if daily["date"] != today:
        daily["date"] = today
        daily["count"] = 0


def check() -> tuple[bool, str]:
    """放行返回 (True, "")；超限返回 (False, 提示语)。不改变计数。"""
    state = st.session_state
    daily = _daily()
    _reset_if_new_day(daily)

    if state.get("asked", 0) >= SESSION_LIMIT:
        return False, (
            f"这个会话已经问了 {SESSION_LIMIT} 次，刷新页面可以继续。"
            f"全站每天上限 {DAILY_LIMIT} 次。"
        )

    if daily["count"] >= DAILY_LIMIT:
        return False, "今天的问答额度用完了，明天再来。"

    return True, ""


def consume() -> None:
    """API 调用成功后调用，扣一次。"""
    state = st.session_state
    state["asked"] = state.get("asked", 0) + 1

    daily = _daily()
    _reset_if_new_day(daily)
    daily["count"] += 1


def remaining() -> tuple[int, int]:
    """返回 (本会话剩余, 今日全站剩余)，给页面显示用。"""
    daily = _daily()
    _reset_if_new_day(daily)
    asked = st.session_state.get("asked", 0)
    return max(0, SESSION_LIMIT - asked), max(0, DAILY_LIMIT - daily["count"])

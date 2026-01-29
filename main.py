import yfinance as yf
import requests
import pandas as pd
import os  # 👈 新增：用于读取系统环境变量

# --- 配置区 ---
# ⚠️ 关键修改：不再硬编码 Key，而是从 GitHub Secrets 读取
PUSH_KEY = os.getenv("PUSH_KEY")
GOLD_SYMBOL = "GC=F"


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def get_gold_data():
    try:
        gold = yf.Ticker(GOLD_SYMBOL)
        df = gold.history(period="6mo")
        if df.empty: return None

        current = df['Close'].iloc[-1]
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        df['RSI'] = calculate_rsi(df['Close'])
        rsi = df['RSI'].iloc[-1]

        # 简单策略逻辑
        if rsi < 30:
            status = "✅【极度超卖】RSI<30，反弹概率大"
        elif rsi < 40 and current < ma20:
            status = "👀【弱势关注】价格在均线下方"
        elif rsi > 70:
            status = "⚠️【过热预警】RSI>70"
        else:
            status = "☕【行情震荡】观望"

        return f"{status}\n价格: ${current:.2f}\nRSI: {rsi:.2f}"
    except Exception as e:
        return f"运行出错: {e}"


def send_wechat(content):
    if not PUSH_KEY:
        print("❌ 错误：未检测到 PUSH_KEY 环境变量")
        return

    url = "https://api2.pushdeer.com/message/push"
    params = {"pushkey": PUSH_KEY, "text": content}
    try:
        requests.get(url, params=params, timeout=10)
        print("✅ 推送请求已发送")
    except Exception as e:
        print(f"❌ 发送失败: {e}")


if __name__ == "__main__":
    msg = get_gold_data()
    if msg:
        print(msg)
        send_wechat(msg)
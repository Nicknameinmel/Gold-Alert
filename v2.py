import yfinance as yf
import requests
import pandas as pd
import sys

# --- 配置区 ---
# ⚠️ 请务必去 Pushdeer 重置 Key，并填入新的 Key
PUSH_KEY = "PDU38852TT0hoVGHniEpx35dH6DBh9dLDeKKF6HUj"
GOLD_SYMBOL = "GC=F"  # 纽约金期货


def calculate_rsi(series, period=14):
    """
    计算标准 RSI (Wilder's Smoothing)
    """
    delta = series.diff()

    # 获取上涨和下跌的绝对值
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 使用 ewm (Exponential Weighted Moving Average) 模拟 Wilder's Smoothing
    # com = period - 1 是标准 RSI 的参数设定
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    # 处理除以 0 的情况
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def get_gold_data():
    """获取黄金数据并分析"""
    print("正在获取数据...")
    try:
        gold = yf.Ticker(GOLD_SYMBOL)
        # 获取更长的数据以确保 RSI 计算准确 (至少 3-6 个月)
        df = gold.history(period="6mo")

        if df.empty:
            return "❌ 获取数据失败：返回为空"
    except Exception as e:
        return f"❌ 获取数据出错: {e}"

    # 获取当前价格
    current_price = df['Close'].iloc[-1]

    # 计算 MA20
    df['MA20'] = df['Close'].rolling(window=20).mean()
    ma20 = df['MA20'].iloc[-1]

    # 计算标准 RSI
    df['RSI'] = calculate_rsi(df['Close'])
    rsi = df['RSI'].iloc[-1]

    # 简单的趋势判断（可选：比较当前价和前一天价格）
    prev_close = df['Close'].iloc[-2]
    change_pct = ((current_price - prev_close) / prev_close) * 100

    # 组装基础信息
    msg = (f"当前金价: ${current_price:.2f} ({change_pct:+.2f}%)\n"
           f"MA20均线: ${ma20:.2f}\n"
           f"RSI (14): {rsi:.2f}\n")

    # 策略逻辑
    if rsi < 30:  # 严格超卖通常看30，激进看40
        status = "✅【极度超卖】RSI低于30，存在反弹可能。"
    elif rsi < 40 and current_price < ma20:
        status = "👀【弱势关注】价格低于均线且RSI较低，留意企稳信号。"
    elif rsi > 70:
        status = "⚠️【过热预警】RSI超买(>70)，注意回调风险。"
    else:
        status = "☕【行情震荡】无极端信号，建议观望。"

    return f"黄金行情提醒：\n{status}\n----------------\n{msg}"


def send_wechat(content):
    """发送推送至微信/Pushdeer App"""
    # 基础 URL
    base_url = "https://api2.pushdeer.com/message/push"

    # 使用 params 字典，requests 库会自动处理 URL 编码（换行、表情等）
    params = {
        "pushkey": PUSH_KEY,
        "text": content,
        "type": "markdown"  # 如果 Pushdeer 支持 markdown 格式更好
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            # 检查 API 返回的内容是否真的成功
            res_json = response.json()
            if res_json.get("code") == 0:
                print("✅ 推送成功！")
            else:
                print(f"❌ 推送接口报错: {res_json}")
        else:
            print(f"❌ 推送网络请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 发送过程出错: {e}")


if __name__ == "__main__":
    if "PDU38852" in PUSH_KEY:
        print("⛔ 警告：请先修改 PUSH_KEY 为你自己的新 Key，不要使用泄露的旧 Key！")
    else:
        message = get_gold_data()
        print(f"准备发送内容：\n{message}")  # 本地先打印看看
        send_wechat(message)
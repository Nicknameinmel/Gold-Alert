import yfinance as yf
import requests

# --- 配置区 ---
PUSH_KEY = "PDU38852TT0hoVGHniEpx35dH6DBh9dLDeKKF6HUj"  # 填入你申请的 Key
GOLD_SYMBOL = "GC=F"  # 纽约金期货（美元）


def get_gold_data():
    """获取黄金数据并分析"""
    gold = yf.Ticker(GOLD_SYMBOL)
    df = gold.history(period="30d")

    current_price = df['Close'].iloc[-1]
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]

    # 计算 RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]

    # 回撤判断逻辑
    msg = f"当前金价: ${current_price:.2f}\nRSI: {rsi:.2f}\n"

    if rsi < 40 and current_price < ma20:
        status = "✅【回撤买入信号】金价已进入超卖区间，建议关注！"
    elif rsi > 70:
        status = "❌【过热预警】RSI极高，请勿盲目追涨。"
    else:
        status = "💡【行情震荡】目前无极端信号，适合持仓观望。"

    return f"黄金提醒：\n{status}\n{msg}"


def send_wechat(content):
    """发送推送至微信/Pushdeer App"""
    url = f"https://api2.pushdeer.com/message/push?pushkey={PUSH_KEY}&text={content}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("推送成功！")
        else:
            print("推送失败。")
    except Exception as e:
        print(f"发送出错: {e}")


if __name__ == "__main__":
    message = get_gold_data()
    send_wechat(message)
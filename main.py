import yfinance as yf
import requests
import pandas as pd
import os

# --- 配置区 ---
PUSH_KEY = os.getenv("PUSH_KEY") 
GOLD_SYMBOL = "GC=F"       # 黄金期货
DXY_SYMBOL = "DX-Y.NYB"    # 美元指数

def get_data_and_analyze():
    try:
        # 1. 获取黄金数据 (多取一点数据以计算 MA)
        gold = yf.Ticker(GOLD_SYMBOL)
        df_gold = gold.history(period="1mo")
        
        # 2. 获取美元指数数据
        dxy = yf.Ticker(DXY_SYMBOL)
        df_dxy = dxy.history(period="5d")

        if df_gold.empty or df_dxy.empty:
            return "❌ 数据获取失败，请检查网络或代码。"

        # --- 黄金指标计算 ---
        current_price = df_gold['Close'].iloc[-1]
        prev_close = df_gold['Close'].iloc[-2]
        
        # A. 计算 MA5
        ma5 = df_gold['Close'].rolling(window=5).mean().iloc[-1]
        
        # B. 判断连续阴线 (今天跌，昨天也跌)
        # 逻辑：今天收盘 < 昨天收盘 AND 昨天收盘 < 前天收盘
        is_drop_today = df_gold['Close'].iloc[-1] < df_gold['Close'].iloc[-2]
        is_drop_yesterday = df_gold['Close'].iloc[-2] < df_gold['Close'].iloc[-3]
        consecutive_drop = is_drop_today and is_drop_yesterday # 连续2日下跌

        # C. 判断是否跌破 MA5
        below_ma5 = current_price < ma5

        # --- 美元指标计算 ---
        # D. 美元反抽 (简单判断：美元指数今日上涨)
        dxy_current = df_dxy['Close'].iloc[-1]
        dxy_prev = df_dxy['Close'].iloc[-2]
        dxy_change = ((dxy_current - dxy_prev) / dxy_prev) * 100
        dxy_rebound = dxy_change > 0  # 美元在涨

        # --- 策略判定 ---
        # 核心条件：连续2阴 + 跌破MA5 + 美元涨
        signal_triggered = consecutive_drop and below_ma5 and dxy_rebound

        # --- 组装消息 ---
        status_icon = "✅" if signal_triggered else "⏸️"
        title = "【回撤确认】满足条件" if signal_triggered else "【观察中】未满足所有条件"

        msg = (
            f"{title}\n"
            f"----------------\n"
            f"💰 黄金价格: ${current_price:.2f}\n"
            f"📉 连跌两天: {'是' if consecutive_drop else '否'}\n"
            f"〰️ 跌破MA5: {'是' if below_ma5 else '否'} (${ma5:.1f})\n"
            f"----------------\n"
            f"💵 美元指数: {dxy_current:.2f}\n"
            f"📈 美元反抽: {'是' if dxy_rebound else '否'} ({dxy_change:+.2f}%)\n"
        )
        
        # 如果触发信号，额外加一句建议
        if signal_triggered:
            msg += "\n💡 提示：短线空头趋势共振，注意风险！"

        return f"{status_icon} 黄金策略更新\n{msg}"

    except Exception as e:
        return f"❌ 运行出错: {str(e)}"

def send_wechat(content):
    if not PUSH_KEY:
        print("❌ 未检测到 PUSH_KEY")
        return
    
    url = "https://api2.pushdeer.com/message/push"
    # 使用 markdown 类型可以让格式更好看
    params = {"pushkey": PUSH_KEY, "text": content, "type": "markdown"}
    
    try:
        requests.get(url, params=params, timeout=10)
        print("✅ 推送请求已发送")
    except Exception as e:
        print(f"❌ 发送失败: {e}")

if __name__ == "__main__":
    message = get_data_and_analyze()
    print(message)
    send_wechat(message)

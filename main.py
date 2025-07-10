import requests
import datetime
import json
import os

WEBHOOK = os.getenv("WEBHOOK")  # 从 GitHub Secrets 获取

def fetch_pump_tokens():
    url = "https://pump.fun/api/projects?sort=hot"
    res = requests.get(url).json()
    return res

def filter_tokens(tokens):
    now = datetime.datetime.utcnow()
    threshold = now.timestamp() - 12 * 3600
    result = []
    for token in tokens:
        if token.get("fdv", 0) >= 1_000_000:
            created = token.get("createdEpochSeconds", 0)
            if created >= threshold:
                result.append(token)
    return result

def get_top100_change(ca):
    return "+7.3%"  # 模拟数据

def build_message(tokens):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"📢 新币播报（截至 {now}）\n\n"
    for i, token in enumerate(tokens[:5]):
        name = token.get("name", "未知")
        price = token.get("price", 0)
        fdv = token.get("fdv", 0)
        volume = token.get("volume", 0)
        ca = token.get("publicKey", "N/A")
        link = f"https://pump.fun/{ca}"
        top100 = get_top100_change(ca)
        text += (
            f"{i+1}️⃣【${name}】\n"
            f"🔗 {link}\n"
            f"💰 价格：{price:.6f} SOL\n"
            f"📈 市值：${int(fdv):,}\n"
            f"💵 交易量：${int(volume):,}\n"
            f"📦 CA地址：{ca[:5]}...{ca[-4:]}\n"
            f"👥 Top 100 钱包变化：{top100}\n\n"
        )
    return text

def send_wechat(text):
    if not WEBHOOK:
        print("❌ 没有设置 WEBHOOK")
        return
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "text", "text": {"content": text}}
    res = requests.post(WEBHOOK, headers=headers, data=json.dumps(data))
    print("状态码:", res.status_code)
    print("返回信息:", res.text)

if __name__ == "__main__":
    tokens = fetch_pump_tokens()
    filtered = filter_tokens(tokens)
    msg = build_message(filtered) if filtered else "⚠️ 过去12小时无市值破百万的新币。"
    send_wechat(msg)

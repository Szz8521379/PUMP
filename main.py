import os
import requests
from datetime import datetime, timedelta

# 从环境变量读取企业微信机器人Webhook地址
WEBHOOK = os.environ.get("WEBHOOK_NEWCOINS")

if not WEBHOOK:
    print("curl "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=ec4b5f2c-caf5-4c68-ab3c-1c5d2d76b2ed" `
  -H "Content-Type: application/json" `
  -Body '{"msgtype":"text","text":{"content":"🔔 测试推送成功！来自 curl"}}' `
  -Method POST
")
    exit(1)

def send_to_wechat(content: str):
    """推送消息到企业微信"""
    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }
    try:
        res = requests.post(WEBHOOK, json=payload)
        print("推送状态码:", res.status_code)
        print("推送返回内容:", res.text)
    except Exception as e:
        print("推送失败:", e)

def fetch_pump_tokens():
    """示例：从pump.fun获取市值≥1M的新币"""
    url = "https://pump.fun/api/trending"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        tokens = []
        for token in data:
            market_cap = token.get("marketCap", 0)
            if market_cap >= 1_000_000:
                tokens.append({
                    "name": token.get("name"),
                    "symbol": token.get("symbol"),
                    "market_cap": market_cap,
                    "volume": token.get("volume", 0),
                    "address": token.get("tokenAddress"),
                    "url": f"https://pump.fun/{token.get('tokenAddress')}"
                })
        return tokens
    except Exception as e:
        print("获取 pump 数据失败:", e)
        return []

def fetch_dex_tokens():
    """示例：从 DexScreener 获取24小时内上线且市值≥1M的币"""
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"
    try:
        res = requests.get(url, timeout=10)
        pairs = res.json().get("pairs", [])
        now = datetime.utcnow()
        threshold_time = now - timedelta(hours=24)
        tokens = []
        for pair in pairs:
            if not pair.get("pairCreatedAt"): 
                continue
            try:
                created = datetime.fromisoformat(pair["pairCreatedAt"].replace("Z", "+00:00"))
            except: 
                continue
            if created < threshold_time: 
                continue
            mcap = float(pair.get("fdv", 0) or 0)
            if mcap >= 1_000_000:
                tokens.append({
                    "name": pair.get("baseToken", {}).get("name"),
                    "symbol": pair.get("baseToken", {}).get("symbol"),
                    "market_cap": mcap,
                    "volume": pair.get("volume", {}).get("h24", 0),
                    "address": pair.get("pairAddress"),
                    "url": pair.get("url")
                })
        return tokens
    except Exception as e:
        print("获取 dex 数据失败:", e)
        return []

def format_tokens(title, tokens):
    if not tokens:
        return f"🔹【{title}】\n暂无符合条件的新币\n\n"
    msg = f"🔹【{title}】\n"
    for token in tokens[:5]:
        msg += f"🚀 {token['symbol']} | 💰市值: {int(token['market_cap']/1e6)}M | 📈交易量: {int(token['volume'])}\n"
        msg += f"🔗链接: {token['url']}\n\n"
    return msg

def main():
    pump_tokens = fetch_pump_tokens()
    dex_tokens = fetch_dex_tokens()

    msg = "📊【新币推送】过去24小时市值突破1M USDT\n\n"
    msg += format_tokens("Pump 平台", pump_tokens)
    msg += format_tokens("DexScreener 平台", dex_tokens)

    send_to_wechat(msg)

if __name__ == "__main__":
    main()

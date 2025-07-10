import os
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time

WEBHOOK = os.environ.get("WEBHOOK_NEWCOINS")

def send_to_wechat(content: str):
    if not WEBHOOK:
        print("❌ Webhook 地址未设置")
        return
    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }
    try:
        res = requests.post(WEBHOOK, json=payload)
        print("✅ 推送状态码:", res.status_code)
        print("📨 返回:", res.text)
    except Exception as e:
        print("推送失败:", e)

def fetch_alva_description(symbol_or_address):
    """通过 Alva 搜索简介"""
    url = f"https://alva.xyz/zh-CN/search?q={symbol_or_address}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        desc = soup.find("div", class_="text-sm text-muted")
        if desc:
            return desc.get_text().strip()
    except Exception as e:
        print(f"Alva 查询失败: {e}")
    return "暂无简介"

def fetch_pump_tokens():
    url = "https://pump.fun/board"
    try:
        res = requests.get(url, timeout=10)
        data = res.json().get("tokens", [])
        result = []
        for token in data:
            market_cap = token.get("marketCap", 0)
            if market_cap >= 1_000_000:
                result.append({
                    "symbol": token.get("symbol"),
                    "name": token.get("name"),
                    "market_cap": market_cap,
                    "url": f"https://pump.fun/{token.get('id')}",
                    "alva_key": token.get("symbol")
                })
        return result
    except Exception as e:
        print("❌ 获取 pump 数据失败:", e)
        return []

def fetch_dex_tokens():
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"
    try:
        res = requests.get(url, timeout=10)
        pairs = res.json().get("pairs", [])
        now = datetime.utcnow()
        threshold = now - timedelta(hours=24)
        result = []
        for pair in pairs:
            mcap = float(pair.get("fdv") or 0)
            created = pair.get("pairCreatedAt")
            if not created:
                continue
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except:
                continue
            if mcap >= 1_000_000 and created_dt >= threshold:
                result.append({
                    "symbol": pair["baseToken"]["symbol"],
                    "name": pair["baseToken"]["name"],
                    "market_cap": mcap,
                    "url": pair["url"],
                    "alva_key": pair["pairAddress"]
                })
        return result
    except Exception as e:
        print("❌ 获取 dex 数据失败:", e)
        return []

def format_tokens(title, tokens):
    if not tokens:
        return f"🔹【{title}】暂无新币符合条件\n"
    msg = f"🔹【{title}】\n"
    for token in tokens[:5]:
        desc = fetch_alva_description(token['alva_key'])
        msg += f"🚀 {token['symbol']} | 💰市值: {int(token['market_cap']/1e6)}M\n"
        msg += f"📄 简介：{desc[:80]}...\n"  # 简介太长则截断
        msg += f"🔗链接: {token['url']}\n\n"
        time.sleep(1.5)  # 加个延迟，防止访问太频繁被 Alva 封
    return msg

def main():
    msg = "📊【新币追踪】24小时市值突破 1M USDT 的代币\n\n"
    msg += format_tokens("Pump 平台", fetch_pump_tokens())
    msg += format_tokens("DexScreener", fetch_dex_tokens())
    send_to_wechat(msg)

if __name__ == "__main__":
    main()

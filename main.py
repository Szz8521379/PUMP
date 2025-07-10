import requests
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("WEBHOOK_NEWCOINS")
HEADERS = {"User-Agent": "Mozilla/5.0"}
NEW_COIN_HOURS = 24

def get_alva_description(symbol):
    try:
        url = f"https://alva.xyz/zh-CN/search?q={symbol}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        desc_tag = soup.find("p", class_="text-muted")
        return desc_tag.text.strip() if desc_tag else "暂无简介"
    except Exception as e:
        print(f"Alva简介获取异常: {e}")
        return "简介获取失败"

def get_pump_coins():
    url = "https://pump.fun/api/coins/recent"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        now = datetime.utcnow()
        coins = []
        for c in data:
            mc = c.get("marketCapUsd", 0)
            launch_ts = c.get("launchTime")
            if launch_ts:
                launch_time = datetime.utcfromtimestamp(launch_ts)
                if now - launch_time > timedelta(hours=NEW_COIN_HOURS):
                    continue
            if mc and mc >= 1_000_000:
                coins.append({
                    "platform": "pump.fun",
                    "name": c.get("name"),
                    "symbol": c.get("symbol"),
                    "market_cap": mc,
                    "volume": c.get("volume", 0),
                    "ca": c.get("address")
                })
        return coins
    except Exception as e:
        print(f"获取 pump.fun 异常: {e}")
        return []

def get_dexscreener_coins():
    url = "https://api.dexscreener.com/latest/dex/pairs"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        pairs = r.json().get("pairs", [])
        dex_symbols = set()
        dex_contracts = set()
        for p in pairs:
            symbol = p.get("baseToken", {}).get("symbol")
            ca = p.get("pairAddress")
            if symbol:
                dex_symbols.add(symbol)
            if ca:
                dex_contracts.add(ca.lower())
        return dex_symbols, dex_contracts
    except Exception as e:
        print(f"获取 dexscreener 异常: {e}")
        return set(), set()

def format_coin(c):
    desc = get_alva_description(c["symbol"])
    return (
        f"平台: {c['platform']}\n"
        f"名称: {c['name']} ({c['symbol']})\n"
        f"市值: ${c['market_cap']:,}\n"
        f"交易量: ${c['volume']:,}\n"
        f"合约地址: {c['ca']}\n"
        f"简介: {desc}\n"
        "-------------------------"
    )

def send_wechat(text):
    if not WEBHOOK:
        print("❌ 未设置 WEBHOOK_NEWCOINS 环境变量")
        return False
    payload = {"msgtype": "text", "text": {"content": text}}
    try:
        resp = requests.post(WEBHOOK, json=payload, timeout=10)
        print(f"推送状态码: {resp.status_code}")
        print(f"推送返回内容: {resp.text}")
        return resp.status_code == 200
    except Exception as e:
        print(f"推送异常: {e}")
        return False

def main():
    print("开始抓取pump.fun数据...")
    pump_coins = get_pump_coins()
    print(f"抓取到pump.fun币数: {len(pump_coins)}")

    print("开始抓取DexScreener数据...")
    dex_symbols, dex_contracts = get_dexscreener_coins()
    print(f"DexScreener币种数量: {len(dex_symbols)}")

    filtered_coins = []
    for c in pump_coins:
        ca = c.get("ca", "").lower()
        sym = c.get("symbol")
        if ca in dex_contracts or sym in dex_symbols:
            filtered_coins.append(c)
    print(f"筛选后符合条件币数: {len(filtered_coins)}")

    if not filtered_coins:
        send_wechat("今日无符合pump发射且已上DexScreener的新币，市值≥1M。")
        return

    content = "📢【今日pump发射且上DexScreener新币播报】\n\n" + "\n\n".join(format_coin(c) for c in filtered_coins)
    success = send_wechat(content)
    if not success:
        print("推送微信失败，请检查Webhook和网络")

if __name__ == "__main__":
    main()

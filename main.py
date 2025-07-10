import requests
from bs4 import BeautifulSoup
import datetime
import os

WEBHOOK = os.getenv("WEBHOOK_NEWCOINS")  # 企业微信机器人地址

def fetch_pump_tokens():
    try:
        res = requests.get("https://pump.fun/api/projects?sort=hot", timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Pump.fun抓取失败: {e}")
        return []

def fetch_dexscreener_tokens():
    try:
        res = requests.get("https://api.dexscreener.com/latest/dex/tokens", timeout=10)
        res.raise_for_status()
        return res.json().get("tokens", [])
    except Exception as e:
        print(f"DexScreener抓取失败: {e}")
        return []

def normalize_tokens():
    all_tokens = []
    now = datetime.datetime.utcnow().timestamp()
    threshold = now - 12*3600

    # Pump.fun
    for t in fetch_pump_tokens():
        fdv = t.get("fdv", 0)
        created = t.get("createdEpochSeconds", 0)
        if fdv >= 1_000_000 and created >= threshold:
            all_tokens.append({
                "name": t.get("name") or "匿名",
                "ca": t.get("publicKey"),
                "price": t.get("price"),
                "fdv": fdv,
                "volume": t.get("volume"),
                "link": f"https://pump.fun/{t.get('publicKey')}"
            })

    # DexScreener
    for t in fetch_dexscreener_tokens():
        fdv = t.get("marketCapUsd", 0)
        listed = t.get("listedAt", 0)
        if fdv >= 1_000_000 and listed >= threshold:
            all_tokens.append({
                "name": t.get("name") or "匿名",
                "ca": t.get("address"),
                "price": t.get("priceUsd"),
                "fdv": fdv,
                "volume": t.get("volumeUsd"),
                "link": t.get("url")
            })

    # 按市值排序最高10条
    return sorted(all_tokens, key=lambda x: x["fdv"], reverse=True)[:10]

def fetch_alva_data(ca):
    url = f"https://alva.xyz/zh-CN/token/{ca}"
    try:
        res = requests.get(url, {"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        desc = "暂无简介"
        tag = soup.find("div", string=lambda s: s and "简介" in s)
        if tag:
            sib = tag.find_next_sibling("div")
            if sib: desc = sib.get_text(strip=True)

        heat = next((div.get_text(strip=True)
                     for div in soup.find_all("div")
                     if any(k in div.get_text() for k in ["点赞", "讨论", "评论"])), "暂无数据")

        v_list = "、".join([a.get_text(strip=True)
                             for a in soup.find_all("a")
                             if "@" in a.get_text()][:3]) or "未知"

        return desc, heat, v_list
    except Exception:
        return "简介抓取失败", "热度无", "大V未知"

def build_message(tokens):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"📢 Still Ballin（截至 {now}）\n\n"
    for i, t in enumerate(tokens, 1):
        desc, heat, v_list = fetch_alva_data(t["ca"])
        text += (
            f"{i}️⃣\n"
            f"🔗 {t['link']}\n"
            f"💰 价格：{t['price']}\n"
            f"📈 市值：${int(t['fdv']):,}\n"
            f"💵 交易量：${int(t['volume']):,}\n"
            f"📦 合约地址：{t['ca'][:5]}...{t['ca'][-4:]}\n"
            f"📝 简介：{desc}\n"
            f"🔥 讨论热度：{heat}\n"
            f"🧠 参与大V：{v_list}\n\n"
        )
    return text

def send_wechat(text):
    if not WEBHOOK:
        print("未设置 WEBHOOK_NEWCOINS")
        return
    res = requests.post(WEBHOOK, json={"msgtype": "text", "text": {"content": text}})
    print("微信推送状态：", res.status_code, res.text)

def main():
    tokens = normalize_tokens()
    if tokens:
        send_wechat(build_message(tokens))
    else:
        print("暂无符合条件币种")

if __name__ == "__main__":
    main()

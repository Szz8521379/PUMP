import os
import json
import requests
from datetime import datetime

WEBHOOK = os.environ.get("WEBHOOK_NEWCOINS")
DATA_FILE = "last_volumes.json"

def send_to_wechat(content: str):
    if not WEBHOOK:
        print("Webhook未设置")
        return
    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }
    try:
        res = requests.post(WEBHOOK, json=payload)
        print("推送状态码:", res.status_code)
        print("返回内容:", res.text)
    except Exception as e:
        print("推送失败:", e)

def load_last_volumes():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_last_volumes(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def fetch_dexscreener_data():
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        return data.get("pairs", [])
    except Exception as e:
        print("获取DexScreener数据失败:", e)
        return []

def analyze_volume_spike(pairs, last_volumes):
    abnormal = []
    updated_volumes = {}
    for pair in pairs:
        pair_addr = pair.get("pairAddress")
        vol_24h = pair.get("volume", {}).get("h24", 0)
        if pair_addr is None or vol_24h is None:
            continue
        last_vol = last_volumes.get(pair_addr, 0)
        # 首次没有数据直接保存，不报警
        if last_vol == 0:
            updated_volumes[pair_addr] = vol_24h
            continue
        ratio = vol_24h / last_vol if last_vol else 0
        increase_pct = (vol_24h - last_vol) / last_vol if last_vol else 0

        # 满足放大5倍且涨幅50%以上
        if ratio >= 5 and increase_pct >= 0.5:
            abnormal.append({
                "symbol": pair.get("baseToken", {}).get("symbol", "未知"),
                "name": pair.get("baseToken", {}).get("name", "未知"),
                "pairAddress": pair_addr,
                "old_volume": last_vol,
                "new_volume": vol_24h,
                "ratio": ratio,
                "url": pair.get("url", "")
            })
        updated_volumes[pair_addr] = vol_24h
    return abnormal, updated_volumes

def main():
    last_volumes = load_last_volumes()
    pairs = fetch_dexscreener_data()
    spikes, updated_volumes = analyze_volume_spike(pairs, last_volumes)
    save_last_volumes(updated_volumes)

    if not spikes:
        print(f"{datetime.utcnow()} - 无异常交易量放大")
        return

    msg = "【DexScreener 老币交易量异常监控】发现以下币种交易量放大：\n\n"
    for t in spikes:
        msg += (f"🚨 {t['symbol']} ({t['name']})\n"
                f"交易量从 {int(t['old_volume'])} 增长到 {int(t['new_volume'])}，放大 {t['ratio']:.2f} 倍\n"
                f"交易对链接: {t['url']}\n\n")
    send_to_wechat(msg)

if __name__ == "__main__":
    main()

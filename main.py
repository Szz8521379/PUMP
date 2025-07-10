import os
import json
import requests
from datetime import datetime, timedelta

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
    ten_days_ago = datetime.utcnow() - timedelta(days=10)

    for pair in pairs:
        pair_addr = pair.get("pairAddress")
        vol_15min = pair.get("volume", {}).get("m15", 0)  # 15分钟交易量
        price_change_15min = pair.get("priceChange", {}).get("m15", 0)  # 15分钟价格涨幅
        pair_created_at = pair.get("pairCreatedAt")  # 交易对创建时间（毫秒）

        if pair_addr is None or vol_15min is None or price_change_15min is None or pair_created_at is None:
            continue

        # 转换为 datetime 检查年龄
        pair_created_time = datetime.fromtimestamp(pair_created_at / 1000)
        age_days = (datetime.utcnow() - pair_created_time).days

        last_vol = last_volumes.get(pair_addr, 0)
        # 首次没有数据直接保存，不报警
        if last_vol == 0:
            updated_volumes[pair_addr] = vol_15min
            continue

        ratio = vol_15min / last_vol if last_vol else 0

        # 筛选：年龄≥10天，交易量放大≥5倍，价格涨幅≥50%
        if age_days >= 10 and ratio >= 5 and price_change_15min >= 50:
            abnormal.append({
                "symbol": pair.get("baseToken", {}).get("symbol", "未知"),
                "name": pair.get("baseToken", {}).get("name", "未知"),
                "pairAddress": pair_addr,
                "old_volume": last_vol,
                "new_volume": vol_15min,
                "price_change": price_change_15min,
                "ratio": ratio,
                "url": pair.get("url", "")
            })
        updated_volumes[pair_addr] = vol_15min

    return abnormal, updated_volumes

def main():
    last_volumes = load_last_volumes()
    pairs = fetch_dexscreener_data()
    spikes, updated_volumes = analyze_volume_spike(pairs, last_volumes)
    save_last_volumes(updated_volumes)

    if not spikes:
        print(f"{datetime.utcnow()} - 无异常交易量放大")
        return

    msg = "【DexScreener 老币监控】发现以下币种异常：\n\n"
    for t in spikes:
        msg += (f"🚨 {t['symbol']} ({t['name']})\n"
                f"15分钟交易量从 ${int(t['old_volume'])} 增长到 ${int(t['new_volume'])}，放大 {t['ratio']:.2f} 倍\n"
                f"15分钟价格涨幅: {t['price_change']:.2f}%\n"
                f"交易对链接: {t['url']}\n"
                f"请自行研究（DYOR）！\n\n")
    send_to_wechat(msg)

if __name__ == "__main__":
    main()

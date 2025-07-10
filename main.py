import os
import requests
import json

# 读取 GitHub Secrets 中配置的 webhook 地址
webhook = os.getenv("WEBHOOK_NEWCOINS")

if not webhook:
    print("❌ 没有获取到 webhook 地址，请检查 GitHub Secrets 是否设置了 WEBHOOK_NEWCOINS")
else:
    message = {
        "msgtype": "text",
        "text": {
            "content": "✅【测试成功】GitHub Actions 成功触发微信推送，请查看企业微信群 💬"
        }
    }

    print("📡 开始推送微信消息...")
    try:
        response = requests.post(
            webhook,
            headers={"Content-Type": "application/json"},
            data=json.dumps(message)
        )
        print("📬 状态码:", response.status_code)
        print("📬 返回内容:", response.text)
        if response.status_code == 200:
            print("✅ 推送成功，请查看微信群 👀")
        else:
            print("❌ 推送失败，可能 webhook 有误或消息格式出错")
    except Exception as e:
        print("❌ 发送消息时出错:", e)

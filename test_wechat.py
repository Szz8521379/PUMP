import os
import requests
import json

def test_wechat_webhook():
    webhook = os.getenv('WEBHOOK_NEWCOINS')
    if not webhook:
        print("错误：环境变量 WEBHOOK_NEWCOINS 未配置！")
        return

    print("当前使用的微信 webhook 地址是：", webhook)

    data = {
        "msgtype": "text",
        "text": {
            "content": "【测试消息】这是自动发送的微信机器人测试消息。"
        }
    }

    try:
        response = requests.post(webhook, data=json.dumps(data), headers={"Content-Type": "application/json"})
        print("微信推送状态码：", response.status_code)
        print("微信接口返回内容：", response.text)
        if response.status_code == 200:
            print("测试消息发送成功！")
        else:
            print("测试消息发送失败！请检查 webhook 是否正确。")
    except Exception as e:
        print("发送测试消息时出错：", e)

if __name__ == "__main__":
    test_wechat_webhook()

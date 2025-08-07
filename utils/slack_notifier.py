
import yaml
import requests

def send_to_slack(summary, report_path):
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    webhook = config.get("slack_webhook")
    if not webhook:
        return
    message = {
        "text": f"*投资研究周报*\n摘要：{summary}\n📄 本地报告: `{report_path}`"
    }
    requests.post(webhook, json=message)

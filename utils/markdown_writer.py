
import datetime
import os

def write_markdown_report(news, analysis, prices, sectors, macro):
    today = datetime.date.today().isoformat()
    os.makedirs("reports", exist_ok=True)
    path = f"reports/report_{today}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 📊 投资研究周报 ({today})\n\n")
        f.write("## 🔥 热点新闻与分析\n")
        for r in analysis:
            f.write(f"### {r['title']}\n{r['analysis']}\n\n")

        f.write("## 📈 股票价格\n\n")
        f.write("| 股票代码 | 最新价格（USD） |\n|---|---|\n")
        for t, p in prices.items():
            f.write(f"| {t} | ${p:.2f} |\n")

        f.write("\n## 🏭 行业表现\n\n")
        f.write("| 行业 | 1日变化 | 5日变化 |\n|---|---|---|\n")
        for s in sectors["sectors"]:
            f.write(f"| {s['sector']} | {s['1D Change']} | {s['5D Change']} |\n")

        f.write("\n## 🧮 宏观经济指标\n\n")
        f.write("| 指标 | 最新 | 前值 | 单位 |\n|---|---|---|---|\n")
        for i in macro["macro_indicators"]:
            f.write(f"| {i['name']} | {i['latest']} | {i['previous']} | {i['unit']} |\n")

    return path, "本周重点：请关注宏观变化与科技板块机会。"

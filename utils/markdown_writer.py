
import datetime
from config import REPORTS_DIR

def write_markdown_report(news, analysis, prices, sectors, macro):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    date_display = now.strftime("%Y-%m-%d %H:%M")
    path = REPORTS_DIR / f"report_{timestamp}.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# 📊 投资研究周报 ({date_display})\n\n")
        f.write("## 🔥 热点新闻与分析\n")
        for r in analysis:
            summary = r.get('summary', '无分析内容')
            sentiment = r.get('sentiment', '未知')
            stocks = r.get('stocks', [])
            industry_themes = r.get('industry_themes', [])
            
            f.write(f"### {r['title']}\n")
            f.write(f"**情绪**: {sentiment}\n\n")
            f.write(f"**行业主题**: {', '.join(industry_themes) if industry_themes else '无'}\n\n")
            # 构建股票信息字符串
            stock_info = []
            for s in stocks:
                company_name = s.get('company_name', '')
                stock_code = s.get('stock_code', '')
                if company_name and stock_code:
                    stock_info.append(f"{company_name}({stock_code})")
            
            f.write(f"**相关股票**: {', '.join(stock_info) if stock_info else '无'}\n\n")
            f.write(f"**总结**: {summary}\n\n")

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

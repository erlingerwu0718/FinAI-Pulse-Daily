import feedparser
import json
import datetime
import pytz
import os

# 设置时区为北京时间
beijing_tz = pytz.timezone('Asia/Shanghai')

def fetch_data():
    items = []
    # 1. 获取 ArXiv 论文 (实际数据)
    print("Fetching ArXiv...")
    try:
        # 搜索 Finance + AI
        feed = feedparser.parse("http://export.arxiv.org/api/query?search_query=all:finance+AND+all:artificial+intelligence&start=0&max_results=5&sortBy=submittedDate&sortOrder=descending")
        for entry in feed.entries:
            items.append({
                "id": entry.id,
                "source": "ArXiv",
                "type": "paper",
                "title": entry.title.replace("\n", " "),
                "time": entry.published[:10],
                "link": entry.link,
                "tags": ["Research"],
                "summary": entry.summary[:200] + "...",
                "ai_analysis": "（自动抓取）最新学术论文，建议阅读原文。",
                "sentiment": "学术"
            })
    except Exception as e:
        print(f"Error fetching ArXiv: {e}")

    # 2. 你可以在这里添加更多 RSS 源 (如 News)
    
    # 3. 添加更新时间戳作为一条特殊数据，或者只更新页面头部
    return items

def generate_html():
    # 获取数据
    data = fetch_data()
    json_str = json.dumps(data, ensure_ascii=False)
    
    # 获取当前时间
    now = datetime.datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M")
    
    # 读取模板
    with open("template.html", "r", encoding="utf-8") as f:
        template = f.read()
    
    # 替换数据
    # 1. 替换列表数据
    output = template.replace("{{ITEMS_DATA}}", json_str)
    # 2. 替换页面上的“最后更新时间” (假设前端代码里有 <span x-text="lastUpdated"></span>)
    # 我们直接修改 JS 里的初始值
    output = output.replace("lastUpdated: '2025-11-19 14:00'", f"lastUpdated: '{now}'")
    
    # 生成最终文件
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(output)
    print(f"Site updated at {now}")

if __name__ == "__main__":
    generate_html()

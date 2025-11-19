import feedparser
import json
import datetime
import pytz
import re

# 设置北京时间
tz = pytz.timezone('Asia/Shanghai')

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext[:200] + "..."

def fetch_data():
    items = []
    current_year = datetime.datetime.now().year
    
    # --- 1. 抓取 Google News (AI Finance) ---
    print("正在抓取 Google News...")
    try:
        # 使用 Google News RSS，搜索 "AI in Finance"，限制为过去24小时 (when:1d)
        news_url = "https://news.google.com/rss/search?q=AI+in+Finance+when:1d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(news_url)
        
        for entry in feed.entries[:10]: # 取前10条
            # 简单的日期过滤，防止未来日期，默认今天
            pub_date = datetime.datetime.now().strftime("%Y-%m-%d")
            if 'published' in entry:
                # 这里简化处理，直接用抓取日期，因为RSS格式各异
                pass 
            
            items.append({
                "id": entry.link,
                "source": "News",
                "title": entry.title,
                "time": pub_date,
                "link": entry.link,
                "summary": clean_html(entry.summary) if 'summary' in entry else entry.title,
            })
    except Exception as e:
        print(f"News Error: {e}")

    # --- 2. 抓取 ArXiv (AI + Finance) ---
    print("正在抓取 ArXiv...")
    try:
        # 按提交日期排序，最新的在最前
        arxiv_url = "http://export.arxiv.org/api/query?search_query=all:finance+AND+all:artificial+intelligence&sortBy=submittedDate&sortOrder=descending&max_results=5"
        feed = feedparser.parse(arxiv_url)
        
        for entry in feed.entries:
            # ArXiv 的日期格式通常是 2025-11-19T...
            pub_date = entry.published[:10]
            
            # 过滤掉未来的日期（如果有）
            if int(pub_date[:4]) > current_year + 1:
                continue

            items.append({
                "id": entry.id,
                "source": "Paper",
                "title": entry.title.replace("\n", " "),
                "time": pub_date,
                "link": entry.link,
                "summary": entry.summary[:300] + "...",
            })
    except Exception as e:
        print(f"ArXiv Error: {e}")
    
    return items

def generate_html():
    # 1. 获取真实数据
    data = fetch_data()
    
    # 如果没有抓到数据，放入一条提示
    if not data:
        data = [{
            "id": "0", "source": "News", "title": "暂无最新更新", 
            "time": datetime.datetime.now().strftime("%Y-%m-%d"), 
            "link": "#", "summary": "请检查网络或等待下次更新。"
        }]

    json_str = json.dumps(data, ensure_ascii=False)
    
    # 2. 获取当前时间
    now_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    
    # 3. 读取模板
    try:
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
    except FileNotFoundError:
        print("错误：找不到 template.html")
        return

    # 4. 替换数据
    # 替换 {{ITEMS_DATA}} 为 JSON 字符串
    output = template.replace("{{ITEMS_DATA}}", json_str)
    # 替换最后更新时间
    output = output.replace("lastUpdated: '等待更新...'", f"lastUpdated: '{now_str}'")
    
    # 5. 生成 index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(output)
    print(f"更新成功！时间: {now_str}, 条目数: {len(data)}")

if __name__ == "__main__":
    generate_html()

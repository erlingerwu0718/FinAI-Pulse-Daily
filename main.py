import feedparser
import json
import datetime
import pytz
import re
import os
from deep_translator import GoogleTranslator

tz = pytz.timezone('Asia/Shanghai')

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.replace("&nbsp;", " ")

def translate_text(text):
    # 简单的重试机制
    try:
        return GoogleTranslator(source='auto', target='zh-CN').translate(text[:500])
    except Exception:
        return text # 翻译失败返还原文

def fetch_data():
    items = []
    current_year = datetime.datetime.now().year
    
    # --- 1. 读取手动维护的 X 数据 ---
    print("正在读取 x_data.json ...")
    try:
        if os.path.exists("x_data.json"):
            with open("x_data.json", "r", encoding="utf-8") as f:
                x_items = json.load(f)
                if isinstance(x_items, list):
                    # 确保手动数据也有 title_en，如果没有，就用 title 顶替
                    for x in x_items:
                        if 'title_en' not in x:
                            x['title_en'] = x['title'] 
                    items.extend(x_items)
    except Exception as e:
        print(f"读取 X 数据失败: {e}")

    # --- 2. 抓取 Google News ---
    print("正在抓取 Google News...")
    try:
        news_url = "https://news.google.com/rss/search?q=AI+in+Finance+when:1d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(news_url)
        for entry in feed.entries[:15]: # 稍微多抓一点
            cn_title = translate_text(entry.title)
            raw_summary = clean_html(entry.summary) if 'summary' in entry else entry.title
            cn_summary = translate_text(raw_summary[:200] + "...")
            
            items.append({
                "id": entry.link,
                "source": "News",
                "title": cn_title,         # 中文标题
                "title_en": entry.title,   # 英文原标题
                "time": datetime.datetime.now().strftime("%Y-%m-%d"),
                "link": entry.link,
                "summary": cn_summary
            })
    except Exception as e:
        print(f"News Error: {e}")

    # --- 3. 抓取 ArXiv ---
    print("正在抓取 ArXiv...")
    try:
        arxiv_url = "http://export.arxiv.org/api/query?search_query=all:finance+AND+all:artificial+intelligence&sortBy=submittedDate&sortOrder=descending&max_results=5"
        feed = feedparser.parse(arxiv_url)
        for entry in feed.entries:
            pub_date = entry.published[:10]
            if int(pub_date[:4]) > current_year + 1: continue
            
            raw_title = entry.title.replace("\n", " ")
            cn_title = translate_text(raw_title)
            cn_summary = translate_text(entry.summary[:200] + "...")
            
            items.append({
                "id": entry.id,
                "source": "Paper",
                "title": cn_title,      # 中文标题
                "title_en": raw_title,  # 英文原标题
                "time": pub_date,
                "link": entry.link,
                "summary": cn_summary
            })
    except Exception as e:
        print(f"ArXiv Error: {e}")
    
    # 按时间倒序
    items.sort(key=lambda x: x['time'], reverse=True)
    
    return items

def generate_html():
    data = fetch_data()
    if not data: data = []
    
    json_str = json.dumps(data, ensure_ascii=False)
    now_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    
    try:
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
        output = template.replace("{{ITEMS_DATA}}", json_str)
        output = output.replace("lastUpdated: '等待更新...'", f"lastUpdated: '{now_str}'")
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(output)
        print("更新成功！")
    except Exception as e:
        print(f"HTML生成错误: {e}")

if __name__ == "__main__":
    generate_html()

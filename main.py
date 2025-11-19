import feedparser
import json
import datetime
import pytz
import re
from deep_translator import GoogleTranslator

# 设置北京时间
tz = pytz.timezone('Asia/Shanghai')

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.replace("&nbsp;", " ")

def translate_text(text):
    try:
        # 限制长度以防翻译超时，只翻译前300字符
        return GoogleTranslator(source='auto', target='zh-CN').translate(text[:500])
    except Exception as e:
        print(f"Translation failed: {e}")
        return text # 如果翻译失败，返回原文

def fetch_data():
    items = []
    current_year = datetime.datetime.now().year
    translator = GoogleTranslator(source='auto', target='zh-CN')
    
    # --- 1. 抓取 Google News (AI Finance) ---
    print("正在抓取 Google News 并翻译...")
    try:
        news_url = "https://news.google.com/rss/search?q=AI+in+Finance+when:1d&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(news_url)
        
        for entry in feed.entries[:12]: # 取前12条
            pub_date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # 清洗 + 翻译
            raw_summary = clean_html(entry.summary) if 'summary' in entry else entry.title
            cn_title = translate_text(entry.title)
            cn_summary = translate_text(raw_summary[:200] + "...") # 只翻译前200字作为摘要
            
            items.append({
                "id": entry.link,
                "source": "News",
                "title": cn_title, # 中文标题
                "title_en": entry.title, # 保留英文原标题备用
                "time": pub_date,
                "link": entry.link,
                "summary": cn_summary, # 中文摘要
            })
    except Exception as e:
        print(f"News Error: {e}")

    # --- 2. 抓取 ArXiv (保持不变，也加上翻译) ---
    print("正在抓取 ArXiv...")
    try:
        arxiv_url = "http://export.arxiv.org/api/query?search_query=all:finance+AND+all:artificial+intelligence&sortBy=submittedDate&sortOrder=descending&max_results=5"
        feed = feedparser.parse(arxiv_url)
        
        for entry in feed.entries:
            pub_date = entry.published[:10]
            if int(pub_date[:4]) > current_year + 1: continue

            cn_title = translate_text(entry.title.replace("\n", " "))
            cn_summary = translate_text(entry.summary[:200] + "...")

            items.append({
                "id": entry.id,
                "source": "Paper",
                "title": cn_title,
                "time": pub_date,
                "link": entry.link,
                "summary": cn_summary,
            })
    except Exception as e:
        print(f"ArXiv Error: {e}")
    
    return items

def generate_html():
    data = fetch_data()
    if not data:
        data = [{"id": "0", "source": "System", "title": "暂无更新", "time": "", "link": "#", "summary": "请稍后再试"}]

    json_str = json.dumps(data, ensure_ascii=False)
    now_str = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")
    
    try:
        with open("template.html", "r", encoding="utf-8") as f:
            template = f.read()
        
        output = template.replace("{{ITEMS_DATA}}", json_str)
        output = output.replace("lastUpdated: '等待更新...'", f"lastUpdated: '{now_str}'")
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(output)
        print(f"更新成功！时间: {now_str}")
        
    except Exception as e:
        print(f"HTML生成错误: {e}")

if __name__ == "__main__":
    generate_html()

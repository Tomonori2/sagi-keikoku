# 警察庁SOS47「注意喚起・お知らせ」から、最近の詐欺の手口タイトルだけを取得して
# news_data.js に保存する。統計発表（お知らせ）は除外し、手口の注意喚起のみを対象にする。
import re
import sys
import json
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

URL = "https://www.npa.go.jp/bureau/safetylife/sos47/new-topics/"
OUT_FILE = "news_data.js"
MAX_ITEMS = 8

ARTICLE_RE = re.compile(
    r'<a href="([^"]+)" class="top-news_inner">.*?'
    r'<span class="top-news_date">([^<]+)</span>\s*'
    r'<label class="top-news_cat" data-cat="([^"]+)">.*?'
    r'<p class="top-news_text">([^<]+)</p>',
    re.S,
)


DATE_RE = re.compile(r"(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日")


def date_key(date_str):
    m = DATE_RE.search(date_str)
    if not m:
        return (0, 0, 0)
    y, mo, d = m.groups()
    return (int(y), int(mo), int(d))


def fetch_news():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as res:
        html = res.read().decode("utf-8")

    seen_titles = set()
    items = []
    for href, date, cat, title in ARTICLE_RE.findall(html):
        if cat != "caution":  # 「注意喚起」のみ（統計発表の「お知らせ」は除外）
            continue
        title = title.strip()
        if title in seen_titles:  # ページ上部の「特集」欄との重複を除く
            continue
        seen_titles.add(title)
        items.append({
            "date": date.strip().replace("　", " "),
            "title": title,
            "url": "https://www.npa.go.jp" + href,
        })

    items.sort(key=lambda it: date_key(it["date"]), reverse=True)
    return items[:MAX_ITEMS]


def save(items):
    js = "// 警察庁SOS47ページから自動取得（fetch_scam_news.py）。手動で書き換えないこと。\n"
    js += "const SCAM_NEWS = " + json.dumps(items, ensure_ascii=False, indent=2) + ";\n"
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(js)


if __name__ == "__main__":
    print("警察庁の注意喚起情報を取得中...")
    items = fetch_news()
    if not items:
        print("⚠️ 0件でした。ページの構造が変わった可能性があります。news_data.js は更新しません。")
    else:
        save(items)
        print(f"💾 {len(items)}件を {OUT_FILE} に保存しました")
        for it in items:
            print(f"  ・{it['date']}　{it['title']}")

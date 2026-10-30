#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solar AM Notes - 最新ニュース・政策動向 自動収集スクリプト (ワイド拡充版)
・経済産業省 / 資源エネルギー庁 公式新着 (Atom)
・スマートジャパン（再エネ・電力システム専門）
・日経BP メガソーラービジネス / SOLAR JOURNAL / PVeye（太陽光専門メディア）
・Google News RSS（メガソーラー・政策・規制・条例・市場・PPA・盗難・事故・ファイナンス）
などから、アセットマネージャーに関わる最新情報を多角的に収集し data/news.json に保存します。
※Python標準ライブラリのみで動作します。
"""

import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# JSTタイムゾーン
JST = timezone(timedelta(hours=9))

def build_gnews_url(query):
    """Google News RSS URLを生成"""
    encoded = urllib.parse.quote(query)
    return f"https://news.google.com/rss/search?hl=ja&gl=JP&ceid=JP:ja&q={encoded}"

# 収集フィード定義（広範囲カバー）
FEEDS = [
    # 1. 経産省公式
    {
        "name": "経済産業省 / 資源エネルギー庁",
        "url": "https://www.meti.go.jp/ml_index_release_atom.xml",
        "type": "atom",
        "category": "meti",
        "filter_keywords": True,
    },
    {
        "name": "経済産業省 METI Journal",
        "url": "https://journal.meti.go.jp/feed/",
        "type": "rss2",
        "category": "meti",
        "filter_keywords": True,
    },
    # 2. 専門メディア
    {
        "name": "スマートジャパン",
        "url": "https://rss.itmedia.co.jp/rss/2.0/smartjapan.xml",
        "type": "rss2",
        "category": "media",
        "filter_keywords": False,
    },
    {
        "name": "日経BP メガソーラービジネス",
        "url": "https://project.nikkeibp.co.jp/ms/mega-solar/index.rdf",
        "type": "rdf",
        "category": "media",
        "filter_keywords": False,
    },
    {
        "name": "SOLAR JOURNAL",
        "url": "https://solarjournal.jp/feed/",
        "type": "rss2",
        "category": "media",
        "filter_keywords": False,
    },
    {
        # RSS非提供のため公開ニュース一覧HTMLから見出しのみ抽出（本文は会員限定）
        "name": "PVeye",
        "url": "https://www.pveye.jp/article/news/",
        "type": "pveye_html",
        "category": "media",
        "filter_keywords": False,
    },
    # 3. Google News：政策・規制・条例・行政指導
    {
        "name": "Google News（政策・自治体条例）",
        "url": build_gnews_url('メガソーラー OR "太陽光発電" (経産省 OR 環境省 OR 規制 OR 条例 OR ガイドライン OR 指導 OR 訴訟 OR 盛土)'),
        "type": "gnews",
        "category": "policy",
        "filter_keywords": False,
    },
    # 4. Google News：FIT/FIP・市場・出力制御・PPA・蓄電池
    {
        "name": "Google News（制度・市場・PPA）",
        "url": build_gnews_url('("FIT" OR "FIP" OR "出力制御" OR "系統用蓄電池" OR "オフサイトPPA" OR "コーポレートPPA" OR "JEPX" OR "廃棄等費用") (太陽光 OR 再エネ)'),
        "type": "gnews",
        "category": "market",
        "filter_keywords": False,
    },
    # 5. Google News：O&M・事故・盗難・現場トラブル
    {
        "name": "Google News（O&M・保安・事故・盗難）",
        "url": build_gnews_url('太陽光発電 (ケーブル盗難 OR 銅線盗難 OR 火災 OR 土砂 OR 点検 OR 保安 OR パワコン OR ドローン)'),
        "type": "gnews",
        "category": "om_tech",
        "filter_keywords": False,
    },
    # 6. Google News：投資・ファンド・M&A・セカンダリー
    {
        "name": "Google News（投資・ファイナンス）",
        "url": build_gnews_url('太陽光発電所 (インフラファンド OR 買収 OR 売却 OR セカンダリー OR 出資 OR ファンド OR GK-TK)'),
        "type": "gnews",
        "category": "finance",
        "filter_keywords": False,
    },
]

# 経産省などの汎用フィード用キーワード
KEYWORDS = [
    "太陽光", "メガソーラー", "再エネ", "再生可能エネルギー", "FIT", "FIP",
    "調達価格", "出力制御", "系統連系", "系統", "蓄電池", "電力市場", "JEPX",
    "インフラファンド", "電気事業法", "保安規程", "電気主任技術者",
    "廃棄等費用", "放置太陽光", "林地開発", "盛土", "GX", "脱炭素電源",
    "アグリゲーション", "オフサイトPPA", "コーポレートPPA", "非化石",
    "ペロブスカイト", "発電所", "送配電", "需給", "エネルギー基本計画"
]

def is_relevant(text):
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False

def determine_category(title, summary, default_cat):
    """ニュース内容から最適なカテゴリを決定"""
    comb = f"{title} {summary}"
    if any(k in comb for k in ["インフラファンド", "買収", "売却", "セカンダリー", "融資", "出資", "ファンド", "GK-TK", "TK出資", "IRR", "DSCR", "プロジェクトファイナンス"]):
        return "finance"
    elif any(k in comb for k in ["ケーブル盗難", "銅線", "盗難", "火災", "土砂", "法面", "点検", "故障", "ドローン", "パワコン", "モジュール", "保安規程", "電気保安", "電気主任技術者"]):
        return "om_tech"
    elif any(k in comb for k in ["出力制御", "JEPX", "市場", "インバランス", "系統連系", "連系線", "代理制御", "系統用蓄電池", "PPA", "オフサイトPPA", "需給"]):
        return "market"
    elif any(k in comb for k in ["FIT", "FIP", "調達価格", "算定委員会", "特措法", "法改正", "ガイドライン", "廃棄等費用", "条例", "規制", "説明会", "森林法", "林地開発", "盛土"]):
        return "policy"
    elif default_cat in ["meti", "policy", "market", "finance", "om_tech"]:
        return default_cat
    else:
        return "industry"

def fetch_feed(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 SolarAMNewsBot/2.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read()
    except Exception as e:
        print(f"[WARN] フィード取得失敗: {url[:60]}... ({e})", file=sys.stderr)
        return None

def clean_html(raw_html):
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", "", raw_html)
    return clean.strip().replace("\n", " ").replace("\r", "").replace("&quot;", '"').replace("&amp;", "&")

def parse_date(date_str):
    if not date_str:
        return datetime.now(JST).strftime("%Y-%m-%d")
    date_str = date_str.strip()
    iso_match = re.match(r"^(\d{4}-\d{2}-\d{2})", date_str)
    if iso_match:
        return iso_match.group(1)
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.astimezone(JST).strftime("%Y-%m-%d")
    except Exception:
        pass
    return datetime.now(JST).strftime("%Y-%m-%d")

def split_gnews_title(raw_title):
    """Google News の 'タイトル - 配信元' を分離"""
    if not raw_title:
        return "", "Google News"
    parts = raw_title.rsplit(" - ", 1)
    if len(parts) == 2 and len(parts[1]) < 30:
        return parts[0].strip(), parts[1].strip()
    return raw_title.strip(), "ニュース"

def parse_pveye_html(feed_def, data):
    """PVeye ニュース一覧ページ（eye sight / Inside News）から見出しを抽出"""
    items = []
    html = data.decode("utf-8", errors="ignore")
    today = datetime.now(JST).strftime("%Y-%m-%d")
    pattern = re.compile(
        r'<article class="item"><a href="(/(?:eye_sight|inside_news)/view/\d+/?)">[\s\S]*?<h3>([\s\S]*?)</h3>([\s\S]*?)</article>'
    )
    for m in pattern.finditer(html):
        link = "https://www.pveye.jp" + m.group(1)
        title = clean_html(m.group(2))
        rest = m.group(3)
        sub = re.search(r'<p class="sub-title\d*"[^>]*>([\s\S]*?)</p>', rest)
        summary = clean_html(sub.group(1)) if sub else ""
        # 日付は「YYYY年MM月号」表記のため号の1日とし、未来日付は今日に丸める
        dm = re.search(r"(\d{4})年(\d{1,2})月号", rest)
        date = f"{dm.group(1)}-{int(dm.group(2)):02d}-01" if dm else today
        if date > today:
            date = today
        items.append({
            "title": title,
            "summary": summary[:160],
            "link": link,
            "date": date,
            "source": feed_def["name"],
            "category": determine_category(title, summary, feed_def["category"])
        })
    return items

def parse_feed(feed_def, data):
    items = []
    if not data:
        return items
    if feed_def["type"] == "pveye_html":
        return parse_pveye_html(feed_def, data)
    try:
        root = ET.fromstring(data)
    except ET.ParseError as e:
        print(f"[WARN] XMLパース失敗: {feed_def['name']} ({e})", file=sys.stderr)
        return items

    ftype = feed_def["type"]

    if ftype == "atom":
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry_tags = root.findall("atom:entry", ns)
        if not entry_tags:
            entry_tags = root.findall("entry")

        for entry in entry_tags:
            title_el = entry.find("atom:title", ns)
            if title_el is None:
                title_el = entry.find("title")
            title = title_el.text if (title_el is not None and title_el.text) else ""

            summary_el = entry.find("atom:summary", ns)
            if summary_el is None:
                summary_el = entry.find("atom:content", ns)
            if summary_el is None:
                summary_el = entry.find("summary")
            summary = summary_el.text if (summary_el is not None and summary_el.text) else ""

            link_el = entry.find("atom:link", ns)
            if link_el is None:
                link_el = entry.find("link")
            link = ""
            if link_el is not None:
                link = link_el.get("href") or link_el.text or ""

            date_el = entry.find("atom:updated", ns)
            if date_el is None:
                date_el = entry.find("atom:published", ns)
            if date_el is None:
                date_el = entry.find("updated")
            date = parse_date(date_el.text if date_el is not None else "")

            comb = f"{title} {summary}"
            if feed_def["filter_keywords"] and not is_relevant(comb):
                continue

            items.append({
                "title": clean_html(title),
                "summary": clean_html(summary)[:160],
                "link": link.strip(),
                "date": date,
                "source": feed_def["name"],
                "category": determine_category(title, summary, feed_def["category"])
            })

    elif ftype == "rdf":
        # RSS 1.0 (RDF)
        ns = {"rss": "http://purl.org/rss/1.0/", "dc": "http://purl.org/dc/elements/1.1/"}
        for item in root.findall("rss:item", ns):
            title = item.findtext("rss:title", default="", namespaces=ns)
            summary = item.findtext("rss:description", default="", namespaces=ns)
            link = item.findtext("rss:link", default="", namespaces=ns)
            date = parse_date(item.findtext("dc:date", default="", namespaces=ns))

            comb = f"{title} {summary}"
            if feed_def["filter_keywords"] and not is_relevant(comb):
                continue

            items.append({
                "title": clean_html(title),
                "summary": clean_html(summary)[:160],
                "link": link.strip(),
                "date": date,
                "source": feed_def["name"],
                "category": determine_category(title, summary, feed_def["category"])
            })

    elif ftype in ["rss2", "gnews"]:
        channel = root.find("channel")
        item_tags = channel.findall("item") if channel is not None else root.findall(".//item")
        for item in item_tags:
            raw_title = item.find("title").text if item.find("title") is not None else ""
            desc_el = item.find("description")
            summary = desc_el.text if (desc_el is not None and desc_el.text) else ""
            link_el = item.find("link")
            link = link_el.text if (link_el is not None and link_el.text) else ""
            date_el = item.find("pubDate")
            date = parse_date(date_el.text if date_el is not None else "")

            if ftype == "gnews":
                title, src = split_gnews_title(raw_title)
                # 「写真・画像」「フォト」等の画像専用リンクは除外
                if any(x in title for x in ["写真・画像", "フォトギャラリー", "写真(1/"]):
                    continue
                summary = clean_html(summary)
                # 概要がソース名と同じか極端に短い場合は空白に
                if summary == src or len(summary) < 5 or summary.startswith("&nbsp;"):
                    summary = ""
            else:
                title = raw_title
                src = feed_def["name"]
                summary = clean_html(summary)

            comb = f"{title} {summary}"
            if feed_def["filter_keywords"] and not is_relevant(comb):
                continue

            items.append({
                "title": clean_html(title),
                "summary": clean_html(summary)[:160],
                "link": link.strip(),
                "date": date,
                "source": src,
                "category": determine_category(title, summary, feed_def["category"])
            })

    return items

def load_curated_seed_topics():
    """アセットマネージャーとして押さえるべき最重要政策・審議会トピック"""
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    return [
        {
            "title": "再エネ特措法に基づく「地域共生」の規律強化（事前説明会の義務化等）",
            "summary": "GX脱炭素電源法に基づく改正再エネ特措法により、一定規模以上の太陽光発電設備について周辺地域への事前周知・説明会開催が認定・変更認定の要件化。違反時の交付金一時留保制度も運用開始。",
            "link": "https://www.enecho.meti.go.jp/category/saving_and_new/saiene/kaitori/fit_explain.html",
            "date": today_str,
            "source": "資源エネルギー庁",
            "category": "policy",
            "featured": True
        },
        {
            "title": "太陽光発電設備の廃棄等費用積立制度の運用状況と取り戻し要件",
            "summary": "10kW以上のFIT/FIP認定案件を対象に調達期間終了前10年間で行われる外部積立（推進機関積立）。取り戻し事由（適正な解体・撤去の実施等）のガイドラインを確認。",
            "link": "https://www.enecho.meti.go.jp/category/saving_and_new/saiene/kaitori/fit_reserve.html",
            "date": today_str,
            "source": "資源エネルギー庁",
            "category": "policy",
            "featured": True
        },
        {
            "title": "全国エリアにおける再エネ出力制御の見通しとオンライン代理制御の精算ルール",
            "summary": "春季・秋季の軽負荷期における太陽光出力制御の実施状況、オフライン事業者の制御をオンライン事業者が代替する「オンライン代理制御」の事業者間精算ルールと最新実績データ。",
            "link": "https://www.occto.or.jp/",
            "date": today_str,
            "source": "電力広域的運営推進機関（OCCTO）",
            "category": "market",
            "featured": True
        },
        {
            "title": "調達価格等算定委員会における最新のFIT/FIP買取価格・基準価格の算定議論",
            "summary": "次年度以降の事業用太陽光（入札対象外・入札対象規模）の調達価格・FIP基準価格、適正利潤率（IRR前提）、地域協調型電源の要件などの最新審議資料。",
            "link": "https://www.meti.go.jp/shingikai/santeii/index.html",
            "date": today_str,
            "source": "経済産業省 審議会",
            "category": "policy",
            "featured": True
        },
        {
            "title": "太陽電池発電設備の保安規程届出および使用前自己確認制度の点検指導状況",
            "summary": "産業保安グループ電力安全課による、小規模事業用電気工作物（10kW以上50kW未満）の使用前自己確認および高圧・特高発電所の事故報告・自然災害対策に関する最新ガイダンス。",
            "link": "https://www.meti.go.jp/policy/safety_security/industrial_safety/sangyo/electric/index.html",
            "date": today_str,
            "source": "経済産業省 産業保安",
            "category": "om_tech",
            "featured": True
        }
    ]

def main():
    print(f"[{datetime.now(JST)}] 最新ニュース・政策情報の広域収集を開始します...")
    all_items = []

    for f in FEEDS:
        print(f"-> 取得中: {f['name']}")
        raw = fetch_feed(f["url"])
        parsed = parse_feed(f, raw)
        print(f"   取得件数: {len(parsed)} 件")
        all_items.extend(parsed)

    seeds = load_curated_seed_topics()
    all_items = seeds + all_items

    # タイトルの正規化による重複排除（類似タイトルの除外）
    seen_titles = set()
    unique_items = []
    for item in all_items:
        t = re.sub(r"[\s\u3000\-_|:：【】［］（）()]+", "", item["title"]).lower()
        if not t or len(t) < 5 or t in seen_titles:
            continue
        seen_titles.add(t)
        unique_items.append(item)

    # 日付降順でソート（featured は最上位）
    unique_items.sort(key=lambda x: (not x.get("featured", False), x.get("date", "")), reverse=True)

    # 上限を120件に拡張
    unique_items = unique_items[:120]

    result = {
        "updated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M JST"),
        "total_count": len(unique_items),
        "items": unique_items
    }

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "news.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # assets/js/news_data.js にも出力（ローカル file:// 閲覧時のCORS回避用）
    js_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "js")
    os.makedirs(js_dir, exist_ok=True)
    js_file = os.path.join(js_dir, "news_data.js")
    with open(js_file, "w", encoding="utf-8") as f:
        f.write("window.SOLAR_NEWS_DATA = " + json.dumps(result, ensure_ascii=False, indent=2) + ";\n")

    print(f"[{datetime.now(JST)}] 収集完了: 合計 {len(unique_items)} 件を {out_file} および {js_file} に保存しました。")

if __name__ == "__main__":
    main()

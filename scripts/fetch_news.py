#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Solar AM Notes - 最新ニュース・政策動向 自動収集スクリプト
経済産業省、資源エネルギー庁、スマートジャパン（再エネ・電力専門メディア）等の
公式フィードから、メガソーラー・再エネ関連情報を抽出して data/news.json に保存します。
※Python標準ライブラリのみで動作します（外部パッケージ不要）。
"""

import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

# JSTタイムゾーン
JST = timezone(timedelta(hours=9))

# 収集対象のフィード定義
FEEDS = [
    {
        "name": "経済産業省 / 資源エネルギー庁",
        "url": "https://www.meti.go.jp/ml_index_release_atom.xml",
        "type": "atom",
        "category": "meti",
        "filter_keywords": True,  # 再エネ・電力・太陽光関連を抽出
    },
    {
        "name": "経済産業省 METI Journal",
        "url": "https://journal.meti.go.jp/feed/",
        "type": "rss2",
        "category": "meti",
        "filter_keywords": True,
    },
    {
        "name": "スマートジャパン（再エネ・電力専門）",
        "url": "https://rss.itmedia.co.jp/rss/2.0/smartjapan.xml",
        "type": "rss2",
        "category": "media",
        "filter_keywords": False,  # 専門メディアなので全件対象
    },
]

# メガソーラーAM関連キーワード（経産省などの絞り込み用）
KEYWORDS = [
    "太陽光", "メガソーラー", "再エネ", "再生可能エネルギー", "FIT", "FIP",
    "調達価格", "出力制御", "系統連系", "系統", "蓄電池", "電力市場", "JEPX",
    "インフラファンド", "電気事業法", "保安規程", "電気主任技術者",
    "廃棄等費用", "放置太陽光", "林地開発", "盛土", "GX", "脱炭素電源",
    "アグリゲーション", "オフサイトPPA", "コーポレートPPA", "非化石",
    "ペロブスカイト", "発電所", "送配電", "需給", "エネルギー基本計画"
]

def is_relevant(text):
    """テキストに太陽光・再エネ関連キーワードが含まれているか判定"""
    text_lower = text.lower()
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            return True
    return False

def determine_category(title, summary, default_cat):
    """ニュース内容からカテゴリタグを決定"""
    comb = f"{title} {summary}"
    if any(k in comb for k in ["FIT", "FIP", "調達価格", "算定委員会", "特措法", "法改正", "ガイドライン", "廃棄等", "説明会"]):
        return "policy"  # 制度・法改正
    elif any(k in comb for k in ["出力制御", "JEPX", "市場", "インバランス", "系統", "連系線", "代理制御", "需給"]):
        return "market"  # 市場・出力制御
    elif any(k in comb for k in ["O&M", "点検", "故障", "火災", "盗難", "ドローン", "パワコン", "モジュール", "保安", "劣化"]):
        return "om_tech" # O&M・技術
    elif default_cat == "meti":
        return "meti"    # 経産省・エネ庁
    else:
        return "industry"# 業界動向

def fetch_feed(url):
    """URLからXMLデータを取得（タイムアウト・User-Agent設定）"""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SolarAMNewsBot/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return res.read()
    except Exception as e:
        print(f"[WARN] フィード取得失敗: {url} ({e})", file=sys.stderr)
        return None

def clean_html(raw_html):
    """簡単なHTMLタグ除去"""
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", "", raw_html)
    return clean.strip().replace("\n", " ").replace("\r", "")

def parse_date(date_str):
    """各種日付文字列を標準フォーマット (YYYY-MM-DD) に変換"""
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

def parse_feed(feed_def, data):
    """XMLをパースしてアイテムリストを返す（Element bool評価のトラップを回避）"""
    items = []
    if not data:
        return items
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
            # title
            title_el = entry.find("atom:title", ns)
            if title_el is None:
                title_el = entry.find("title")
            title = title_el.text if (title_el is not None and title_el.text) else ""

            # summary
            summary_el = entry.find("atom:summary", ns)
            if summary_el is None:
                summary_el = entry.find("atom:content", ns)
            if summary_el is None:
                summary_el = entry.find("summary")
            summary = summary_el.text if (summary_el is not None and summary_el.text) else ""

            # link
            link_el = entry.find("atom:link", ns)
            if link_el is None:
                link_el = entry.find("link")
            link = ""
            if link_el is not None:
                link = link_el.get("href") or link_el.text or ""

            # date
            date_el = entry.find("atom:updated", ns)
            if date_el is None:
                date_el = entry.find("atom:published", ns)
            if date_el is None:
                date_el = entry.find("updated")
            date = parse_date(date_el.text if date_el is not None else "")

            # フィルタリング
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

    elif ftype == "rss2":
        channel = root.find("channel")
        item_tags = channel.findall("item") if channel is not None else root.findall(".//item")
        for item in item_tags:
            title_el = item.find("title")
            title = title_el.text if (title_el is not None and title_el.text) else ""

            desc_el = item.find("description")
            summary = desc_el.text if (desc_el is not None and desc_el.text) else ""

            link_el = item.find("link")
            link = link_el.text if (link_el is not None and link_el.text) else ""

            date_el = item.find("pubDate")
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

    return items

def load_curated_seed_topics():
    """アセットマネージャーとして押さえるべき重要政策・直近トピック（シードデータ）"""
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
            "category": "meti",
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
    print(f"[{datetime.now(JST)}] ニュース・政策情報の収集を開始します...")
    all_items = []

    for f in FEEDS:
        print(f"-> 取得中: {f['name']} ({f['url']})")
        raw = fetch_feed(f["url"])
        parsed = parse_feed(f, raw)
        print(f"   取得件数: {len(parsed)} 件")
        all_items.extend(parsed)

    # シード（重要固定トピック）をマージ
    seeds = load_curated_seed_topics()
    all_items = seeds + all_items

    # タイトルによる重複排除
    seen_titles = set()
    unique_items = []
    for item in all_items:
        t = item["title"].strip()
        if not t or t in seen_titles:
            continue
        seen_titles.add(t)
        unique_items.append(item)

    # 日付降順でソート（featured は最上位）
    unique_items.sort(key=lambda x: (not x.get("featured", False), x.get("date", "")), reverse=True)
    unique_items = unique_items[:60]

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

    print(f"[{datetime.now(JST)}] 収集完了: {len(unique_items)} 件を {out_file} に保存しました。")

if __name__ == "__main__":
    main()

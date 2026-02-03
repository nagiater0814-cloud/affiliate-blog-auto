import os
import random
import requests
import re
import time
from datetime import datetime, timezone, timedelta
import google.generativeai as genai

# ==========================================
# 0. 環境設定
# ==========================================
WP_URL = os.environ.get("WP_URL")
WP_USER = os.environ.get("WP_USER")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Geminiの設定（★ここを最新の軽量モデルに変更！）
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# ==========================================
# 1. 曜日別テーマ設定
# ==========================================
DAILY_THEMES = {
    0: {  # 月曜
        "category": "睡眠",
        "products": [
            {"id": "MON-1", "name": "高級マットレス", "target": "睡眠の質向上、朝の腰痛", "keywords": ["マットレス", "腰痛"], "pexels_query": "sleeping bedroom mattress"},
            {"id": "MON-2", "name": "安眠枕", "target": "首の痛み、ストレートネック", "keywords": ["枕", "首"], "pexels_query": "pillow sleeping comfort"}
        ]
    },
    1: {  # 火曜
        "category": "在宅ワーク",
        "products": [
            {"id": "TUE-1", "name": "ワークチェア", "target": "在宅ワークの腰痛、坐骨神経痛", "keywords": ["デスクチェア", "腰痛"], "pexels_query": "office chair desk work"},
            {"id": "TUE-2", "name": "姿勢矯正クッション", "target": "猫背、骨盤の歪み", "keywords": ["クッション", "姿勢"], "pexels_query": "cushion office ergonomic"}
        ]
    },
    2: {  # 水曜
        "category": "運動",
        "products": [
            {"id": "WED-1", "name": "ストレッチポール", "target": "背中の張り、肩こり", "keywords": ["ストレッチポール", "肩こり"], "pexels_query": "foam roller stretching"},
            {"id": "WED-2", "name": "ヨガマット", "target": "自宅での運動習慣", "keywords": ["ヨガマット", "運動"], "pexels_query": "yoga mat exercise"}
        ]
    },
    3: {  # 木曜
        "category": "栄養",
        "products": [
            {"id": "THU-1", "name": "プロテイン", "target": "筋肉維持、疲労回復", "keywords": ["プロテイン", "筋肉"], "pexels_query": "protein powder fitness"},
            {"id": "THU-2", "name": "関節サプリ", "target": "膝の違和感、軟骨ケア", "keywords": ["サプリ", "膝"], "pexels_query": "supplements health"}
        ]
    },
    4: {  # 金曜
        "category": "休息",
        "products": [
            {"id": "FRI-1", "name": "リカバリーウェア", "target": "着るだけで疲労回復", "keywords": ["リカバリーウェア", "睡眠"], "pexels_query": "relaxing sleep recovery"},
            {"id": "FRI-2", "name": "入浴剤", "target": "冷え性、深部体温", "keywords": ["入浴剤", "風呂"], "pexels_query": "bath relaxation spa"}
        ]
    },
    5: {  # 土曜
        "category": "足腰",
        "products": [
            {"id": "SAT-1", "name": "膝サポーター", "target": "階段の上り下りが辛い", "keywords": ["サポーター", "膝"], "pexels_query": "knee support brace"},
            {"id": "SAT-2", "name": "インソール", "target": "立ち仕事の足の疲れ", "keywords": ["インソール", "足裏"], "pexels_query": "shoe insole feet"}
        ]
    },
    6: {  # 日曜
        "category": "まとめ",
        "products": [
            {"id": "SUN-1", "name": "健康習慣まとめ", "target": "1週間の振り返り", "keywords": ["健康", "習慣"], "pexels_query": "healthy lifestyle wellness"},
            {"id": "SUN-2", "name": "セルフケア総集編", "target": "自宅でできるケア", "keywords": ["セルフケア", "マッサージ"], "pexels_query": "self care massage"}
        ]
    }
}

def get_japan_weekday():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).weekday()

def select_product():
    weekday = get_japan_weekday()
    theme = DAILY_THEMES[weekday]
    product = random.choice(theme["products"])
    print(f"📅 今日は {['月','火','水','木','金','土','日'][weekday]}曜日 - テーマ:【{theme['category']}】")
    print(f"📦 選定商材: {product['name']}")
    return product

# ==========================================
# 2. 記事作成 (Gemini 1.5 Flash)
# ==========================================
def generate_article(product):
    print("📝 Gemini APIで記事を生成中...")

    prompt = f"""
    あなたは**実務歴8年の現役整体師（国家資格保有）**です。
    以下の商品について、読者の悩みに寄り添うブログ記事をHTML形式で書いてください。

    【商品】{product['name']}
    【ターゲット】{product['target']}

    【構成】
    1. 導入：悩みに共感する（整体院でのエピソードなど）
    2. 原因：なぜ痛むのか医学的に解説
    3. 解決策：商品の紹介（押し売りせず自然に）
    4. まとめ：応援メッセージ

    【ルール】
    - 出力はHTMLの <body> タグの中身のみ（<html>などは不要）
    - タイトルは <h1> タグで1つ入れる
    - 見出しは <h2>, <h3> を使う
    - 文字数は2000文字程度
    - 日本語のみ
    """

    try:
        # ★ここが重要！モデル名を確実に存在する 1.5-flash に指定
        response = model.generate_content(prompt)
        raw_text = response.text

        html_content = raw_text.replace("```html", "").replace("```", "").strip()
        
        title_match = re.search(r"<h1>(.*?)</h1>", html_content, re.DOTALL)
        if title_match:
            title = title_match.group(1)
            content = html_content.replace(title_match.group(0), "").strip()
        else:
            title = f"整体師が教える！{product['name']}の選び方"
            content = html_content

        return {"title": title, "content": content}

    except Exception as e:
        print(f"❌ Geminiエラー: {e}")
        return None

# ==========================================
# 3. 画像取得 & WordPress投稿
# ==========================================
def get_pexels_image(query):
    print(f"📷 画像検索: {query}")
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape&size=large"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200 and res.json().get('photos'):
            return res.json()['photos'][0]['src']['large2x']
    except Exception as e:
        print(f"⚠️ 画像エラー: {e}")
    return None

def post_to_wordpress(title, content, image_url):
    print("🚀 WordPressへ投稿処理開始...")
    
    media_id = None
    if image_url:
        try:
            img_data = requests.get(image_url).content
            filename = f"wp_auto_{int(time.time())}.jpg"
            media_url = f"{WP_URL}/wp-json/wp/v2/media"
            headers = {
                "Content-Type": "image/jpeg",
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
            auth = (WP_USER, WP_APP_PASSWORD)
            res = requests.post(media_url, headers=headers, data=img_data, auth=auth)
            if res.status_code == 201:
                media_id = res.json()['id']
                print("✅ 画像アップロード成功")
        except Exception as e:
            print(f"⚠️ 画像アップロード失敗: {e}")

    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    
    # アフィリエイト枠（仮）
    affiliate_box = f"""
    <div style="margin-top:40px; padding:20px; background:#f0f8ff; border:2px solid #0073aa; border-radius:10px; text-align:center;">
    <h3 style="margin:0; color:#0073aa;">▼整体師のおすすめ</h3>
    <p>腰痛対策なら、まずはこのアイテムを試してみてください。</p>
    <p>（ここにアフィリエイトリンクが自動で入ります）</p>
    </div>
    """
    
    payload = {
        "title": title,
        "content": content + affiliate_box,
        "status": "draft",
        "featured_media": media_id if media_id else 0
    }
    
    res = requests.post(post_url, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"🎉 投稿成功！ 下書きURL: {res.json().get('link')}")
    else:
        print(f"❌ 投稿失敗: {res.text}")

def main():
    print("--- 自動投稿システム開始 ---")
    product = select_product()
    article = generate_article(product)
    
    if article:
        image_url = get_pexels_image(product['pexels_query'])
        post_to_wordpress(article['title'], article['content'], image_url)
    else:
        print("❌ 記事生成に失敗しました")

if __name__ == "__main__":
    main()
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

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# ==========================================
# 1. 曜日別テーマ設定
# ==========================================
DAILY_THEMES = {
    0: { "category": "睡眠・寝具", "products": [
        {"id": "MON-1", "name": "高級マットレス", "target": "睡眠の質向上、朝の腰痛", "keywords": ["マットレス", "腰痛"], "pexels_query": "sleeping bedroom mattress"},
        {"id": "MON-2", "name": "安眠枕", "target": "首の痛み、ストレートネック", "keywords": ["枕", "首"], "pexels_query": "pillow sleeping comfort"}
    ]},
    1: { "category": "在宅ワーク・デスク環境", "products": [
        {"id": "TUE-1", "name": "ワークチェア", "target": "在宅ワークの腰痛、坐骨神経痛", "keywords": ["デスクチェア", "腰痛"], "pexels_query": "office chair desk work"},
        {"id": "TUE-2", "name": "姿勢矯正クッション", "target": "猫背、骨盤の歪み", "keywords": ["クッション", "姿勢"], "pexels_query": "cushion office ergonomic"}
    ]},
    2: { "category": "ストレッチ・運動", "products": [
        {"id": "WED-1", "name": "ストレッチポール", "target": "背中の張り、肩こり", "keywords": ["ストレッチポール", "肩こり"], "pexels_query": "foam roller stretching"},
        {"id": "WED-2", "name": "ヨガマット", "target": "自宅での運動習慣", "keywords": ["ヨガマット", "運動"], "pexels_query": "yoga mat exercise"}
    ]},
    3: { "category": "栄養・サプリメント", "products": [
        {"id": "THU-1", "name": "プロテイン", "target": "筋肉維持、疲労回復", "keywords": ["プロテイン", "筋肉"], "pexels_query": "protein powder fitness"},
        {"id": "THU-2", "name": "関節サプリ", "target": "膝の違和感、軟骨ケア", "keywords": ["サプリ", "膝"], "pexels_query": "supplements health"}
    ]},
    4: { "category": "休息・リカバリー", "products": [
        {"id": "FRI-1", "name": "リカバリーウェア", "target": "着るだけで疲労回復", "keywords": ["リカバリーウェア", "睡眠"], "pexels_query": "relaxing sleep recovery"},
        {"id": "FRI-2", "name": "入浴剤", "target": "冷え性、深部体温", "keywords": ["入浴剤", "風呂"], "pexels_query": "bath relaxation spa"}
    ]},
    5: { "category": "足腰サポート", "products": [
        {"id": "SAT-1", "name": "膝サポーター", "target": "階段の上り下りが辛い", "keywords": ["サポーター", "膝"], "pexels_query": "knee support brace"},
        {"id": "SAT-2", "name": "インソール", "target": "立ち仕事の足の疲れ", "keywords": ["インソール", "足裏"], "pexels_query": "shoe insole feet"}
    ]},
    6: { "category": "健康コラム", "products": [
        {"id": "SUN-1", "name": "健康習慣まとめ", "target": "1週間の振り返り", "keywords": ["健康", "習慣"], "pexels_query": "healthy lifestyle wellness"},
        {"id": "SUN-2", "name": "セルフケア総集編", "target": "自宅でできるケア", "keywords": ["セルフケア", "マッサージ"], "pexels_query": "self care massage"}
    ]}
}

def get_japan_weekday():
    jst = timezone(timedelta(hours=9))
    return datetime.now(jst).weekday()

def select_product():
    weekday = get_japan_weekday()
    theme = DAILY_THEMES[weekday]
    product = random.choice(theme["products"])
    print(f"📅 今日は {['月','火','水','木','金','土','日'][weekday]}曜日 - カテゴリ:【{theme['category']}】")
    print(f"📦 選定商材: {product['name']}")
    return product, theme['category']

# ==========================================
# 2. 記事作成 (SEO・Cocoon対応)
# ==========================================
def generate_article(product):
    print("📝 Gemini APIでSEO記事を執筆中...")
    
    # ★プロンプト強化: 画像タグの挿入位置を強く指示
    prompt = f"""
    あなたはSEOに強い実務歴8年の整体師です。
    以下の商品について、検索上位を狙えるブログ記事を作成してください。

    【商品】{product['name']}
    【ターゲット】{product['target']}
    【キーワード】{', '.join(product['keywords'])}

    【必須ルール】
    本文中に以下の2つのプレースホルダー文字列を**必ず**含めてください。
    1. [[IMAGE_CAUSE]] → 痛みの原因やメカニズムを解説したセクションの直後に入れること。
    2. [[AFFILIATE_AREA]] → 商品を紹介したセクションの直後に入れること。

    【出力構成（区切り文字: [[DELIMITER]]）】
    1. SEOタイトル (32文字以内)
    [[DELIMITER]]
    2. メタディスクリプション (120文字前後)
    [[DELIMITER]]
    3. メタキーワード (カンマ区切り)
    [[DELIMITER]]
    4. 記事本文 (HTML bodyのみ)
       - 導入
       - <h2>原因解説...</h2>
       - 本文
       - [[IMAGE_CAUSE]]
       - <h2>解決策...</h2>
       - 商品紹介
       - [[AFFILIATE_AREA]]
       - まとめ
    """

    try:
        response = model.generate_content(prompt)
        parts = response.text.split("[[DELIMITER]]")
        
        if len(parts) < 4:
            return {
                "seo_title": f"整体師監修！{product['name']}の選び方",
                "meta_desc": f"{product['name']}について整体師が解説します。",
                "meta_kw": ",".join(product['keywords']),
                "content": response.text.replace("```html", "").replace("```", "")
            }

        return {
            "seo_title": parts[0].strip(),
            "meta_desc": parts[1].strip(),
            "meta_kw": parts[2].strip(),
            "content": parts[3].strip().replace("```html", "").replace("```", "")
        }
    except Exception as e:
        print(f"❌ Geminiエラー: {e}")
        return None

# ==========================================
# 3. 画像＆投稿処理
# ==========================================
def get_or_create_category(category_name):
    print(f"📂 カテゴリ確認中: {category_name}")
    auth = (WP_USER, WP_APP_PASSWORD)
    try:
        res = requests.get(f"{WP_URL}/wp-json/wp/v2/categories?search={category_name}", auth=auth)
        if res.status_code == 200 and len(res.json()) > 0:
            for cat in res.json():
                if cat['name'] == category_name:
                    return cat['id']
        
        res = requests.post(f"{WP_URL}/wp-json/wp/v2/categories", json={"name": category_name}, auth=auth)
        if res.status_code == 201:
            return res.json()['id']
    except:
        pass
    return 1

def get_pexels_image(query, size="large2x"):
    print(f"📷 画像検索: {query}")
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape&size={size}"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200 and res.json().get('photos'):
            return res.json()['photos'][0]['src'][size]
    except Exception as e:
        print(f"⚠️ 画像エラー: {e}")
    return None

def upload_image_to_wp(image_url, alt_text):
    if not image_url: return None, None
    try:
        img_data = requests.get(image_url).content
        filename = f"wp_auto_{int(time.time())}_{random.randint(100,999)}.jpg"
        media_url = f"{WP_URL}/wp-json/wp/v2/media"
        headers = { "Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{filename}"' }
        auth = (WP_USER, WP_APP_PASSWORD)
        res = requests.post(media_url, headers=headers, data=img_data, auth=auth)
        if res.status_code == 201:
            media_id = res.json()['id']
            requests.post(f"{WP_URL}/wp-json/wp/v2/media/{media_id}", json={"alt_text": alt_text}, auth=auth)
            return media_id, res.json()['source_url']
    except:
        pass
    return None, None

def post_to_wordpress(article_data, featured_media_id, category_id):
    print("🚀 WordPressへ投稿処理開始...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    payload = {
        "title": article_data['seo_title'],
        "content": article_data['content'],
        "status": "draft",
        "featured_media": featured_media_id if featured_media_id else 0,
        "categories": [category_id],
        "excerpt": article_data['meta_desc'],
        "meta": {
            "the_page_seo_title": article_data['seo_title'],
            "the_page_meta_description": article_data['meta_desc'],
            "the_page_meta_keywords": article_data['meta_kw']
        }
    }
    requests.post(post_url, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    print(f"🎉 投稿成功")

# ==========================================
# 4. メイン処理
# ==========================================
def main():
    print("--- 自動投稿システム (スマート配置版) ---")
    product, category_name = select_product()
    category_id = get_or_create_category(category_name)
    article = generate_article(product)
    
    if article:
        content = article['content']

        # 画像① アイキャッチ
        print("🖼️ 画像1: アイキャッチ取得...")
        header_img, _ = upload_image_to_wp(get_pexels_image(product['pexels_query']), f"{product['name']} イメージ")

        # 画像② 本文用
        print("🖼️ 画像2: 本文用取得...")
        body_query = "spine anatomy" if "腰" in product['keywords'] else "muscle pain doctor"
        _, body_img_src = upload_image_to_wp(get_pexels_image(body_query), "整体師による解説")

        # ★スマート挿入ロジック★
        if body_img_src:
            img_tag = f'<img src="{body_img_src}" alt="解説図" style="width:100%; height:auto; margin: 30px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">'
            
            if "[[IMAGE_CAUSE]]" in content:
                # 1. AIが指示通り場所を作ってくれたら、そこに素直に入れる
                content = content.replace("[[IMAGE_CAUSE]]", img_tag)
            else:
                # 2. AIが忘れたら、「原因」「なぜ」「メカニズム」という言葉が入った見出しを探す
                print("⚠️ タグ忘れ検知: 文脈検索を実行します")
                # 正規表現で <h2 ...>〜原因/なぜ〜</h2> を探す
                match = re.search(r'(<h2.*?(?:原因|なぜ|メカニズム).*?</h2>)', content)
                if match:
                    # 見つかったら、その見出しの直後に入れる
                    print("   ✅ 『原因』セクションを発見。ここに画像を挿入します。")
                    target_h2 = match.group(1)
                    content = content.replace(target_h2, target_h2 + img_tag)
                else:
                    # 3. それも見つからなければ、仕方ないので最初の見出しの後ろ
                    print("   ⚠️ 文脈が見つからないため、最初の見出し後に挿入します")
                    content = content.replace("</h2>", "</h2>" + img_tag, 1)

        # 広告枠の処理
        affiliate_box = f"""
        <div style="margin: 40px 0; padding: 30px; background-color: #f9f9f9; border: 3px solid #66cdaa; border-radius: 10px; text-align: center;">
            <h3 style="margin-top:0; color:#2e8b57; font-size:1.2em;">▼整体師おすすめの{product['name']}</h3>
            <p style="font-size:0.9em; color:#555;">毎日のケアで痛みのない生活を。</p>
            <div style="margin-top:20px; font-weight:bold; color:#d32f2f;">
                （ここにアフィリエイトリンクを貼ってください）
            </div>
        </div>
        """
        if "[[AFFILIATE_AREA]]" in content:
            content = content.replace("[[AFFILIATE_AREA]]", affiliate_box)
        else:
            content += affiliate_box

        article['content'] = content
        post_to_wordpress(article, header_img, category_id)

    else:
        print("❌ 生成失敗")

if __name__ == "__main__":
    main()
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
        {"id": "MON-1", "name": "高級マットレス", "target": "睡眠の質向上、朝の腰痛", "keywords": ["マットレス", "腰痛", "睡眠改善"], "pexels_query": "sleeping bedroom mattress"},
        {"id": "MON-2", "name": "安眠枕", "target": "首の痛み、ストレートネック", "keywords": ["枕", "首こり", "ストレートネック"], "pexels_query": "pillow sleeping comfort"}
    ]},
    1: { "category": "デスクワーク", "products": [
        {"id": "TUE-1", "name": "ワークチェア", "target": "在宅ワークの腰痛、坐骨神経痛", "keywords": ["デスクチェア", "腰痛", "テレワーク"], "pexels_query": "office chair desk work"},
        {"id": "TUE-2", "name": "姿勢矯正クッション", "target": "猫背、骨盤の歪み", "keywords": ["クッション", "姿勢矯正", "骨盤ケア"], "pexels_query": "cushion office ergonomic"}
    ]},
    2: { "category": "運動・ストレッチ", "products": [
        {"id": "WED-1", "name": "ストレッチポール", "target": "背中の張り、肩こり", "keywords": ["ストレッチポール", "肩こり", "筋膜リリース"], "pexels_query": "foam roller stretching"},
        {"id": "WED-2", "name": "ヨガマット", "target": "自宅での運動習慣", "keywords": ["ヨガマット", "宅トレ", "運動不足"], "pexels_query": "yoga mat exercise"}
    ]},
    3: { "category": "栄養・健康食", "products": [
        {"id": "THU-1", "name": "プロテイン", "target": "筋肉維持、疲労回復", "keywords": ["プロテイン", "疲労回復", "栄養補給"], "pexels_query": "protein powder fitness"},
        {"id": "THU-2", "name": "関節サプリ", "target": "膝の違和感、軟骨ケア", "keywords": ["サプリメント", "膝の痛み", "関節ケア"], "pexels_query": "supplements health"}
    ]},
    4: { "category": "休息・入浴", "products": [
        {"id": "FRI-1", "name": "リカバリーウェア", "target": "着るだけで疲労回復", "keywords": ["リカバリーウェア", "睡眠の質", "疲労回復"], "pexels_query": "relaxing sleep recovery"},
        {"id": "FRI-2", "name": "入浴剤", "target": "冷え性、深部体温", "keywords": ["入浴剤", "温活", "リラックス"], "pexels_query": "bath relaxation spa"}
    ]},
    5: { "category": "足腰ケア", "products": [
        {"id": "SAT-1", "name": "膝サポーター", "target": "階段の上り下りが辛い", "keywords": ["サポーター", "膝痛", "ウォーキング"], "pexels_query": "knee support brace"},
        {"id": "SAT-2", "name": "インソール", "target": "立ち仕事の足の疲れ", "keywords": ["インソール", "足の疲れ", "扁平足"], "pexels_query": "shoe insole feet"}
    ]},
    6: { "category": "健康コラム", "products": [
        {"id": "SUN-1", "name": "健康習慣まとめ", "target": "1週間の振り返り", "keywords": ["健康習慣", "生活改善", "予防医学"], "pexels_query": "healthy lifestyle wellness"},
        {"id": "SUN-2", "name": "セルフケア総集編", "target": "自宅でできるケア", "keywords": ["セルフケア", "マッサージ", "ストレッチ"], "pexels_query": "self care massage"}
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
    return product, theme['category']

# ==========================================
# 2. 記事作成
# ==========================================
def generate_article(product):
    print("📝 Gemini APIでSEO記事を執筆中...")
    
    prompt = f"""
    あなたはSEOに強い実務歴8年の整体師です。
    以下の商品について、ブログ記事を作成してください。

    【商品】{product['name']}
    【ターゲット】{product['target']}
    【キーワード】{', '.join(product['keywords'])}

    【出力構成（区切り文字: [[DELIMITER]]）】
    1. SEOタイトル (32文字以内)
    [[DELIMITER]]
    2. メタディスクリプション (120文字前後)
    [[DELIMITER]]
    3. 記事本文 (HTML bodyのみ)
       - 見出し(h2)を使い、[[AFFILIATE_AREA]] という文字列を必ず含めること。
    """

    try:
        response = model.generate_content(prompt)
        parts = response.text.split("[[DELIMITER]]")
        
        if len(parts) < 3:
            return None # 失敗

        return {
            "seo_title": parts[0].strip(),
            "meta_desc": parts[1].strip(),
            "content": parts[2].strip().replace("```html", "").replace("```", "")
        }
    except Exception as e:
        print(f"❌ Geminiエラー: {e}")
        return None

# ==========================================
# 3. カテゴリ・タグ・画像処理
# ==========================================
def get_id_by_name(endpoint, name):
    """カテゴリやタグの名前からIDを取得（なければ作成）"""
    auth = (WP_USER, WP_APP_PASSWORD)
    
    # 1. 検索
    try:
        search_url = f"{WP_URL}/wp-json/wp/v2/{endpoint}?search={name}"
        res = requests.get(search_url, auth=auth)
        if res.status_code == 200 and len(res.json()) > 0:
            # 完全一致を確認
            for item in res.json():
                if item['name'] == name:
                    return item['id']
    except:
        pass

    # 2. 作成
    try:
        create_url = f"{WP_URL}/wp-json/wp/v2/{endpoint}"
        res = requests.post(create_url, json={"name": name}, auth=auth)
        if res.status_code == 201:
            return res.json()['id']
    except:
        pass
    
    return None

def get_tag_ids(keywords):
    """キーワードリストからタグIDのリストを取得"""
    tag_ids = []
    print(f"🏷️ タグ処理中: {keywords}")
    for kw in keywords:
        tid = get_id_by_name("tags", kw)
        if tid:
            tag_ids.append(tid)
    return tag_ids

def get_pexels_image(query):
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape&size=large2x"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200 and res.json().get('photos'):
            return res.json()['photos'][0]['src']['large2x']
    except:
        pass
    return None

def upload_image_to_wp(image_url, alt_text):
    if not image_url: return None
    try:
        img_data = requests.get(image_url).content
        filename = f"wp_auto_{int(time.time())}.jpg"
        media_url = f"{WP_URL}/wp-json/wp/v2/media"
        headers = { "Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{filename}"' }
        auth = (WP_USER, WP_APP_PASSWORD)
        res = requests.post(media_url, headers=headers, data=img_data, auth=auth)
        if res.status_code == 201:
            media_id = res.json()['id']
            # SEO対策: Altテキスト設定
            requests.post(f"{WP_URL}/wp-json/wp/v2/media/{media_id}", json={"alt_text": alt_text}, auth=auth)
            return media_id
    except:
        pass
    return None

def post_to_wordpress(article_data, media_id, category_id, tag_ids):
    print("🚀 WordPressへ投稿処理開始...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    
    payload = {
        "title": article_data['seo_title'],
        "content": article_data['content'],
        "status": "draft",
        "featured_media": media_id if media_id else 0,
        "categories": [category_id] if category_id else [],  # ★カテゴリID
        "tags": tag_ids,                                     # ★タグID配列
        "excerpt": article_data['meta_desc'],                # ★ここが重要（SEO説明文）
        "meta": {
            # Cocoon用予備設定（効かなくてもexcerptが働くのでOK）
            "the_page_seo_title": article_data['seo_title'],
            "the_page_meta_description": article_data['meta_desc'],
        }
    }
    
    res = requests.post(post_url, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"🎉 投稿成功！ 下書きURL: {res.json().get('link')}")
        print(f"   SEO情報: 抜粋(Description)を設定しました")
        print(f"   カテゴリID: {category_id}, タグ数: {len(tag_ids)}")
    else:
        print(f"❌ 投稿失敗: {res.text}")

# ==========================================
# 4. メイン処理
# ==========================================
def main():
    print("--- 自動投稿システム (SEO・カテゴリ・タグ修正版) ---")
    
    # 1. ネタ決め
    product, category_name = select_product()
    
    # 2. カテゴリID取得（なければ作る）
    print(f"📂 カテゴリ準備: {category_name}")
    category_id = get_id_by_name("categories", category_name)
    
    # 3. タグID取得（なければ作る）
    tag_ids = get_tag_ids(product['keywords'])
    
    # 4. 記事生成
    article = generate_article(product)
    
    if article:
        # 5. 画像取得
        print("🖼️ 画像取得中...")
        img_url = get_pexels_image(product['pexels_query'])
        media_id = upload_image_to_wp(img_url, f"{product['name']} イメージ")

        # 6. 本文加工（広告枠・強制画像挿入）
        content = article['content']
        
        # 広告枠
        affiliate_box = f"""
        <div style="margin: 40px 0; padding: 30px; background-color: #f9f9f9; border: 3px solid #66cdaa; border-radius: 10px; text-align: center;">
            <h3 style="margin-top:0; color:#2e8b57;">▼整体師おすすめの{product['name']}</h3>
            <p>詳細はこちら</p>
            <div style="margin-top:20px; color:#d32f2f;">（ここに広告リンク）</div>
        </div>
        """
        if "[[AFFILIATE_AREA]]" in content:
            content = content.replace("[[AFFILIATE_AREA]]", affiliate_box)
        else:
            content += affiliate_box
            
        # 画像強制挿入（見出しH2の後ろ）
        if media_id: # 同じ画像を本文にも使い回す（簡易化のため）
            # ※本来は別の画像が良いが、まずはエラーなく動くことを優先
            pass 

        article['content'] = content

        # 7. 投稿
        post_to_wordpress(article, media_id, category_id, tag_ids)

    else:
        print("❌ 記事生成失敗")

if __name__ == "__main__":
    main()
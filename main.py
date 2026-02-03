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
# ★最新の軽量モデルを指定
model = genai.GenerativeModel('gemini-flash-latest')

# ==========================================
# 1. 曜日別テーマ設定
# ==========================================
DAILY_THEMES = {
    0: { "category": "睡眠", "products": [
        {"id": "MON-1", "name": "高級マットレス", "target": "睡眠の質向上、朝の腰痛", "keywords": ["マットレス", "腰痛"], "pexels_query": "sleeping bedroom mattress"},
        {"id": "MON-2", "name": "安眠枕", "target": "首の痛み、ストレートネック", "keywords": ["枕", "首"], "pexels_query": "pillow sleeping comfort"}
    ]},
    1: { "category": "在宅ワーク", "products": [
        {"id": "TUE-1", "name": "ワークチェア", "target": "在宅ワークの腰痛、坐骨神経痛", "keywords": ["デスクチェア", "腰痛"], "pexels_query": "office chair desk work"},
        {"id": "TUE-2", "name": "姿勢矯正クッション", "target": "猫背、骨盤の歪み", "keywords": ["クッション", "姿勢"], "pexels_query": "cushion office ergonomic"}
    ]},
    2: { "category": "運動", "products": [
        {"id": "WED-1", "name": "ストレッチポール", "target": "背中の張り、肩こり", "keywords": ["ストレッチポール", "肩こり"], "pexels_query": "foam roller stretching"},
        {"id": "WED-2", "name": "ヨガマット", "target": "自宅での運動習慣", "keywords": ["ヨガマット", "運動"], "pexels_query": "yoga mat exercise"}
    ]},
    3: { "category": "栄養", "products": [
        {"id": "THU-1", "name": "プロテイン", "target": "筋肉維持、疲労回復", "keywords": ["プロテイン", "筋肉"], "pexels_query": "protein powder fitness"},
        {"id": "THU-2", "name": "関節サプリ", "target": "膝の違和感、軟骨ケア", "keywords": ["サプリ", "膝"], "pexels_query": "supplements health"}
    ]},
    4: { "category": "休息", "products": [
        {"id": "FRI-1", "name": "リカバリーウェア", "target": "着るだけで疲労回復", "keywords": ["リカバリーウェア", "睡眠"], "pexels_query": "relaxing sleep recovery"},
        {"id": "FRI-2", "name": "入浴剤", "target": "冷え性、深部体温", "keywords": ["入浴剤", "風呂"], "pexels_query": "bath relaxation spa"}
    ]},
    5: { "category": "足腰", "products": [
        {"id": "SAT-1", "name": "膝サポーター", "target": "階段の上り下りが辛い", "keywords": ["サポーター", "膝"], "pexels_query": "knee support brace"},
        {"id": "SAT-2", "name": "インソール", "target": "立ち仕事の足の疲れ", "keywords": ["インソール", "足裏"], "pexels_query": "shoe insole feet"}
    ]},
    6: { "category": "まとめ", "products": [
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
    print(f"📅 今日は {['月','火','水','木','金','土','日'][weekday]}曜日 - テーマ:【{theme['category']}】")
    print(f"📦 選定商材: {product['name']}")
    return product

# ==========================================
# 2. 記事作成 (SEO・Cocoon対応版)
# ==========================================
def generate_article(product):
    print("📝 Gemini APIでSEO完全対応の記事を構成中...")

    prompt = f"""
    あなたはSEOマーケティングに精通した実務歴8年の整体師です。
    以下の商品について、検索上位を狙えるブログ記事を作成してください。

    【商品】{product['name']}
    【ターゲット】{product['target']}
    【キーワード】{', '.join(product['keywords'])}

    【出力構成】
    以下の4つのセクションを「[[DELIMITER]]」という文字列で区切って出力してください。

    1. SEOタイトル
       - 検索結果に表示されるタイトル。
       - **32文字以内**厳守。
       - 重要なキーワードを左側に配置。
    [[DELIMITER]]
    2. メタディスクリプション
       - 検索結果のスニペット用。
       - **120文字前後**。
       - クリックしたくなるような要約。
    [[DELIMITER]]
    3. メタキーワード
       - カンマ区切りで3〜5個（例: 腰痛,マットレス,快眠）。
    [[DELIMITER]]
    4. 記事本文（HTML）
       - <body>タグの中身のみ。
       - 構成:
         - 導入（共感）
         - <h2>原因解説...</h2>
         - 解説本文
         - [[IMAGE_CAUSE]] (←この文字列をそのまま書く)
         - <h2>解決策...</h2>
         - 商品紹介本文
         - [[AFFILIATE_AREA]] (←この文字列をそのまま書く)
         - まとめ

    ※ JSONではなく、プレーンテキストで出力してください。
    """

    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # 区切り文字で分割
        parts = raw_text.split("[[DELIMITER]]")
        
        if len(parts) < 4:
            print("⚠️ データの分割に失敗しました。簡易モードで動作します。")
            return {
                "seo_title": f"整体師が選ぶ！{product['name']}おすすめガイド",
                "meta_desc": f"{product['name']}の効果と選び方を整体師が解説。{product['target']}でお悩みの方へ。",
                "meta_kw": ",".join(product['keywords']),
                "content": raw_text.replace("```html", "").replace("```", "")
            }

        seo_title = parts[0].strip().replace("SEOタイトル", "").replace(":", "").strip()
        meta_desc = parts[1].strip().replace("メタディスクリプション", "").replace(":", "").strip()
        meta_kw = parts[2].strip().replace("メタキーワード", "").replace(":", "").strip()
        content = parts[3].strip().replace("記事本文", "").replace("HTML", "").replace(":", "").replace("```html", "").replace("```", "").strip()

        print(f"✅ SEOデータ生成完了")
        print(f"   SEO Title: {seo_title} ({len(seo_title)}文字)")
        
        return {
            "seo_title": seo_title,
            "meta_desc": meta_desc,
            "meta_kw": meta_kw,
            "content": content
        }

    except Exception as e:
        print(f"❌ Geminiエラー: {e}")
        return None

# ==========================================
# 3. 画像＆投稿処理 (Cocoon対応)
# ==========================================
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
        headers = {
            "Content-Type": "image/jpeg",
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        auth = (WP_USER, WP_APP_PASSWORD)
        
        res = requests.post(media_url, headers=headers, data=img_data, auth=auth)
        if res.status_code == 201:
            data = res.json()
            media_id = data['id']
            # SEO対策: 画像のAltテキストを設定
            requests.post(
                f"{WP_URL}/wp-json/wp/v2/media/{media_id}",
                json={"alt_text": alt_text},
                auth=auth
            )
            return media_id, data['source_url']
    except Exception as e:
        print(f"⚠️ アップロード失敗: {e}")
    return None, None

def post_to_wordpress(article_data, featured_media_id):
    print("🚀 WordPressへ投稿処理開始...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    
    # ★ここが重要：Cocoon用のカスタムフィールド設定
    # the_page_seo_title: SEOタイトル
    # the_page_meta_description: メタディスクリプション
    # the_page_meta_keywords: メタキーワード
    
    payload = {
        "title": article_data['seo_title'], # 記事タイトルもSEOタイトルに合わせる
        "content": article_data['content'],
        "status": "draft",
        "featured_media": featured_media_id if featured_media_id else 0,
        "excerpt": article_data['meta_desc'], # 抜粋にも入れる
        "meta": {
            "the_page_seo_title": article_data['seo_title'],
            "the_page_meta_description": article_data['meta_desc'],
            "the_page_meta_keywords": article_data['meta_kw']
        }
    }
    
    # メタデータの送信を試みる
    try:
        res = requests.post(post_url, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
        if res.status_code == 201:
            print(f"🎉 投稿成功！ 下書きURL: {res.json().get('link')}")
            print("   SEO設定（Cocoon）も完了しました")
        else:
            print(f"❌ 投稿失敗: {res.text}")
    except Exception as e:
        print(f"❌ 送信エラー: {e}")

# ==========================================
# 4. メイン処理
# ==========================================
def main():
    print("--- 自動投稿システム開始 (SEO完全版) ---")
    product = select_product()
    article = generate_article(product)
    
    if article:
        content = article['content']

        # 画像① アイキャッチ
        print("🖼️ アイキャッチ画像...")
        header_img, _ = upload_image_to_wp(
            get_pexels_image(product['pexels_query']), 
            f"{product['name']} イメージ"
        )

        # 画像② 本文挿入用
        print("🖼️ 本文画像...")
        _, body_img_src = upload_image_to_wp(
            get_pexels_image("spine anatomy doctor"), 
            "整体師による姿勢解説"
        )

        # 画像置換
        if body_img_src:
            img_tag = f'<img src="{body_img_src}" alt="姿勢の解説" style="width:100%; height:auto; margin: 20px 0; border-radius: 8px;">'
            content = content.replace("[[IMAGE_CAUSE]]", img_tag)
        else:
            content = content.replace("[[IMAGE_CAUSE]]", "")

        # 広告枠置換
        affiliate_box = f"""
        <div style="margin: 40px 0; padding: 30px; background-color: #fcfcfc; border: 2px solid #66cdaa; border-radius: 8px; text-align: center;">
            <h3 style="margin-top:0; color:#2e8b57;">▼{product['name']}の詳細はこちら</h3>
            <p>整体師も推奨する毎日のケアアイテムです。</p>
            <div style="margin-top:20px; color:#d32f2f; font-weight:bold;">
                （ここにA8.netの広告リンクを貼る）
            </div>
        </div>
        """
        content = content.replace("[[AFFILIATE_AREA]]", affiliate_box)
        article['content'] = content

        # 投稿実行
        post_to_wordpress(article, header_img)

    else:
        print("❌ 記事生成失敗")

if __name__ == "__main__":
    main()
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

# Gemini設定 (gemini-flash-latest を使用)
genai.configure(api_key=GEMINI_API_KEY)
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
# 2. 記事作成 (構成指定あり)
# ==========================================
def generate_article(product):
    print("📝 Gemini APIで記事を構成中...")

    # ★ここがポイント：記事の中に「画像の場所」と「広告の場所」を指定させる
    prompt = f"""
    あなたは実務歴8年の現役整体師です。
    以下の商品について、読者をひきつけるブログ記事をHTML形式で書いてください。

    【商品】{product['name']}
    【ターゲット】{product['target']}

    【構成ルール】
    以下の順番とタグ構成を必ず守ってください。
    
    1. **タイトル** (<h1>タグ)
    2. **導入** (読者の悩みに共感する文章)
    3. **見出し** (<h2>原因解説：...</h2>)
    4. **本文** (医学的な解説)
    5. **[[IMAGE_CAUSE]]** (★ここに「[[IMAGE_CAUSE]]」という文字列をそのまま書いてください。後で画像を挿入します)
    6. **見出し** (<h2>解決策：{product['name']}の活用</h2>)
    7. **本文** (商品の紹介)
    8. **[[AFFILIATE_AREA]]** (★ここに「[[AFFILIATE_AREA]]」という文字列をそのまま書いてください。後で広告枠を挿入します)
    9. **まとめ** (応援メッセージ)

    【出力ルール】
    - HTMLの <body> タグの中身のみ出力
    - 文字数は2000文字程度
    - 専門用語を使いつつ、親しみやすいトーンで
    """

    try:
        response = model.generate_content(prompt)
        raw_text = response.text
        # 不要なマークダウン記号を削除
        html_content = raw_text.replace("```html", "").replace("```", "").strip()
        
        # タイトル抽出
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
# 3. 画像＆投稿処理
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

def upload_image_to_wp(image_url):
    """画像をWPにアップロードしてIDとURLを返す"""
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
            return data['id'], data['source_url']
    except Exception as e:
        print(f"⚠️ アップロード失敗: {e}")
    return None, None

def post_to_wordpress(title, content, featured_media_id):
    print("🚀 WordPressへ投稿処理開始...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    
    payload = {
        "title": title,
        "content": content,
        "status": "draft",
        "featured_media": featured_media_id if featured_media_id else 0
    }
    
    res = requests.post(post_url, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        print(f"🎉 投稿成功！ 下書きURL: {res.json().get('link')}")
    else:
        print(f"❌ 投稿失敗: {res.text}")

# ==========================================
# 4. メイン処理 (画像を2枚使う)
# ==========================================
def main():
    print("--- 自動投稿システム開始 (画像強化版) ---")
    product = select_product()
    article = generate_article(product)
    
    if article:
        content = article['content']

        # --- 画像①：アイキャッチ用（おしゃれな写真） ---
        print("🖼️ アイキャッチ画像を取得中...")
        header_img_url = get_pexels_image(product['pexels_query'])
        header_id, _ = upload_image_to_wp(header_img_url)

        # --- 画像②：本文用（医学的・説明的な写真） ---
        # "spine anatomy" や "back pain doctor" などを検索
        print("🖼️ 本文用の解説画像を取得中...")
        body_query = "spine anatomy doctor" # 医学的な雰囲気を狙う
        body_img_url = get_pexels_image(body_query)
        _, body_img_src = upload_image_to_wp(body_img_url)

        # --- 記事の加工：プレースホルダーを置換 ---
        
        # 1. [[IMAGE_CAUSE]] を 本文用画像タグ に置換
        if body_img_src:
            img_tag = f'<img src="{body_img_src}" alt="身体の歪みのイメージ" style="width:100%; height:auto; margin: 20px 0; border-radius: 8px;">'
            content = content.replace("[[IMAGE_CAUSE]]", img_tag)
        else:
            content = content.replace("[[IMAGE_CAUSE]]", "") # 画像なければ消す

        # 2. [[AFFILIATE_AREA]] を 広告ボックス に置換
        affiliate_box = f"""
        <div style="margin: 40px 0; padding: 30px; background-color: #fdfdfd; border: 3px solid #e0f2f1; border-radius: 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="margin-top: 0; color: #00796b; font-size: 1.2em;">▼整体師おすすめの{product['name']}</h3>
            <p style="font-size: 0.9em; color: #555;">毎日のケアで、痛みのない生活を取り戻しましょう。</p>
            <div style="margin-top: 20px; font-weight: bold; color: #d32f2f;">
                （ここにA8.netの広告リンクを貼り付けてください）
            </div>
        </div>
        """
        content = content.replace("[[AFFILIATE_AREA]]", affiliate_box)

        # --- 投稿 ---
        post_to_wordpress(article['title'], content, header_id)

    else:
        print("❌ 記事生成に失敗しました")

if __name__ == "__main__":
    main()
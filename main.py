"""
SEOアフィリエイト特化型 WordPress自動投稿システム
- 整体師視点のセールスライティング記事を自動生成
- Pexels APIで高品質画像を取得
- WordPressに下書き投稿
"""

import os
import random
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数の読み込み
load_dotenv()

# 環境変数
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini APIの設定
genai.configure(api_key=GEMINI_API_KEY)

# ============================
# 1. 曜日別テーマ設定（ネタ被り防止）
# ============================
# 0=月曜, 1=火曜, ..., 6=日曜
DAILY_THEMES = {
    0: {  # 月曜：【睡眠】
        "category": "睡眠",
        "products": [
            {
                "id": "MON-1",
                "name": "高級マットレス",
                "target": "睡眠の質向上、朝起きた時の腰痛・背中の痛み",
                "keywords": ["マットレス", "腰痛", "睡眠の質"],
                "pexels_query": "sleeping bedroom mattress"
            },
            {
                "id": "MON-2",
                "name": "安眠枕・オーダーメイド枕（Limneなど）",
                "target": "首の痛み、ストレートネック、いびき改善",
                "keywords": ["枕", "首の痛み", "ストレートネック"],
                "pexels_query": "pillow sleeping comfort"
            }
        ]
    },
    1: {  # 火曜：【在宅】
        "category": "在宅ワーク",
        "products": [
            {
                "id": "TUE-1",
                "name": "ワークチェア・ゲーミングチェア",
                "target": "在宅ワークによる腰痛、坐骨神経痛、長時間座り姿勢の問題",
                "keywords": ["デスクチェア", "在宅ワーク", "腰痛"],
                "pexels_query": "office chair desk work"
            },
            {
                "id": "TUE-2",
                "name": "姿勢矯正クッション・座布団",
                "target": "猫背、骨盤の歪み、お尻の痛み",
                "keywords": ["クッション", "姿勢矯正", "骨盤"],
                "pexels_query": "cushion office ergonomic"
            }
        ]
    },
    2: {  # 水曜：【運動】
        "category": "運動・ストレッチ",
        "products": [
            {
                "id": "WED-1",
                "name": "ストレッチポール・フォームローラー",
                "target": "筋膜リリース、肩こり解消、柔軟性向上",
                "keywords": ["ストレッチポール", "筋膜リリース", "肩こり"],
                "pexels_query": "foam roller stretching exercise"
            },
            {
                "id": "WED-2",
                "name": "ヨガマット・トレーニングマット",
                "target": "自宅トレーニング、ヨガ、ストレッチ習慣",
                "keywords": ["ヨガマット", "ストレッチ", "自宅トレーニング"],
                "pexels_query": "yoga mat exercise home"
            }
        ]
    },
    3: {  # 木曜：【栄養】
        "category": "栄養・サプリメント",
        "products": [
            {
                "id": "THU-1",
                "name": "プロテイン・BCAA",
                "target": "筋肉疲労回復、筋力維持、タンパク質不足",
                "keywords": ["プロテイン", "筋肉", "疲労回復"],
                "pexels_query": "protein powder fitness nutrition"
            },
            {
                "id": "THU-2",
                "name": "関節サポートサプリ（グルコサミン・コンドロイチン）",
                "target": "関節痛、膝の痛み、軟骨ケア",
                "keywords": ["グルコサミン", "関節痛", "膝の痛み"],
                "pexels_query": "supplements health vitamins"
            }
        ]
    },
    4: {  # 金曜：【休息】
        "category": "休息・リカバリー",
        "products": [
            {
                "id": "FRI-1",
                "name": "リカバリーウェア（BAKUNE等）",
                "target": "睡眠中の疲労回復、血行促進、冷え性改善",
                "keywords": ["リカバリーウェア", "疲労回復", "睡眠"],
                "pexels_query": "relaxing sleep recovery"
            },
            {
                "id": "FRI-2",
                "name": "入浴剤・エプソムソルト",
                "target": "筋肉疲労、冷え性、リラックス効果",
                "keywords": ["入浴剤", "エプソムソルト", "筋肉疲労"],
                "pexels_query": "bath relaxation spa"
            }
        ]
    },
    5: {  # 土曜：【足腰】
        "category": "足腰サポート",
        "products": [
            {
                "id": "SAT-1",
                "name": "膝サポーター・腰サポーター",
                "target": "膝の痛み、腰痛、スポーツ時のケガ予防",
                "keywords": ["サポーター", "膝の痛み", "腰痛"],
                "pexels_query": "knee support brace sports"
            },
            {
                "id": "SAT-2",
                "name": "インソール・中敷き",
                "target": "足の疲れ、扁平足、立ち仕事の負担軽減",
                "keywords": ["インソール", "足の疲れ", "扁平足"],
                "pexels_query": "shoe insole feet comfort"
            }
        ]
    },
    6: {  # 日曜：【まとめ】
        "category": "週間まとめ・健康コラム",
        "products": [
            {
                "id": "SUN-1",
                "name": "整体師が教える1週間の健康習慣",
                "target": "健康維持、予防医学、生活習慣改善",
                "keywords": ["健康習慣", "予防", "生活改善"],
                "pexels_query": "healthy lifestyle wellness"
            },
            {
                "id": "SUN-2",
                "name": "自宅でできるセルフケア総まとめ",
                "target": "セルフマッサージ、ストレッチ、痛み予防",
                "keywords": ["セルフケア", "マッサージ", "ストレッチ"],
                "pexels_query": "self care massage relaxation"
            }
        ]
    }
}


def get_japan_weekday() -> int:
    """日本時間の曜日を取得する（0=月曜, 6=日曜）"""
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    return now_jst.weekday()


def select_product():
    """曜日に基づいて商材を選定する（ネタ被り防止）"""
    weekday = get_japan_weekday()
    weekday_names = ["月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜"]
    
    theme = DAILY_THEMES[weekday]
    product = random.choice(theme["products"])
    
    print(f"📅 今日は{weekday_names[weekday]}日 - テーマ:【{theme['category']}】")
    print(f"📦 選定商材: {product['name']} (ターゲット: {product['target']})")
    return product


def generate_article(product: dict) -> dict:
    """
    Gemini APIでセールスライティング記事を生成する
    Returns: {"title": str, "content": str}
    """
    prompt = f"""
あなたは**実務歴8年の現役整体師**であり、**国家資格・柔道整復師**を保有しています。
専門家の視点から、読者の悩みに寄り添いながら、解決策として商品を自然に紹介する記事を執筆してください。

【商品テーマ】
{product['name']}

【ターゲット読者の悩み】
{product['target']}

【記事構成ルール（必ず守ってください）】
1. **導入（悩みへの共感）**: 読者の悩みに深く共感するパラグラフ。整体院での実体験や患者さんとのエピソードを交えて。
2. **医学的な原因解説**: なぜその痛みが起こるのか、専門家として分かりやすく解説（骨格、筋肉、神経の観点から）。
3. **解決策の提案（商品紹介）**: {product['name']}がなぜ効果的なのか、整体師としての知見を交えて紹介。
4. **まとめ**: 読者への応援メッセージと行動喚起。

【出力形式】
- 言語: **日本語のみ**（英語は一切使わない）
- フォーマット: HTML形式
- タイトル: <h1>タグで1つ（SEOを意識した魅力的なタイトル）
- 見出し: <h2>, <h3>タグを適切に使用
- 本文: <p>タグで段落を分ける
- 文字数: 約2000〜2500文字

【補足ルール】
- 医学用語は使いつつも、一般読者に分かりやすく説明すること
- 「私の整体院に来られる患者さんも...」など、実体験を交えること
- 商品を押し売りせず、あくまで「選択肢の一つ」として紹介すること
- 最後に「まとめ」セクションを必ず入れること

---
上記の指示に従って、SEOに強い日本語のブログ記事をHTML形式で出力してください。
"""

    print("📝 Gemini APIで記事を生成中...")
    
    # まず利用可能なモデルを確認
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    list_response = requests.get(list_url)
    
    if list_response.status_code == 200:
        models = list_response.json().get("models", [])
        print("📋 利用可能なモデル一覧:")
        generate_models = []
        for m in models:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                model_name = m["name"].replace("models/", "")
                print(f"   - {model_name}")
                generate_models.append(model_name)
        
        # 優先順位でモデルを選択（Gemmaモデルも試す）
        preferred = ["gemma-3-27b-it", "gemma-3-12b-it", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
        selected_model = None
        for p in preferred:
            for gm in generate_models:
                if p in gm:
                    selected_model = gm
                    break
            if selected_model:
                break
        
        if not selected_model and generate_models:
            selected_model = generate_models[0]
        
        if not selected_model:
            raise Exception("利用可能なモデルが見つかりません")
        
        print(f"✅ 選択されたモデル: {selected_model}")
    else:
        print(f"モデル一覧取得失敗: {list_response.status_code} - {list_response.text}")
        selected_model = "gemini-1.5-flash"  # デフォルト
    
    # REST API を直接呼び出し
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }
    
    # リトライロジック（レート制限対応）
    import time
    max_retries = 3
    
    for attempt in range(max_retries):
        response = requests.post(api_url, json=payload)
        
        if response.status_code == 200:
            break
        elif response.status_code == 429:
            wait_time = 60  # 60秒待機
            print(f"⏳ レート制限に達しました。{wait_time}秒待機中... (試行 {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            raise Exception(f"Gemini API Error: {response.status_code}")
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code} - {response.text}")
        raise Exception(f"Gemini API Error: {response.status_code} - レート制限を超過しました。後でお試しください。")
    
    result = response.json()
    html_content = result["candidates"][0]["content"]["parts"][0]["text"]
    
    # HTMLからタイトルを抽出
    import re
    title_match = re.search(r"<h1>(.*?)</h1>", html_content, re.DOTALL)
    title = title_match.group(1).strip() if title_match else f"整体師が教える{product['name']}の選び方"
    
    # h1タグはWordPressが自動で付けるので削除
    html_content = re.sub(r"<h1>.*?</h1>", "", html_content, flags=re.DOTALL).strip()
    
    # コードブロックのマークダウン記法を削除（```html など）
    html_content = re.sub(r"```html\s*", "", html_content)
    html_content = re.sub(r"```\s*", "", html_content)
    
    print(f"✅ 記事生成完了: {title}")
    
    return {
        "title": title,
        "content": html_content
    }


def get_pexels_image(query: str) -> str:
    """
    Pexels APIで高品質な横長画像を取得する
    Returns: 画像URL
    """
    print(f"🖼️ Pexels APIで画像を検索中: {query}")
    
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": 10,
        "orientation": "landscape",
        "size": "large"
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get("photos"):
        raise Exception("Pexelsから画像を取得できませんでした")
    
    # ランダムに1枚選択
    photo = random.choice(data["photos"])
    image_url = photo["src"]["large2x"]
    
    print(f"✅ 画像取得完了: {image_url[:60]}...")
    
    return image_url


def download_image(image_url: str) -> bytes:
    """画像をダウンロードしてバイナリデータを返す"""
    response = requests.get(image_url)
    response.raise_for_status()
    return response.content


def upload_image_to_wp(image_data: bytes, filename: str) -> int:
    """
    WordPressに画像をアップロードする
    Returns: メディアID
    """
    print("📤 WordPressに画像をアップロード中...")
    
    url = f"{WP_URL}/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type": "image/jpeg"
    }
    
    response = requests.post(
        url,
        headers=headers,
        data=image_data,
        auth=(WP_USER, WP_APP_PASSWORD)
    )
    response.raise_for_status()
    
    media_id = response.json()["id"]
    print(f"✅ 画像アップロード完了: Media ID = {media_id}")
    
    return media_id


def add_affiliate_placeholder(content: str) -> str:
    """記事の最後にアフィリエイトリンク枠を追加する"""
    affiliate_box = """
<div style="background:#f9f9f9; padding:20px; border:2px solid #ff9900; text-align:center; margin-top:30px; border-radius:8px;">
<h3 style="color:#333; margin-top:0;">▼整体師おすすめのアイテム</h3>
<p style="color:#666;">（ここにA8.netのリンクを貼る）</p>
</div>
"""
    return content + affiliate_box


def post_to_wordpress(title: str, content: str, featured_media_id: int) -> dict:
    """
    WordPressに記事を下書き投稿する
    Returns: 投稿データ
    """
    print("📮 WordPressに記事を投稿中...")
    
    url = f"{WP_URL}/wp-json/wp/v2/posts"
    
    payload = {
        "title": title,
        "content": content,
        "status": "draft",  # 下書きとして投稿
        "featured_media": featured_media_id
    }
    
    response = requests.post(
        url,
        json=payload,
        auth=(WP_USER, WP_APP_PASSWORD)
    )
    response.raise_for_status()
    
    post_data = response.json()
    print(f"✅ 投稿完了: {post_data['link']}")
    print(f"   ステータス: {post_data['status']} (下書き)")
    
    return post_data


def main(request=None):
    """
    メイン処理
    Google Cloud Functions / GitHub Actions から呼び出される
    """
    print("=" * 50)
    print("🚀 SEOアフィリエイト記事 自動投稿システム 起動")
    print("=" * 50)
    
    try:
        # 1. 商材を選定
        product = select_product()
        
        # 2. Gemini APIで記事を生成
        article = generate_article(product)
        
        # 3. Pexels APIで画像を取得
        image_url = get_pexels_image(product["pexels_query"])
        image_data = download_image(image_url)
        
        # 4. WordPressに画像をアップロード
        filename = f"affiliate_{product['id']}_{random.randint(1000, 9999)}.jpg"
        media_id = upload_image_to_wp(image_data, filename)
        
        # 5. アフィリエイトリンク枠を追加
        content_with_affiliate = add_affiliate_placeholder(article["content"])
        
        # 6. WordPressに投稿
        post = post_to_wordpress(
            title=article["title"],
            content=content_with_affiliate,
            featured_media_id=media_id
        )
        
        print("=" * 50)
        print("🎉 処理完了！")
        print(f"   投稿ID: {post['id']}")
        print(f"   タイトル: {article['title']}")
        print("=" * 50)
        
        # Cloud Functions用の戻り値
        return {
            "success": True,
            "post_id": post["id"],
            "title": article["title"],
            "product": product["name"]
        }
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        raise


# ローカル実行用
if __name__ == "__main__":
    main()

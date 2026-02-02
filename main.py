"""
SEOアフィリエイト特化型 WordPress自動投稿システム
- 整体師視点のセールスライティング記事を自動生成
- Pexels APIで高品質画像を取得
- WordPressに下書き投稿
"""

import os
import random
import requests
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
# 1. アフィリエイト商材リスト
# ============================
PRODUCTS = [
    {
        "id": "A",
        "name": "高級マットレス",
        "target": "睡眠の質、朝の腰痛",
        "keywords": ["マットレス", "腰痛", "睡眠"],
        "pexels_query": "sleeping bedroom mattress"
    },
    {
        "id": "B",
        "name": "ワークチェア/ゲーミングチェア",
        "target": "在宅ワークの腰痛、坐骨神経痛",
        "keywords": ["デスクチェア", "在宅ワーク", "腰痛"],
        "pexels_query": "office chair desk work"
    },
    {
        "id": "C",
        "name": "安眠枕/オーダーメイド枕",
        "target": "首の痛み、ストレートネック",
        "keywords": ["枕", "首の痛み", "ストレートネック"],
        "pexels_query": "pillow sleeping neck"
    }
]


def select_product():
    """商材をランダムに選定する"""
    product = random.choice(PRODUCTS)
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
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    
    html_content = response.text
    
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

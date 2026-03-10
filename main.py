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
RAKUTEN_APP_ID = os.environ.get("RAKUTEN_APP_ID")
RAKUTEN_AFFILIATE_ID = os.environ.get("RAKUTEN_AFFILIATE_ID")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# ==========================================
# 1. 曜日別テーマ設定
# ==========================================
DAILY_THEMES = {
    0: { "category": "睡眠・寝具", "products": [
        {"id": "MON-1", "name": "高級マットレス", "target": "睡眠の質向上、朝の腰痛", "keywords": ["マットレス", "腰痛", "睡眠改善"], "pexels_query": "sleeping bedroom mattress", "problem_query": "back pain tired morning"},
        {"id": "MON-2", "name": "安眠枕", "target": "首の痛み、ストレートネック", "keywords": ["枕", "首こり", "ストレートネック"], "pexels_query": "pillow sleeping comfort", "problem_query": "neck pain stress headache"}
    ]},
    1: { "category": "デスクワーク", "products": [
        {"id": "TUE-1", "name": "ワークチェア", "target": "在宅ワークの腰痛、坐骨神経痛", "keywords": ["デスクチェア", "腰痛", "テレワーク"], "pexels_query": "office chair desk work", "problem_query": "back pain office sitting"},
        {"id": "TUE-2", "name": "姿勢矯正クッション", "target": "猫背、骨盤の歪み", "keywords": ["クッション", "姿勢矯正", "骨盤ケア"], "pexels_query": "cushion office ergonomic", "problem_query": "bad posture slouching desk"}
    ]},
    2: { "category": "運動・ストレッチ", "products": [
        {"id": "WED-1", "name": "ストレッチポール", "target": "背中の張り、肩こり", "keywords": ["ストレッチポール", "肩こり", "筋膜リリース"], "pexels_query": "foam roller stretching", "problem_query": "shoulder pain stiff muscle"},
        {"id": "WED-2", "name": "ヨガマット", "target": "自宅での運動習慣", "keywords": ["ヨガマット", "宅トレ", "運動不足"], "pexels_query": "yoga mat exercise", "problem_query": "sedentary lifestyle tired"}
    ]},
    3: { "category": "栄養・健康食", "products": [
        {"id": "THU-1", "name": "プロテイン", "target": "筋肉維持、疲労回復", "keywords": ["プロテイン", "疲労回復", "栄養補給"], "pexels_query": "protein powder fitness", "problem_query": "tired exhausted fatigue"},
        {"id": "THU-2", "name": "関節サプリ", "target": "膝の違和感、軟骨ケア", "keywords": ["サプリメント", "膝の痛み", "関節ケア"], "pexels_query": "supplements health", "problem_query": "knee pain walking stairs"}
    ]},
    4: { "category": "休息・入浴", "products": [
        {"id": "FRI-1", "name": "リカバリーウェア", "target": "着るだけで疲労回復", "keywords": ["リカバリーウェア", "睡眠の質", "疲労回復"], "pexels_query": "relaxing sleep recovery", "problem_query": "exhausted tired stress"},
        {"id": "FRI-2", "name": "入浴剤", "target": "冷え性、深部体温", "keywords": ["入浴剤", "温活", "リラックス"], "pexels_query": "bath relaxation spa", "problem_query": "cold feet stress tension"}
    ]},
    5: { "category": "足腰ケア", "products": [
        {"id": "SAT-1", "name": "膝サポーター", "target": "階段の上り下りが辛い", "keywords": ["サポーター", "膝痛", "ウォーキング"], "pexels_query": "knee support brace", "problem_query": "knee pain elderly walking"},
        {"id": "SAT-2", "name": "インソール", "target": "立ち仕事の足の疲れ", "keywords": ["インソール", "足の疲れ", "扁平足"], "pexels_query": "shoe insole feet", "problem_query": "foot pain standing work"}
    ]},
    6: { "category": "健康コラム", "products": [
        {"id": "SUN-1", "name": "健康習慣まとめ", "target": "1週間の振り返り", "keywords": ["健康習慣", "生活改善", "予防医学"], "pexels_query": "healthy lifestyle wellness", "problem_query": "unhealthy lifestyle stress"},
        {"id": "SUN-2", "name": "セルフケア総集編", "target": "自宅でできるケア", "keywords": ["セルフケア", "マッサージ", "ストレッチ"], "pexels_query": "self care massage", "problem_query": "body pain tension stress"}
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
# 2. 楽天アフィリエイト商品検索
# ==========================================
def search_rakuten_product(keyword):
    """楽天市場から商品を検索してアフィリエイトリンクを取得"""
    if not RAKUTEN_APP_ID or not RAKUTEN_AFFILIATE_ID:
        print("   ⚠️ 楽天APIキーが設定されていません")
        return None
    
    print(f"🛒 楽天で商品検索中: {keyword}")
    
    try:
        url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
        params = {
            "applicationId": RAKUTEN_APP_ID,
            "affiliateId": RAKUTEN_AFFILIATE_ID,
            "keyword": keyword,
            "hits": 3,  # 上位3件を取得
            "sort": "+reviewCount",  # レビュー数順
            "imageFlag": 1
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("Items", [])
            
            if items:
                # 最もレビューが多い商品を選択
                best_item = items[0]["Item"]
                result = {
                    "name": best_item["itemName"][:50],
                    "price": best_item["itemPrice"],
                    "url": best_item.get("affiliateUrl") or best_item["itemUrl"],
                    "image": best_item["mediumImageUrls"][0]["imageUrl"] if best_item.get("mediumImageUrls") else None,
                    "shop": best_item["shopName"],
                    "review_count": best_item.get("reviewCount", 0),
                    "item_code": best_item.get("itemCode", "")
                }
                print(f"   ✅ 商品発見: {result['name'][:30]}... ({result['price']:,}円)")
                return result
            else:
                print("   ⚠️ 商品が見つかりませんでした")
        else:
            print(f"   ⚠️ 楽天API エラー: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 楽天検索エラー: {e}")
    
    return None

def create_pochipp_product(rakuten_product):
    """楽天商品をポチップに登録してショートコードIDを取得"""
    print(f"📦 ポチップに商品を登録中...")
    
    try:
        auth = (WP_USER, WP_APP_PASSWORD)
        
        # ポチップのカスタム投稿タイプで商品を作成
        pochipp_data = {
            "title": rakuten_product["name"],
            "status": "publish",
            "meta": {
                "pochipp_pid_rakuten": rakuten_product.get("item_code", ""),
                "pochipp_title_rakuten": rakuten_product["name"],
                "pochipp_price_rakuten": str(rakuten_product["price"]),
                "pochipp_url_rakuten": rakuten_product["url"],
                "pochipp_img_rakuten": rakuten_product.get("image", ""),
                "pochipp_img": rakuten_product.get("image", ""),
                "pochipp_shop_rakuten": rakuten_product.get("shop", ""),
            }
        }
        
        # ポチップのREST APIエンドポイント
        res = requests.post(
            f"{WP_URL}/wp-json/wp/v2/pochipps",
            json=pochipp_data,
            auth=auth
        )
        
        if res.status_code == 201:
            pochipp_id = res.json().get("id")
            print(f"   ✅ ポチップ登録成功: ID={pochipp_id}")
            return pochipp_id
        else:
            print(f"   ⚠️ ポチップ登録失敗: {res.status_code}")
            print(f"   レスポンス: {res.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ ポチップエラー: {e}")
        return None

# ==========================================
# 3. 記事作成
# ==========================================
def generate_article(product):
    print("📝 Gemini APIでSEO記事を執筆中...")
    
    prompt = f"""
あなたは「デスクワーク改善室　所長M」です。
実務歴8年の整体師・柔道整復師として、延べ1万人以上の施術経験があります。
解剖学・運動学の専門知識を活かし、デスクワーカーの体の悩みを解決するブログを書いています。

【商品】{product['name']}
【ターゲットの悩み】{product['target']}

【記事の構成（この順番を厳守）】
1. 悩みへの共感（読者の「あるある」を描写し、共感を得る）
2. 原因の解説（解剖学・骨格・筋肉の仕組みを使って専門的に説明する）
   - 必ず具体的な筋肉名（例：脊柱起立筋、大腰筋、僧帽筋など）を使うこと
   - 骨格や関節の構造（例：仙腸関節、頸椎、腰椎のカーブなど）に言及すること
   - なぜその悩みが起きるのか、体の仕組みから論理的に説明すること
3. 解決策の提示（商品がなぜ効果的なのか、体の仕組みと結びつけて説明する）
4. まとめ（所長Mからの一言アドバイス）

【文体ルール】
- 語尾は「〜です」「〜ます」と専門家として言い切ること。「〜だと思います」「〜かもしれません」は禁止
- 「私の整体院に来る患者さんでも〜」のような実体験を交えること
- ネットの情報のまとめではなく、専門家としてのオリジナルの見解を述べること
- 記事内で名乗る場合は「所長M」と名乗ること

【文字数】
3,000文字以上。各セクションを充実させて、読者が「専門家の記事だ」と感じる深い内容にすること。

【絶対に守るルール】
- 「SEOタイトル」「メタディスクリプション」などの見出しラベルは絶対に書かない
- 説明文や前置きは一切不要。いきなり出力する
- エスケープ文字は使わない
- マークダウン記法は使わない

【出力フォーマット】
以下の3つを [[DELIMITER]] で区切って出力してください。

読者の心に響く魅力的なタイトル（32文字以内）
[[DELIMITER]]
記事の要約文（120文字程度）
[[DELIMITER]]
記事本文（HTML形式）
- <h2>で見出しを4つ以上作成すること
- <p>で段落を作成
- 記事中盤の商品紹介セクションに [[AFFILIATE_AREA]] を必ず1つ配置
- <strong>タグで重要な専門用語を強調すること
"""

    try:
        response = model.generate_content(prompt)
        parts = response.text.split("[[DELIMITER]]")
        
        if len(parts) < 3:
            print(f"⚠️ 記事パース失敗: パーツ数={len(parts)}")
            return None

        # クリーンアップ処理
        def clean_text(text, is_html=False):
            text = text.strip()
            # リテラルな\nや¥nを削除（全パターン対応）
            text = re.sub(r'\\n', ' ', text)
            text = re.sub(r'￥n', ' ', text)
            text = text.replace('¥n', ' ').replace('¥t', ' ')
            # マークダウン記号を削除
            text = re.sub(r'^#{1,3}\s*', '', text, flags=re.MULTILINE)
            # 余計なラベルを削除
            for label in ['SEOタイトル', 'メタディスクリプション', '記事本文', '1.', '2.', '3.']:
                text = text.replace(f'{label}:', '').replace(f'{label}：', '')
            # コードブロックを削除
            text = text.replace('```html', '').replace('```', '')
            if not is_html:
                # タイトル・メタはシングルライン化
                text = text.replace('\n', ' ').replace('\r', ' ')
                text = re.sub(r'\s+', ' ', text)
            return text.strip()

        return {
            "seo_title": clean_text(parts[0]),
            "meta_desc": clean_text(parts[1]),
            "content": clean_text(parts[2], is_html=True)
        }
    except Exception as e:
        print(f"❌ Geminiエラー: {e}")
        return None

# ==========================================
# 3. カテゴリ・タグ・画像処理
# ==========================================
def get_or_create_term(endpoint, name):
    """カテゴリやタグの名前からIDを取得（なければ作成）"""
    auth = (WP_USER, WP_APP_PASSWORD)
    
    print(f"   🔍 {endpoint}を検索中: {name}")
    
    # 1. 検索
    try:
        search_url = f"{WP_URL}/wp-json/wp/v2/{endpoint}?search={name}"
        res = requests.get(search_url, auth=auth)
        if res.status_code == 200 and len(res.json()) > 0:
            for item in res.json():
                if item['name'] == name:
                    print(f"   ✅ 既存{endpoint}を発見: ID={item['id']}")
                    return item['id']
    except Exception as e:
        print(f"   ⚠️ 検索エラー: {e}")

    # 2. 作成
    print(f"   📝 新規{endpoint}を作成中: {name}")
    try:
        create_url = f"{WP_URL}/wp-json/wp/v2/{endpoint}"
        res = requests.post(create_url, json={"name": name}, auth=auth)
        if res.status_code == 201:
            new_id = res.json()['id']
            print(f"   ✅ 作成成功: ID={new_id}")
            return new_id
        else:
            print(f"   ❌ 作成失敗: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"   ❌ 作成エラー: {e}")
    
    return None

def get_tag_ids(keywords):
    """キーワードリストからタグIDのリストを取得"""
    print(f"🏷️ タグ処理開始: {keywords}")
    tag_ids = []
    for kw in keywords:
        tid = get_or_create_term("tags", kw)
        if tid:
            tag_ids.append(tid)
    print(f"   → 取得したタグID: {tag_ids}")
    return tag_ids

def get_pexels_images(query, count=3):
    """Pexelsから複数の画像URLを取得"""
    print(f"🖼️ 画像検索中: {query} ({count}枚)")
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={count}&orientation=landscape&size=large"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200 and res.json().get('photos'):
            photos = res.json()['photos']
            urls = [p['src']['large2x'] for p in photos]
            print(f"   ✅ {len(urls)}枚の画像を取得")
            return urls
    except Exception as e:
        print(f"   ⚠️ 画像エラー: {e}")
    return []

def upload_image_to_wp(image_url, alt_text):
    if not image_url:
        return None
    print(f"📤 画像アップロード中...")
    try:
        img_data = requests.get(image_url).content
        filename = f"wp_auto_{int(time.time())}.jpg"
        media_url = f"{WP_URL}/wp-json/wp/v2/media"
        headers = {"Content-Type": "image/jpeg", "Content-Disposition": f'attachment; filename="{filename}"'}
        auth = (WP_USER, WP_APP_PASSWORD)
        res = requests.post(media_url, headers=headers, data=img_data, auth=auth)
        if res.status_code == 201:
            media_id = res.json()['id']
            # Alt テキスト設定
            requests.post(f"{WP_URL}/wp-json/wp/v2/media/{media_id}", json={"alt_text": alt_text}, auth=auth)
            print(f"   ✅ アップロード成功: ID={media_id}")
            return media_id
        else:
            print(f"   ❌ アップロード失敗: {res.status_code}")
    except Exception as e:
        print(f"   ❌ アップロードエラー: {e}")
    return None

def post_to_wordpress(article_data, media_id, category_id, tag_ids):
    print("🚀 WordPressへ投稿処理開始...")
    post_url = f"{WP_URL}/wp-json/wp/v2/posts"
    
    # 翌日19:00 JSTに予約
    jst = timezone(timedelta(hours=9))
    tomorrow_7pm = datetime.now(jst).replace(hour=19, minute=0, second=0, microsecond=0) + timedelta(days=1)
    schedule_date = tomorrow_7pm.strftime("%Y-%m-%dT%H:%M:%S")
    
    print(f"   📅 予約投稿: {tomorrow_7pm.strftime('%Y年%m月%d日 %H:%M')} JST")
    
    payload = {
        "title": article_data['seo_title'],
        "content": article_data['content'],
        "status": "future",
        "date": schedule_date,
        "featured_media": media_id if media_id else 0,
        "categories": [category_id] if category_id else [],
        "tags": tag_ids if tag_ids else [],
        "excerpt": article_data['meta_desc'],
    }
    
    print(f"   📋 投稿データ: カテゴリID={category_id}, タグ数={len(tag_ids)}")
    
    res = requests.post(post_url, json=payload, auth=(WP_USER, WP_APP_PASSWORD))
    if res.status_code == 201:
        post_data = res.json()
        print(f"🎉 予約投稿成功！")
        print(f"   投稿URL: {post_data.get('link')}")
        print(f"   投稿ID: {post_data.get('id')}")
        print(f"   公開予定: {tomorrow_7pm.strftime('%Y/%m/%d %H:%M')} JST")
        print(f"   カテゴリ: {post_data.get('categories')}")
        print(f"   タグ: {post_data.get('tags')}")
    else:
        print(f"❌ 投稿失敗: {res.status_code} - {res.text}")

# ==========================================
# 4. メイン処理
# ==========================================
def main():
    print("=" * 50)
    print("🚀 自動投稿システム v2.0 (カテゴリ・タグ自動設定)")
    print("=" * 50)
    
    # 1. ネタ決め
    product, category_name = select_product()
    
    # 2. カテゴリID取得（なければ作る）
    print(f"\n📂 カテゴリ処理: {category_name}")
    category_id = get_or_create_term("categories", category_name)
    
    # 3. タグID取得（なければ作る）
    print(f"\n🏷️ タグ処理")
    tag_ids = get_tag_ids(product['keywords'])
    
    # 4. 記事生成
    print(f"\n📝 記事生成")
    article = generate_article(product)
    
    if article:
        # 5. 複数画像取得・アップロード（危機感 + 解決策のバランス）
        print(f"\n🖼️ 画像処理（問題提起 + 解決策）")
        
        # 解決策画像（アイキャッチ + 本文用1枚）
        solution_urls = get_pexels_images(product['pexels_query'], count=2)
        
        # 問題・危機感画像（本文用1枚）
        problem_query = product.get('problem_query', product['pexels_query'])
        problem_urls = get_pexels_images(problem_query, count=1)
        
        # アイキャッチ用（解決策画像の1枚目）
        featured_media_id = None
        if solution_urls:
            featured_media_id = upload_image_to_wp(solution_urls[0], f"{product['name']} イメージ")
        
        # 本文挿入用の画像をアップロード
        # 順序: 危機感画像 → 解決策画像（問題→解決の流れ）
        content_images = problem_urls + solution_urls[1:]
        inserted_images = []
        
        for i, url in enumerate(content_images):
            label = "問題" if i == 0 else "解決策"
            mid = upload_image_to_wp(url, f"{product['name']} {label}画像")
            if mid:
                try:
                    auth = (WP_USER, WP_APP_PASSWORD)
                    res = requests.get(f"{WP_URL}/wp-json/wp/v2/media/{mid}", auth=auth)
                    if res.status_code == 200:
                        inserted_images.append(res.json().get('source_url'))
                except:
                    pass
        
        print(f"   📸 本文挿入用画像: {len(inserted_images)}枚")

        # 6. 本文加工（画像挿入 + 広告枠）
        content = article['content']
        
        # h2タグの後に画像を挿入
        if inserted_images:
            h2_pattern = r'(</h2>)'
            h2_matches = list(re.finditer(h2_pattern, content, re.IGNORECASE))
            
            # 画像を均等に挿入（最大2箇所）
            insert_positions = []
            if len(h2_matches) >= 2:
                insert_positions = [h2_matches[0].end(), h2_matches[1].end()]
            elif len(h2_matches) == 1:
                insert_positions = [h2_matches[0].end()]
            
            # 逆順で挿入（位置がずれないように）
            for idx, pos in enumerate(reversed(insert_positions)):
                img_idx = len(insert_positions) - 1 - idx
                if img_idx < len(inserted_images):
                    img_html = f'<figure style="margin: 30px 0; text-align: center;"><img src="{inserted_images[img_idx]}" alt="{product["name"]}関連画像" style="max-width: 100%; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08);"/></figure>'
                    content = content[:pos] + img_html + content[pos:]
            
            print(f"   ✅ {min(len(insert_positions), len(inserted_images))}箇所に画像を挿入")
        
        # 楽天商品検索とポチップ自動登録
        print(f"\n🛒 アフィリエイト処理（ポチップ）")
        search_keyword = f"{product['name']} {product['keywords'][0]}" if product.get('keywords') else product['name']
        rakuten_product = search_rakuten_product(search_keyword)
        
        affiliate_box = ""
        if rakuten_product:
            # ポチップに商品を登録
            pochipp_id = create_pochipp_product(rakuten_product)
            
            if pochipp_id:
                # ポチップショートコードを挿入
                affiliate_box = f'\n<!-- wp:pochipp/linkbox {{"pochippId":{pochipp_id}}} -->\n[pochipp id="{pochipp_id}"]\n<!-- /wp:pochipp/linkbox -->\n'
                print(f"   ✅ ポチップショートコード挿入: [pochipp id=\"{pochipp_id}\"]")
            else:
                # ポチップ登録失敗時はフォールバック
                affiliate_box = f"""
<div style="margin: 40px 0; padding: 30px; background: linear-gradient(135deg, #faf8f5 0%, #f5f0e8 100%); border: 2px solid #c9b99a; border-radius: 15px; text-align: center;">
    <h3 style="margin-top:0; color:#6b8e6b;">🌿 所長Mおすすめの{product['name']}</h3>
    <a href="{rakuten_product['url']}" target="_blank" rel="nofollow sponsored" style="display: inline-block; background: linear-gradient(135deg, #bf0000 0%, #e60033 100%); color: #fff; padding: 12px 25px; border-radius: 25px; text-decoration: none; font-weight: bold;">楽天市場で詳細を見る</a>
</div>
"""
        else:
            # 商品が見つからない場合
            affiliate_box = f"""
<div style="margin: 40px 0; padding: 30px; background: linear-gradient(135deg, #faf8f5 0%, #f5f0e8 100%); border: 2px solid #c9b99a; border-radius: 15px; text-align: center;">
    <h3 style="margin-top:0; color:#6b8e6b;">🌿 所長Mおすすめの{product['name']}</h3>
    <a href="https://search.rakuten.co.jp/search/mall/{product['name']}/" target="_blank" rel="nofollow" style="display: inline-block; background: linear-gradient(135deg, #bf0000 0%, #e60033 100%); color: #fff; padding: 12px 25px; border-radius: 25px; text-decoration: none; font-weight: bold;">楽天市場で探す</a>
</div>
"""
        
        if "[[AFFILIATE_AREA]]" in content:
            content = content.replace("[[AFFILIATE_AREA]]", affiliate_box)
        else:
            content += affiliate_box

        article['content'] = content

        # 7. 投稿
        print(f"\n📮 WordPress投稿")
        post_to_wordpress(article, featured_media_id, category_id, tag_ids)

    else:
        print("❌ 記事生成失敗")
    
    print("\n" + "=" * 50)
    print("✅ 処理完了")
    print("=" * 50)

if __name__ == "__main__":
    main()
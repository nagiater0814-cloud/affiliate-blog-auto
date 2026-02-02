# SEOアフィリエイト特化型 WordPress自動投稿システム

整体師視点のセールスライティング記事を自動生成し、WordPressに投稿するシステムです。

## 🎯 機能概要

1. **商材のランダム選定**: 高級マットレス、ワークチェア、安眠枕から自動選択
2. **AI記事生成**: Gemini APIで整体師視点の専門的な記事を生成
3. **高品質画像取得**: Pexels APIで記事にマッチする画像を取得
4. **WordPress投稿**: 下書きとして自動投稿（アイキャッチ画像付き）

## 📁 ファイル構成

```
post_wp.py/
├── main.py              # メインスクリプト
├── requirements.txt     # 依存パッケージ
├── .env.example         # 環境変数テンプレート
└── README.md           # このファイル
```

## 🚀 セットアップ手順

### 1. 必要なAPIキーの取得

| サービス | 取得先 |
|---------|--------|
| **Gemini API** | https://aistudio.google.com/apikey |
| **Pexels API** | https://www.pexels.com/api/ |
| **WordPress アプリパスワード** | WordPress管理画面 → ユーザー → プロフィール |

### 2. 環境変数の設定

```bash
# テンプレートをコピー
cp .env.example .env

# .envファイルを編集して実際の値を入力
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. ローカルで実行

```bash
python main.py
```

---

## ☁️ デプロイ方法（無料枠）

### **推奨: GitHub Actions（完全無料）**

GitHub Actionsは月2,000分の無料枠があり、週1回の実行なら余裕で無料です。

#### 手順

1. **GitHubリポジトリを作成**

2. **Secretsを設定**
   - リポジトリ → Settings → Secrets and variables → Actions → New repository secret
   - 以下を登録:
     - `WP_URL`
     - `WP_USER`
     - `WP_APP_PASSWORD`
     - `PEXELS_API_KEY`
     - `GEMINI_API_KEY`

3. **ワークフローファイルを作成**

   `.github/workflows/post-article.yml`:

   ```yaml
   name: Auto Post Article

   on:
     schedule:
       # 毎週月曜日 午前9時（日本時間）に実行
       # UTC+9 なので UTC 0:00 = JST 9:00
       - cron: '0 0 * * 1'
     workflow_dispatch:  # 手動実行も可能

   jobs:
     post:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Set up Python
           uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         
         - name: Install dependencies
           run: pip install -r requirements.txt
         
         - name: Run script
           env:
             WP_URL: ${{ secrets.WP_URL }}
             WP_USER: ${{ secrets.WP_USER }}
             WP_APP_PASSWORD: ${{ secrets.WP_APP_PASSWORD }}
             PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}
             GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
           run: python main.py
   ```

4. **コミット＆プッシュ**

   ```bash
   git add .
   git commit -m "Add auto post system"
   git push
   ```

---

### **代替: Google Cloud Functions（月200万回まで無料）**

#### 手順

1. **Google Cloudプロジェクトを作成**

2. **Cloud Functionsにデプロイ**

   ```bash
   gcloud functions deploy auto-post-article \
     --gen2 \
     --runtime python311 \
     --trigger-http \
     --allow-unauthenticated \
     --entry-point main \
     --set-env-vars WP_URL=xxx,WP_USER=xxx,WP_APP_PASSWORD=xxx,PEXELS_API_KEY=xxx,GEMINI_API_KEY=xxx \
     --region asia-northeast1
   ```

3. **Cloud Schedulerで定期実行**

   ```bash
   gcloud scheduler jobs create http auto-post-job \
     --location asia-northeast1 \
     --schedule "0 9 * * 1" \
     --time-zone "Asia/Tokyo" \
     --uri "https://YOUR_FUNCTION_URL" \
     --http-method GET
   ```

---

## 💰 コスト比較

| サービス | 無料枠 | 週1実行時のコスト |
|---------|--------|------------------|
| **GitHub Actions** | 月2,000分 | **$0（完全無料）** |
| **Cloud Functions** | 月200万回 | $0（無料枠内） |
| **Cloud Scheduler** | 月3ジョブ無料 | $0（無料枠内） |

**結論**: GitHub Actionsが最もシンプルで完全無料なのでおすすめです。

---

## 🔧 カスタマイズ

### 商材を追加する

`main.py` の `PRODUCTS` リストに追加:

```python
{
    "id": "D",
    "name": "新商品名",
    "target": "ターゲットの悩み",
    "keywords": ["キーワード1", "キーワード2"],
    "pexels_query": "english search query"
}
```

### 投稿ステータスを変更する

下書き以外で投稿したい場合は `post_to_wordpress` 関数の `status` を変更:

```python
"status": "publish"  # 即時公開
"status": "pending"  # レビュー待ち
```

---

## ⚠️ 注意事項

- アフィリエイトリンクは手動で設置が必要です（A8.netなど）
- 生成された記事は投稿前に内容を確認することをおすすめします
- WordPressのREST APIを有効にしてください
- 画像のライセンスはPexelsの規約に従います

---

## 📝 ライセンス

MIT License

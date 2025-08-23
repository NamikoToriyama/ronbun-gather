// This md is used for AI
# 論文収集システム TODO

## 完了済み
- [x] プロジェクト構成の確認と必要な依存関係の調査
- [x] プロジェクト基本セットアップ
  - [x] 仮想環境構築 
  - [x] requirements.txt作成
  - [x] README.md作成（セットアップ手順）
  - [x] .gitignore作成
  - [x] .env.example作成
- [x] LINE Messaging API連携の実装
  - [x] line-bot-sdk導入
  - [x] LINEメッセージ送信機能実装 (line_notifier.py)
  - [x] テストメッセージ送信確認
- [x] Notion API連携の実装
  - [x] notion-client導入済み
  - [x] Notionデータベース作成と設定
  - [x] 論文情報保存機能実装 (poc/updated_notion_poc.py)
  - [x] abstractをページコンテンツに追加機能
  - [x] テストページ作成確認
- [x] 論文検索機能の実装
  - [x] arXiv API検索機能実装 (arxiv_scraper.py)
  - [x] Google Scholar検索機能実装 (paper_scraper.py)
- [x] DeepL翻訳機能の実装
  - [x] DeepL API導入 (deepl==1.18.0)
  - [x] 英語abstractの日本語翻訳機能
  - [x] arXiv + DeepL連携POC作成 (poc/arxiv_deepl_poc.py)
  - [x] 翻訳テスト実行確認

## 完了済み（追加）
- [x] 全体統合（メイン実行システム作成）
  - [x] API分離（deepl_translator.py, line_notifier.py, notion_saver.py）
  - [x] main.py統合システム完成
  - [x] 検索→翻訳→Notion→LINE の全連携
- [x] 重複チェック機能の実装
  - [x] Notionデータベースから既存URL取得
  - [x] 重複論文の自動除外
- [x] 関連性フィルタリング機能
  - [x] 台風・気象関連キーワードチェック
  - [x] 検索精度向上（関連性順ソート）
- [x] 新規論文上限制御
  - [x] 1日最大2件処理で自動終了
  - [x] 効率的な実行制御

## 未着手
- [ ] 定期実行ジョブの設定（cron）
- [ ] エラーハンドリングとログ機能の強化

## 詳細タスク

## 現在のシステム状況

### ✅ 完全実装済み機能
- **arXiv検索**: 関連性順ソート、カテゴリ指定、重複チェック
- **DeepL翻訳**: Abstract全文翻訳、文字数制限管理
- **LINE通知**: 基本情報+翻訳要約の2段階送信
- **Notion保存**: 英語論文+DeepL翻訳+図表、UNREAD設定
- **重複除外**: URL基準の重複チェック
- **関連性フィルタ**: 台風・気象関連論文のみ抽出
- **上限制御**: 1日最大2件で自動終了

### 📋 検索キーワード（現在設定）
- typhoon intensity prediction
- tropical cyclone track forecast  
- hurricane eye wall replacement
- typhoon landfall prediction

### 🔧 設定パラメータ
- MAX_NEW_PAPERS_PER_DAY = 2
- PAPERS_PER_KEYWORD = 1
- MESSAGE_INTERVAL = 2秒
- QUERY_INTERVAL = 5秒

### 📊 実行フロー
1. Notion既存URL取得 → 2. arXiv検索（関連性順） → 3. 関連性+重複フィルタ → 4. DeepL翻訳 → 5. LINE通知 → 6. Notion保存 → 7. 上限チェック → 8. 終了判定

### 🚀 次のステップ
- [ ] 定期実行設定（cron）
- [ ] エラーハンドリング強化
- [ ] ログ機能追加

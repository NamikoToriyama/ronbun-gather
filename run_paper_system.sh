#!/bin/bash

# 論文収集システム用cronジョブスクリプト
# 日次実行用

# ログファイルの設定
LOG_DIR="/Users/torichan/pg/ronbun-app/logs"
LOG_FILE="$LOG_DIR/paper_system_$(date +%Y%m%d).log"

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# タイムスタンプ付きログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting Paper Collection System"

# プロジェクトディレクトリに移動
cd /Users/torichan/pg/ronbun-app

# 仮想環境をアクティベート
source venv/bin/activate

# 環境変数ファイルの存在確認
if [ ! -f .env ]; then
    log "❌ Error: .env file not found"
    exit 1
fi

# 必要なAPIキーの存在確認
if ! grep -q "DEEPL_API_KEY=" .env || ! grep -q "LINE_CHANNEL_ACCESS_TOKEN=" .env; then
    log "❌ Error: Required API keys not found in .env"
    exit 1
fi

log "📋 Environment check passed"

# Python依存関係の確認
pip list | grep -E "(deepl|line-bot-sdk|notion-client|arxiv)" > /dev/null
if [ $? -ne 0 ]; then
    log "⚠️ Installing missing dependencies"
    pip install -r requirements.txt
fi

# メインスクリプト実行
log "🔍 Running paper collection..."
python main.py 2>&1 | tee -a "$LOG_FILE"

# 実行結果の確認
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    log "✅ Paper collection completed successfully"
else
    log "❌ Paper collection failed with exit code ${PIPESTATUS[0]}"
fi

# 古いログファイルの削除（7日より古いもの）
find "$LOG_DIR" -name "paper_system_*.log" -mtime +7 -delete

log "🏁 Paper Collection System finished"
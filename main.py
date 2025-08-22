import time
from deepl_translator import DeepLTranslator
from arxiv_scraper import ArxivScraper
from line_notifier import LineNotifier
from notion_saver import NotionSaver

# ========================================
# 設定
# ========================================

# 検索キーワード（関心のある研究分野を設定）
SEARCH_KEYWORDS = [
    "typhoon intensity prediction",
    "tropical cyclone track forecast", 
    "hurricane eye wall replacement",
    "typhoon landfall prediction",
]

# 各キーワードで取得する論文数
PAPERS_PER_KEYWORD = 1

# 1日に処理する新規論文の上限数（この数に達したら終了）
MAX_NEW_PAPERS_PER_DAY = 2

# メッセージ間の待機時間（秒）
MESSAGE_INTERVAL = 2
QUERY_INTERVAL = 5

class PaperNotificationSystem:
    def __init__(self):
        # 各APIクライアントを初期化
        self.deepl = DeepLTranslator()
        self.arxiv = ArxivScraper()
        self.line = LineNotifier()
        self.notion = NotionSaver()
        
        # 既存のURLを取得（重複チェック用）
        self.existing_urls = self.notion.get_existing_urls() if self.notion.is_enabled() else set()
        
        # 処理済み新規論文数をカウント
        self.processed_new_papers = 0
        
        print("🚀 Paper Notification System initialized")
    
    def is_relevant_paper(self, paper, query):
        """論文がクエリに関連しているかチェック"""
        # 関連キーワード（台風・熱帯低気圧関連）
        typhoon_keywords = [
            'typhoon', 'tropical cyclone', 'hurricane', 'cyclone',
            'storm', 'weather forecasting', 'meteorology', 'atmospheric',
            'precipitation', 'wind', 'satellite', 'climate', 'prediction',
            '台風', '熱帯低気圧', '気象', '予報', '予測'
        ]
        
        # タイトルと要約を結合してチェック
        text_to_check = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
        
        # クエリのキーワードが含まれているかチェック
        query_words = query.lower().split()
        query_match = any(word in text_to_check for word in query_words)
        
        # 台風関連キーワードが含まれているかチェック
        keyword_match = any(keyword.lower() in text_to_check for keyword in typhoon_keywords)
        
        return query_match or keyword_match
    
    def filter_relevant_papers(self, papers, query):
        """関連性の高い論文のみフィルタリング"""
        relevant_papers = []
        
        for paper in papers:
            # 関連性チェック
            if not self.is_relevant_paper(paper, query):
                print(f"❌ Not relevant: {paper['title'][:60]}...")
                print(f"   Categories: {paper.get('categories', [])}")
                continue
            
            # 重複チェック
            paper_url = paper.get('pdf_url') or paper.get('url')
            if self.notion.is_duplicate(paper_url, self.existing_urls):
                print(f"🔄 Duplicate (skipping): {paper['title'][:60]}...")
                print(f"   URL: {paper_url}")
                continue
            
            # 関連性があり、重複でない論文のみ追加
            relevant_papers.append(paper)
            print(f"✅ New relevant paper: {paper['title'][:60]}...")
        
        return relevant_papers
    
    def process_single_paper(self, paper, paper_num, total_papers):
        """単一の論文を処理（翻訳・LINE・Notion）"""
        print(f"\n📄 Processing paper {paper_num}/{total_papers}: {paper['title'][:50]}...")
        
        # DeepL使用状況確認
        usage = self.deepl.get_usage()
        remaining = usage['remaining']
        
        # Abstract翻訳
        abstract_chars = len(paper.get('abstract', ''))
        if remaining >= abstract_chars:
            print(f"🔄 Translating abstract ({abstract_chars} chars)...")
            translated = self.deepl.translate_abstract(paper['abstract'])
            if translated:
                paper['translated_abstract'] = translated
                print(f"✅ Translation completed")
            else:
                print(f"❌ Translation failed")
        else:
            print(f"⚠️ Skipping translation (insufficient quota: need {abstract_chars}, have {remaining})")
            paper['translated_abstract'] = None
        
        # LINEに送信
        # 1つ目のメッセージ（基本情報）
        basic_message = self.line.format_basic_info_message(paper, paper_num, total_papers)
        self.line.send_message(basic_message)
        time.sleep(MESSAGE_INTERVAL)
        
        # 2つ目のメッセージ（翻訳した要約）
        abstract_message = self.line.format_abstract_message(paper)
        self.line.send_message(abstract_message)
        time.sleep(MESSAGE_INTERVAL)
        
        # Notionに保存
        if self.notion.is_enabled():
            notion_page = self.notion.save_paper(paper)
            if notion_page:
                print(f"📝 Notion page created: {notion_page['id']}")
                # 成功した場合、既存URLリストに追加（同じセッション内での重複防止）
                paper_url = paper.get('pdf_url') or paper.get('url')
                if paper_url:
                    self.existing_urls.add(paper_url)
            else:
                print(f"❌ Failed to save to Notion")
        
        print(f"✅ Paper {paper_num} processing completed")
        
        # 新規論文数をカウント
        self.processed_new_papers += 1
    
    def search_translate_and_notify(self, query, max_results=2):
        """論文を検索、翻訳してLINE・Notionで通知"""
        print(f"🔍 Starting paper search for: '{query}'")
        
        # arXivで検索（多めに取得してフィルタリング）
        papers = self.arxiv.search_papers(query, max_results * 3)
        
        if not papers:
            print("❌ No papers found")
            self.line.send_message(f"「{query}」に関する論文が見つかりませんでした。")
            return
        
        print(f"✅ Found {len(papers)} papers")
        
        # 関連性フィルタリング
        relevant_papers = self.filter_relevant_papers(papers, query)
        
        if not relevant_papers:
            print("❌ No relevant papers found after filtering")
            self.line.send_message(f"「{query}」に関連する論文が見つかりませんでした。")
            return
        
        # 必要な数まで絞り込み
        papers = relevant_papers[:max_results]
        print(f"📋 Using {len(papers)} relevant papers")
        
        # DeepL使用状況確認
        usage = self.deepl.get_usage()
        print(f"📊 DeepL usage: {usage['used']:,} / {usage['limit']:,} characters")
        print(f"📊 Remaining: {usage['remaining']:,} characters")
        
        # ヘッダーメッセージ送信
        header = f"🔬 本日の論文情報 ({len(papers)}件)\n" + "="*30
        self.line.send_message(header)
        time.sleep(1)  # レート制限対策
        
        # 各論文を処理
        for i, paper in enumerate(papers, 1):
            self.process_single_paper(paper, i, len(papers))
        
        print(f"\n🎉 All {len(papers)} papers processed and sent!")
        
        # 新規論文数の上限チェック
        return self.processed_new_papers >= MAX_NEW_PAPERS_PER_DAY

def main():
    try:
        print("🚀 Starting Paper Notification System...")
        print(f"📋 Search keywords: {', '.join(SEARCH_KEYWORDS)}")
        print(f"📊 Papers per keyword: {PAPERS_PER_KEYWORD}")
        
        # システム初期化
        system = PaperNotificationSystem()
        
        for query in SEARCH_KEYWORDS:
            print(f"\n{'='*60}")
            print(f"Processing query: {query}")
            print(f"新規論文処理数: {system.processed_new_papers}/{MAX_NEW_PAPERS_PER_DAY}")
            print('='*60)
            
            # 上限に達していたら終了
            if system.processed_new_papers >= MAX_NEW_PAPERS_PER_DAY:
                print(f"🎯 Daily limit reached ({MAX_NEW_PAPERS_PER_DAY} new papers processed)")
                break
            
            should_stop = system.search_translate_and_notify(query, max_results=PAPERS_PER_KEYWORD)
            
            print(f"✅ Query '{query}' completed")
            
            # 上限に達したら終了
            if should_stop:
                print(f"🎯 Daily limit reached ({MAX_NEW_PAPERS_PER_DAY} new papers processed)")
                break
                
            time.sleep(QUERY_INTERVAL)
        
        print(f"\n🎉 Paper Notification System completed successfully!")
        
    except Exception as e:
        print(f"❌ System error: {e}")
        if "DEEPL_API_KEY" in str(e):
            print("Please set your DeepL API key in .env file")
        elif "LINE_CHANNEL_ACCESS_TOKEN" in str(e):
            print("Please set your LINE Bot credentials in .env file")

if __name__ == "__main__":
    main()
